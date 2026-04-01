from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List, Dict
import os
import uuid
import asyncio
import logging
import time
from collections import defaultdict
from dotenv import load_dotenv

from src.utils.supabase_client import get_supabase_client
from src.utils.gnews_client import get_gnews_client

load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Rate limiting: Track requests per IP
request_tracker = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # Max requests per window
RATE_LIMIT_WINDOW = 60  # Window in seconds

app = FastAPI(
    title="Fake News Detection API",
    description="Multi-class fake news detection using DistilBERT, RoBERTa, and XLNet",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware to prevent abuse.
    Allows RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW seconds per IP.
    """
    client_ip = request.client.host
    current_time = time.time()

    # Clean old requests outside the window
    request_tracker[client_ip] = [
        req_time for req_time in request_tracker[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check rate limit
    if len(request_tracker[client_ip]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
        )

    # Track this request
    request_tracker[client_ip].append(current_time)

    response = await call_next(request)
    return response


VALID_MODELS = {"distilbert", "roberta", "xlnet"}


class PredictionRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    model: Optional[str] = "distilbert"


class ExplanationData(BaseModel):
    token: str
    score: float


class PredictionResponse(BaseModel):
    article_id: str
    label: str
    confidence: float
    scores: dict
    model_used: str
    explanation: List[ExplanationData]


class FeedbackRequest(BaseModel):
    article_id: str
    predicted_label: str
    actual_label: str
    user_comment: Optional[str] = None


class ExplainRequest(BaseModel):
    text: str
    model: Optional[str] = "distilbert"
    deep: Optional[bool] = False


# Ensemble API Models
class EnsemblePredictionRequest(BaseModel):
    text: str
    session_id: Optional[str] = None

    @validator('text')
    def validate_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Text too short to classify")
        return v


class VotingResult(BaseModel):
    label: str
    confidence: float
    scores: Dict[str, float]


class VotingStrategies(BaseModel):
    hard_voting: VotingResult
    soft_voting: VotingResult
    weighted_voting: VotingResult


class ModelPredictionResponse(BaseModel):
    model_name: str
    label: str
    confidence: float
    scores: Dict[str, float]
    tokens: List[ExplanationData]


class EnsemblePredictionResponse(BaseModel):
    article_id: str
    primary_prediction: VotingResult  # hard voting result
    voting_strategies: VotingStrategies
    individual_models: List[ModelPredictionResponse]
    merged_explanation: List[ExplanationData]
    execution_time_ms: float
    warnings: Optional[List[str]] = None


@app.on_event("startup")
async def startup_event():
    try:
        get_supabase_client()
        print("✅ Supabase connected")
    except Exception as e:
        print(f"⚠️  Supabase: {e}")
    try:
        get_gnews_client()
        print("✅ GNews API connected")
    except Exception as e:
        print(f"⚠️  GNews: {e}")

    # Pre-load all models at startup so first requests don't time out
    for model_key in ["distilbert", "roberta", "xlnet"]:
        try:
            from src.models.inference import get_classifier
            get_classifier(model_key)
            print(f"✅ {model_key} loaded")
        except Exception:
            print(f"ℹ️  {model_key} will load on first request")

    print("🚀 API server started")


@app.get("/")
async def root():
    return {
        "message": "Fake News Detection API",
        "status": "running",
        "version": "1.0.0",
        "models": list(VALID_MODELS),
    }


@app.get("/health")
async def health_check():
    status = {"api": "healthy", "supabase": "unknown", "gnews": "unknown"}
    try:
        get_supabase_client()
        status["supabase"] = "healthy"
    except Exception as e:
        status["supabase"] = f"unhealthy: {e}"
    try:
        get_gnews_client()
        status["gnews"] = "healthy"
    except Exception as e:
        status["gnews"] = f"unhealthy: {e}"
    return status


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Classify news as True / Fake / Satire / Bias.

    Requirements: 4.4, 4.6, 2.7
    """
    if not request.text and not request.url:
        raise HTTPException(status_code=400, detail="Provide text or url")

    model_key = request.model if request.model in VALID_MODELS else "distilbert"
    article_id = str(uuid.uuid4())

    text = request.text or ""
    if not text and request.url:
        try:
            import requests as req
            from bs4 import BeautifulSoup
            r = req.get(request.url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            text = " ".join(p.get_text() for p in soup.find_all("p"))[:4000]
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Could not fetch URL: {e}")

    if len(text.strip()) < 10:
        raise HTTPException(
            status_code=422, detail="Text too short to classify")

    try:
        from src.models.inference import predict as run_inference
        result = run_inference(text, model_key)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    response = PredictionResponse(
        article_id=article_id,
        label=result["label"],
        confidence=result["confidence"],
        scores=result["scores"],
        model_used=model_key,
        explanation=[ExplanationData(**t) for t in result.get("tokens", [])],
    )

    def _store():
        """
        Store prediction in both predictions and user_analysis_history tables.
        Requirements: 4.4, 4.6, 2.7
        """
        try:
            supabase = get_supabase_client()

            # Store in predictions table (Requirement 2.7)
            try:
                supabase.store_prediction(
                    article_id=article_id,
                    text=text,
                    predicted_label=result["label"],
                    confidence=result["confidence"],
                    model_name=model_key,
                    explanation=result.get("tokens", []),
                )
                logger.info(
                    f"Stored prediction {article_id} in predictions table")
            except Exception as e:
                logger.error(
                    f"Failed to store prediction in predictions table: {e}")

            # Store in user_analysis_history if session_id is provided (Requirement 4.4, 4.6)
            if x_session_id:
                try:
                    supabase.store_user_history(
                        session_id=x_session_id,
                        article_id=article_id,
                        text=text,
                        predicted_label=result["label"],
                        confidence=result["confidence"],
                        model_name=model_key
                    )
                    logger.info(
                        f"Stored prediction {article_id} in user_analysis_history for session {x_session_id}")
                except Exception as e:
                    # Handle missing session_id gracefully (Requirement 4.4)
                    logger.error(
                        f"Failed to store prediction in user_analysis_history: {e}")
            else:
                logger.debug(
                    f"No session_id provided for prediction {article_id}, skipping history storage")

        except Exception as e:
            logger.error(
                f"Database storage failed for prediction {article_id}: {e}")

    background_tasks.add_task(_store)
    return response


@app.post("/predict/ensemble", response_model=EnsemblePredictionResponse)
async def predict_ensemble(
    request: EnsemblePredictionRequest,
    background_tasks: BackgroundTasks,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Run ensemble prediction using all three models (DistilBERT, RoBERTa, XLNet).
    Combines predictions using hard voting, soft voting, and weighted voting strategies.

    Requirements: 2.1, 2.2, 2.5, 2.8
    """
    article_id = str(uuid.uuid4())
    session_id = x_session_id or request.session_id

    try:
        from src.models.ensemble import get_ensemble_classifier

        # Get ensemble classifier instance
        ensemble = get_ensemble_classifier()

        # Run ensemble prediction with 15s timeout (Requirement 2.8)
        result = await asyncio.wait_for(
            ensemble.predict_ensemble(request.text),
            timeout=15.0
        )

        # Build response with all voting strategies
        primary_prediction = VotingResult(
            label=result.hard_voting_label,
            confidence=result.hard_voting_confidence,
            scores={result.hard_voting_label: result.hard_voting_confidence}
        )

        voting_strategies = VotingStrategies(
            hard_voting=VotingResult(
                label=result.hard_voting_label,
                confidence=result.hard_voting_confidence,
                scores={result.hard_voting_label: result.hard_voting_confidence}
            ),
            soft_voting=VotingResult(
                label=result.soft_voting_label,
                confidence=result.soft_voting_confidence,
                scores=result.soft_voting_scores
            ),
            weighted_voting=VotingResult(
                label=result.weighted_voting_label,
                confidence=result.weighted_voting_confidence,
                scores=result.weighted_voting_scores
            )
        )

        # Convert individual model predictions
        individual_models = [
            ModelPredictionResponse(
                model_name=pred.model_name,
                label=pred.label,
                confidence=pred.confidence,
                scores=pred.scores,
                tokens=[ExplanationData(**t) for t in pred.tokens]
            )
            for pred in result.individual_predictions
        ]

        # Convert merged explanation
        merged_explanation = [
            ExplanationData(**token) for token in result.merged_explanation
        ]

        response = EnsemblePredictionResponse(
            article_id=article_id,
            primary_prediction=primary_prediction,
            voting_strategies=voting_strategies,
            individual_models=individual_models,
            merged_explanation=merged_explanation,
            execution_time_ms=result.execution_time_ms,
            warnings=result.warnings
        )

        # Background task: store ensemble prediction to database
        def store_ensemble_prediction():
            """
            Store prediction in both predictions and user_analysis_history tables.
            Handles database failures gracefully - logs errors but doesn't crash.
            Requirements: 2.3, 2.4, 2.6, 2.7, 14.3
            """
            try:
                supabase = get_supabase_client()

                # Store in predictions table with model_name="ensemble" (Requirement 2.7)
                try:
                    supabase.store_prediction(
                        article_id=article_id,
                        text=request.text,
                        predicted_label=result.hard_voting_label,
                        confidence=result.hard_voting_confidence,
                        model_name="ensemble",
                        explanation=result.merged_explanation,
                    )
                    logger.info(
                        f"Stored ensemble prediction {article_id} in predictions table")
                except Exception as e:
                    # Log but continue - don't let predictions table failure stop history storage
                    logger.error(
                        f"Failed to store prediction in predictions table: {e}")

                # Store in user_analysis_history if session_id is provided (Requirement 2.4)
                if session_id:
                    try:
                        supabase.store_user_history(
                            session_id=session_id,
                            article_id=article_id,
                            text=request.text,
                            predicted_label=result.hard_voting_label,
                            confidence=result.hard_voting_confidence,
                            model_name="ensemble"
                        )
                        logger.info(
                            f"Stored ensemble prediction {article_id} in user_analysis_history for session {session_id}")
                    except Exception as e:
                        # Log but don't crash - history storage is non-critical (Requirement 14.3)
                        logger.error(
                            f"Failed to store prediction in user_analysis_history: {e}")
                else:
                    logger.debug(
                        f"No session_id provided for prediction {article_id}, skipping history storage")

            except Exception as e:
                # Catch-all for any database connection failures (Requirement 14.3)
                logger.error(
                    f"Database storage failed for prediction {article_id}: {e}")

        background_tasks.add_task(store_ensemble_prediction)
        return response

    except asyncio.TimeoutError:
        # Requirement 2.8: Return HTTP 504 after 15s timeout
        raise HTTPException(
            status_code=504,
            detail="Ensemble prediction timed out after 15 seconds"
        )
    except ValueError as e:
        # Handle validation errors (e.g., text too short)
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        # Handle case where all models fail
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ensemble prediction error: {str(e)}"
        )


@app.get("/history/{session_id}")
async def get_user_history(
    session_id: str,
    limit: int = Query(100, ge=1, le=100)
):
    """
    Retrieve user's analysis history by session ID.

    Args:
        session_id: UUID v4 session identifier
        limit: Maximum records to return (1-100, default 100)

    Returns:
        List of prediction records with metadata

    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    # Validate UUID format (Requirement 6.6)
    try:
        uuid.UUID(session_id, version=4)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID format"
        )

    try:
        # Add 2s timeout (Requirement 6.7)
        supabase = get_supabase_client()
        history = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                supabase.get_user_history,
                session_id,
                limit
            ),
            timeout=2.0
        )

        # Return empty array with HTTP 200 for sessions with no history (Requirement 6.5)
        return {
            "status": "success",
            "session_id": session_id,
            "count": len(history),
            "history": history
        }
    except asyncio.TimeoutError:
        # Requirement 6.7: Return HTTP 504 after 2s timeout
        raise HTTPException(
            status_code=504,
            detail="History retrieval timed out after 2 seconds"
        )
    except Exception as e:
        logger.error(f"Failed to fetch history for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load history"
        )


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user correction for active learning."""
    try:
        supabase = get_supabase_client()
        result = supabase.store_feedback(
            article_id=feedback.article_id,
            predicted_label=feedback.predicted_label,
            actual_label=feedback.actual_label,
            user_comment=feedback.user_comment,
        )
        return {"status": "success", "message": "Feedback recorded", "data": result}
    except Exception as e:
        import traceback
        print(f"[feedback] ERROR: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error storing feedback: {str(e)}")


@app.get("/news")
async def get_recent_news(
    query: str = "breaking news",
    max_results: int = 10,
    category: Optional[str] = None,
):
    """Fetch recent articles from GNews."""
    try:
        gnews = get_gnews_client()
        if category:
            articles = gnews.get_top_headlines(
                category=category, max_results=max_results)
        else:
            articles = gnews.search_news(query=query, max_results=max_results)
        return {"status": "success", "count": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching news: {e}")


@app.get("/news/analyze")
async def analyze_recent_news(topic: str = "politics", max_articles: int = 5):
    """Fetch and classify recent news articles."""
    try:
        gnews = get_gnews_client()
        articles = gnews.search_news(query=topic, max_results=max_articles)

        from src.models.inference import predict as run_inference
        results = []
        for article in articles:
            text = article.get("content") or article.get(
                "description") or article.get("title", "")
            if len(text.strip()) < 10:
                continue
            try:
                pred = run_inference(text, "distilbert")
                results.append({"article": article, "prediction": pred})
            except Exception:
                results.append({"article": article, "prediction": None})

        return {"status": "success", "topic": topic, "analyzed_count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing news: {e}")


@app.get("/news/newspaper")
async def get_newspaper(max_per_topic: int = 6):
    """Fetch and classify news across multiple topics, grouped by predicted label."""
    topics = ["world news", "politics", "technology",
              "science", "health", "business"]
    try:
        gnews = get_gnews_client()
        from src.models.inference import predict as run_inference

        all_results = []
        seen_urls: set = set()

        for topic in topics:
            articles = gnews.search_news(
                query=topic, max_results=max_per_topic)
            for article in articles:
                url = article.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                text = article.get("content") or article.get(
                    "description") or article.get("title", "")
                if len(text.strip()) < 10:
                    continue
                try:
                    pred = run_inference(text, "distilbert")
                    all_results.append(
                        {"article": article, "prediction": pred})
                except Exception:
                    all_results.append({"article": article, "prediction": {
                        "label": "True", "confidence": 0.5, "scores": {}, "tokens": []
                    }})

        grouped: Dict[str, list] = {"True": [],
                                    "Fake": [], "Satire": [], "Bias": []}
        for item in all_results:
            lbl = item["prediction"].get(
                "label", "True") if item["prediction"] else "True"
            if lbl in grouped:
                grouped[lbl].append(item)

        return {"status": "success", "total": len(all_results), "grouped": grouped}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error building newspaper: {e}")


@app.post("/explain")
async def explain_prediction(request: ExplainRequest):
    """
    Return explainability data for a piece of text.
    Always returns gradient saliency highlights. If deep=True, also runs SHAP via RoBERTa.
    """
    if len(request.text.strip()) < 10:
        raise HTTPException(status_code=422, detail="Text too short")

    model_key = request.model if request.model in VALID_MODELS else "distilbert"

    try:
        from src.models.inference import get_classifier
        import asyncio

        clf = get_classifier(model_key)
        loop = asyncio.get_event_loop()

        attention = await loop.run_in_executor(None, clf.attention_weights, request.text)

        shap_tokens = []
        explanation_text = ""
        if request.deep:
            shap_tokens = await loop.run_in_executor(None, clf.shap_explain, request.text)
            if shap_tokens:
                from src.models.inference import generate_explanation_text, predict as run_predict
                pred = run_predict(request.text, model_key)
                explanation_text = generate_explanation_text(
                    shap_tokens, pred["label"], pred["confidence"], model_key
                )

        return {"attention": attention, "shap": shap_tokens, "explanation_text": explanation_text, "model_used": model_key}
    except Exception as e:
        import traceback
        print(f"[explain] ERROR: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Explain error: {e}")


@app.get("/stats")
async def get_statistics():
    """Prediction statistics from Supabase."""
    try:
        supabase = get_supabase_client()
        stats = supabase.get_prediction_stats()
        return {"status": "success", "statistics": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching stats: {e}")


@app.get("/storage")
async def get_storage_usage():
    """
    Get database storage usage metrics and warnings.

    Returns storage usage information and warns when approaching 90% of 500MB limit.
    """
    try:
        supabase = get_supabase_client()
        usage = supabase.check_storage_usage()
        return {"status": "success", "storage": usage}
    except Exception as e:
        logger.error(f"Error fetching storage usage: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching storage usage: {e}")


@app.get("/models")
async def list_models():
    """List available models and their training status."""
    from pathlib import Path
    models_dir = Path(__file__).parents[2] / "models"
    available = []
    for name in ["distilbert", "roberta", "xlnet"]:
        path = models_dir / name
        trained = (path / "config.json").exists()
        available.append({"name": name, "trained": trained,
                         "path": str(path) if trained else None})
    return {"models": available, "default": "distilbert"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
    )

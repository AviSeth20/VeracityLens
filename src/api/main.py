from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import uuid
from dotenv import load_dotenv

from src.utils.supabase_client import get_supabase_client
from src.utils.gnews_client import get_gnews_client

load_dotenv()

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
async def predict(request: PredictionRequest, background_tasks: BackgroundTasks):
    """Classify news as True / Fake / Satire / Bias."""
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
        try:
            supabase = get_supabase_client()
            supabase.store_prediction(
                article_id=article_id,
                text=text,
                predicted_label=result["label"],
                confidence=result["confidence"],
                model_name=model_key,
                explanation=result.get("tokens", []),
            )
        except Exception as e:
            print(f"[bg] store_prediction failed: {e}")

    background_tasks.add_task(_store)
    return response


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

"""
FastAPI backend for fake news detection
Integrates with Supabase and GNews API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import uuid

from src.utils.supabase_client import get_supabase_client
from src.utils.gnews_client import get_gnews_client

load_dotenv()

app = FastAPI(
    title="Fake News Detection API",
    description="Multi-class fake news detection with explainability using DistilBERT, RoBERTa, and XLNet",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models


class PredictionRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    model: Optional[str] = "distilbert"  # distilbert, roberta, xlnet


class ExplanationData(BaseModel):
    token: str
    score: float


class PredictionResponse(BaseModel):
    article_id: str
    label: str
    confidence: float
    model_used: str
    explanation: List[ExplanationData]


class FeedbackRequest(BaseModel):
    article_id: str
    predicted_label: str
    actual_label: str
    user_comment: Optional[str] = None


class NewsArticle(BaseModel):
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: str

# Startup event


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    try:
        # Test Supabase connection
        supabase = get_supabase_client()
        print("✅ Supabase connected")

        # Test GNews connection
        gnews = get_gnews_client()
        print("✅ GNews API connected")

        print("🚀 API server started successfully")
    except Exception as e:
        print(f"⚠️  Warning during startup: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Fake News Detection API",
        "status": "running",
        "version": "1.0.0",
        "models": ["distilbert", "roberta", "xlnet"],
        "endpoints": {
            "predict": "/predict",
            "feedback": "/feedback",
            "news": "/news",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "api": "healthy",
        "supabase": "unknown",
        "gnews": "unknown"
    }

    try:
        supabase = get_supabase_client()
        health_status["supabase"] = "healthy"
    except Exception as e:
        health_status["supabase"] = f"unhealthy: {str(e)}"

    try:
        gnews = get_gnews_client()
        health_status["gnews"] = "healthy"
    except Exception as e:
        health_status["gnews"] = f"unhealthy: {str(e)}"

    return health_status


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, background_tasks: BackgroundTasks):
    """
    Predict if news is True, Fake, Satire, or Biased

    - **text**: Article text to analyze
    - **url**: Article URL (will fetch content)
    - **model**: Model to use (distilbert, roberta, xlnet)
    """
    if not request.text and not request.url:
        raise HTTPException(
            status_code=400, detail="Either text or url must be provided")

    # Generate unique article ID
    article_id = str(uuid.uuid4())

    # TODO: Load model and make actual prediction
    # For now, return mock response
    mock_prediction = {
        "article_id": article_id,
        "label": "True",
        "confidence": 0.85,
        "model_used": request.model or "distilbert",
        "explanation": [
            ExplanationData(token="verified", score=0.8),
            ExplanationData(token="sources", score=0.6),
            ExplanationData(token="credible", score=0.5)
        ]
    }

    # Store prediction in background
    async def store_prediction_task():
        try:
            supabase = get_supabase_client()
            await supabase.store_prediction(
                article_id=article_id,
                text=request.text or "",
                predicted_label=mock_prediction["label"],
                confidence=mock_prediction["confidence"],
                model_name=mock_prediction["model_used"],
                explanation=[e.dict() for e in mock_prediction["explanation"]]
            )
        except Exception as e:
            print(f"Error storing prediction: {str(e)}")

    background_tasks.add_task(store_prediction_task)

    return PredictionResponse(**mock_prediction)


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback for active learning

    - **article_id**: ID from prediction response
    - **predicted_label**: What the model predicted
    - **actual_label**: Correct label according to user
    - **user_comment**: Optional comment
    """
    try:
        supabase = get_supabase_client()
        result = await supabase.store_feedback(
            article_id=feedback.article_id,
            predicted_label=feedback.predicted_label,
            actual_label=feedback.actual_label,
            user_comment=feedback.user_comment
        )

        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error storing feedback: {str(e)}")


@app.get("/news")
async def get_recent_news(
    query: str = "breaking news",
    max_results: int = 10,
    category: Optional[str] = None
):
    """
    Fetch recent news articles from GNews API

    - **query**: Search query
    - **max_results**: Number of articles (max 100)
    - **category**: News category (optional)
    """
    try:
        gnews = get_gnews_client()

        if category:
            articles = gnews.get_top_headlines(
                category=category,
                max_results=max_results
            )
        else:
            articles = gnews.search_news(
                query=query,
                max_results=max_results
            )

        return {
            "status": "success",
            "count": len(articles),
            "articles": articles
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching news: {str(e)}")


@app.get("/news/analyze")
async def analyze_recent_news(
    topic: str = "politics",
    max_articles: int = 5
):
    """
    Fetch and analyze recent news articles

    - **topic**: News topic to search
    - **max_articles**: Number of articles to analyze
    """
    try:
        gnews = get_gnews_client()
        articles = gnews.search_news(query=topic, max_results=max_articles)

        # TODO: Analyze each article with model
        analyzed_articles = []
        for article in articles:
            # Mock analysis
            analyzed_articles.append({
                "article": article,
                "prediction": {
                    "label": "True",
                    "confidence": 0.75
                }
            })

        return {
            "status": "success",
            "topic": topic,
            "analyzed_count": len(analyzed_articles),
            "results": analyzed_articles
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing news: {str(e)}")


@app.get("/stats")
async def get_statistics():
    """
    Get prediction statistics from database
    """
    try:
        supabase = get_supabase_client()
        stats = await supabase.get_prediction_stats()

        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/models")
async def list_models():
    """List available models"""
    models_dir = os.path.join(os.path.dirname(__file__), "../../models")

    available_models = []
    for model_name in ["distilbert", "roberta", "xlnet"]:
        model_path = os.path.join(models_dir, model_name)
        exists = os.path.exists(model_path)

        available_models.append({
            "name": model_name,
            "available": exists,
            "path": model_path if exists else None
        })

    return {
        "models": available_models,
        "default": "distilbert"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "True").lower() == "true"
    )

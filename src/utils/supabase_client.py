import os
import uuid
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv(
            "SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        self.client: Client = create_client(self.url, self.key)

    @retry_with_exponential_backoff(max_retries=3)
    def store_prediction(self, article_id: str, text: str, predicted_label: str,
                         confidence: float, model_name: str, explanation=None) -> Dict[str, Any]:
        data = {
            "article_id": article_id,
            "text": text[:1000],
            "predicted_label": predicted_label,
            "confidence": confidence,
            "model_name": model_name,
            "explanation": explanation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            response = self.client.table("predictions").insert(data).execute()
            logger.info(f"Stored prediction for article {article_id}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            raise

    def store_feedback(self, article_id: str, predicted_label: str,
                       actual_label: str, user_comment: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "article_id": article_id,
            "predicted_label": predicted_label,
            "actual_label": actual_label,
            "user_comment": user_comment,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        response = self.client.table("feedback").insert(data).execute()
        return response.data

    def get_prediction_stats(self) -> Dict[str, Any]:
        total = self.client.table("predictions").select(
            "*", count="exact").execute()
        by_label_rows = self.client.table(
            "predictions").select("predicted_label").execute()
        label_counts: Dict[str, int] = {}
        for row in by_label_rows.data:
            lbl = row["predicted_label"]
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
        logger.info(f"Total predictions: {total.count}")
        return {"total_predictions": total.count, "by_label": label_counts}

    def check_storage_usage(self) -> Dict[str, Any]:
        """Check database storage usage and warn if approaching the 500MB free-tier limit."""
        try:
            predictions_count = self.client.table("predictions").select(
                "*", count="exact").execute().count
            history_count = self.client.table("user_analysis_history").select(
                "*", count="exact").execute().count
            estimated_mb = (predictions_count * 1.0 +
                            history_count * 0.5) / 1024
            limit_mb = 500
            usage_percent = (estimated_mb / limit_mb) * 100
            result = {
                "predictions_count": predictions_count,
                "history_count": history_count,
                "estimated_storage_mb": round(estimated_mb, 2),
                "limit_mb": limit_mb,
                "usage_percent": round(usage_percent, 2),
                "warning": None
            }
            if usage_percent >= 90:
                warning = f"Storage usage at {usage_percent:.1f}% ({estimated_mb:.1f}MB / {limit_mb}MB). Consider archiving old data."
                result["warning"] = warning
                logger.warning(warning)
            elif usage_percent >= 75:
                logger.info(
                    f"Storage usage at {usage_percent:.1f}% ({estimated_mb:.1f}MB / {limit_mb}MB)")
            return result
        except Exception as e:
            logger.error(f"Failed to check storage usage: {e}")
            return {"error": str(e), "warning": "Unable to check storage usage"}

    def get_feedback_for_training(self, limit: int = 1000) -> List[Dict[str, Any]]:
        response = self.client.table("feedback").select(
            "*").limit(limit).execute()
        return response.data

    @retry_with_exponential_backoff(max_retries=3)
    def store_user_history(self, session_id: str, article_id: str, text: str,
                           predicted_label: str, confidence: float, model_name: str) -> Dict[str, Any]:
        try:
            uuid.UUID(session_id)
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid session_id format: {e}")
            raise ValueError(f"session_id must be a valid UUID: {e}")

        data = {
            "session_id": session_id,
            "article_id": article_id,
            "text_preview": text[:200],
            "predicted_label": predicted_label,
            "confidence": confidence,
            "model_name": model_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        try:
            response = self.client.table(
                "user_analysis_history").insert(data).execute()
            logger.info(f"Stored user history for session {session_id}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to store user history: {e}")
            raise

    @retry_with_exponential_backoff(max_retries=3)
    def get_user_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            uuid.UUID(session_id)
        except (ValueError, AttributeError) as e:
            logger.error(f"Invalid session_id format: {e}")
            raise ValueError(f"session_id must be a valid UUID: {e}")

        try:
            response = (
                self.client.table("user_analysis_history")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            logger.info(
                f"Retrieved {len(response.data)} history records for session {session_id}")
            return response.data
        except Exception as e:
            logger.error(f"Failed to retrieve user history: {e}")
            raise


_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def reset_client():
    global _supabase_client
    _supabase_client = None

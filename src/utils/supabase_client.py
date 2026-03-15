import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv(
            "SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        self.client: Client = create_client(self.url, self.key)

    def store_prediction(
        self,
        article_id: str,
        text: str,
        predicted_label: str,
        confidence: float,
        model_name: str,
        explanation=None,
    ) -> Dict[str, Any]:
        data = {
            "article_id": article_id,
            "text": text[:1000],
            "predicted_label": predicted_label,
            "confidence": confidence,
            "model_name": model_name,
            "explanation": explanation,
            "created_at": datetime.utcnow().isoformat(),
        }
        response = self.client.table("predictions").insert(data).execute()
        return response.data

    def store_feedback(
        self,
        article_id: str,
        predicted_label: str,
        actual_label: str,
        user_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {
            "article_id": article_id,
            "predicted_label": predicted_label,
            "actual_label": actual_label,
            "user_comment": user_comment,
            "created_at": datetime.utcnow().isoformat(),
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
        return {
            "total_predictions": total.count,
            "by_label": label_counts,
        }

    def get_feedback_for_training(self, limit: int = 1000) -> List[Dict[str, Any]]:
        response = self.client.table("feedback").select(
            "*").limit(limit).execute()
        return response.data


_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def reset_client():
    """Force re-initialisation."""
    global _supabase_client
    _supabase_client = None

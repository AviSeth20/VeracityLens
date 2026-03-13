"""
Supabase client configuration and utilities
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Wrapper for Supabase client with helper methods"""

    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
            )

        self.client: Client = create_client(self.url, self.key)

    async def store_prediction(
        self,
        article_id: str,
        text: str,
        predicted_label: str,
        confidence: float,
        model_name: str,
        explanation: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Store a prediction in the database

        Args:
            article_id: Unique identifier for the article
            text: Article text (truncated if too long)
            predicted_label: Predicted class (True/Fake/Satire/Bias)
            confidence: Model confidence score
            model_name: Name of the model used
            explanation: Optional explainability data

        Returns:
            Response from Supabase
        """
        data = {
            "article_id": article_id,
            "text": text[:1000],  # Store first 1000 chars
            "predicted_label": predicted_label,
            "confidence": confidence,
            "model_name": model_name,
            "explanation": explanation,
            "created_at": datetime.utcnow().isoformat()
        }

        response = self.client.table("predictions").insert(data).execute()
        return response.data

    async def store_feedback(
        self,
        article_id: str,
        predicted_label: str,
        actual_label: str,
        user_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store user feedback for active learning

        Args:
            article_id: Article identifier
            predicted_label: What the model predicted
            actual_label: What the user says is correct
            user_comment: Optional user comment

        Returns:
            Response from Supabase
        """
        data = {
            "article_id": article_id,
            "predicted_label": predicted_label,
            "actual_label": actual_label,
            "user_comment": user_comment,
            "created_at": datetime.utcnow().isoformat()
        }

        response = self.client.table("feedback").insert(data).execute()
        return response.data

    async def get_feedback_for_training(
        self,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve feedback data for model retraining

        Args:
            limit: Maximum number of records to retrieve

        Returns:
            List of feedback records
        """
        response = self.client.table("feedback")\
            .select("*")\
            .limit(limit)\
            .execute()

        return response.data

    async def get_prediction_stats(self) -> Dict[str, Any]:
        """
        Get statistics about predictions

        Returns:
            Dictionary with prediction statistics
        """
        # Total predictions
        total = self.client.table("predictions")\
            .select("*", count="exact")\
            .execute()

        # Predictions by label
        by_label = self.client.table("predictions")\
            .select("predicted_label")\
            .execute()

        label_counts = {}
        for record in by_label.data:
            label = record["predicted_label"]
            label_counts[label] = label_counts.get(label, 0) + 1

        return {
            "total_predictions": total.count,
            "by_label": label_counts
        }


# Global instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

"""
Unit tests for the ensemble API endpoint.
Tests Requirements 2.1, 2.2, 2.5, 2.8
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import asyncio
import time

from src.api.main import app


client = TestClient(app)


class TestEnsembleEndpoint:
    """Test suite for POST /predict/ensemble endpoint."""

    def test_ensemble_endpoint_exists(self):
        """Test that the ensemble endpoint is registered."""
        # Test with invalid data to check endpoint exists
        response = client.post("/predict/ensemble", json={})
        # Should return 422 (validation error) not 404 (not found)
        assert response.status_code == 422

    def test_text_too_short_validation(self):
        """Test that text shorter than 10 characters is rejected (Requirement 2.5)."""
        response = client.post(
            "/predict/ensemble",
            json={"text": "short"}
        )
        assert response.status_code == 422
        assert "too short" in response.json()["detail"][0]["msg"].lower()

    def test_valid_request_structure(self):
        """Test that valid request structure is accepted."""
        # Mock the ensemble classifier to avoid actual model loading
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = []
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = None

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "article_id" in data
            assert "primary_prediction" in data
            assert "voting_strategies" in data
            assert "individual_models" in data
            assert "merged_explanation" in data
            assert "execution_time_ms" in data

    def test_session_id_header_extraction(self):
        """Test that X-Session-ID header is extracted (Requirement 2.1)."""
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = []
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = None

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            # Test with X-Session-ID header
            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."},
                headers={"X-Session-ID": "test-session-123"}
            )

            assert response.status_code == 200

    def test_timeout_handling(self):
        """Test that timeout returns HTTP 504 (Requirement 2.8)."""
        async def mock_timeout(text):
            await asyncio.sleep(20)  # Simulate timeout
            return None

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_timeout
            mock_get_ensemble.return_value = mock_ensemble

            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."}
            )

            assert response.status_code == 504
            assert "timed out" in response.json()["detail"].lower()

    def test_storage_integration_both_tables(self):
        """Test that predictions are stored in both predictions and user_analysis_history tables (Requirements 2.3, 2.4, 2.7)."""
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = []
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = None

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble, \
                patch('src.api.main.get_supabase_client') as mock_get_supabase:

            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            mock_supabase = Mock()
            mock_supabase.store_prediction = Mock(
                return_value={"id": "test-id"})
            mock_supabase.store_user_history = Mock(
                return_value={"id": "test-history-id"})
            mock_get_supabase.return_value = mock_supabase

            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."},
                headers={"X-Session-ID": "test-session-123"}
            )

            assert response.status_code == 200

            # Give background task time to execute
            time.sleep(0.5)

            # Verify store_prediction was called with model_name="ensemble"
            assert mock_supabase.store_prediction.called
            call_kwargs = mock_supabase.store_prediction.call_args[1]
            assert call_kwargs["model_name"] == "ensemble"
            assert call_kwargs["predicted_label"] == "True"
            assert call_kwargs["confidence"] == 0.95

            # Verify store_user_history was called
            assert mock_supabase.store_user_history.called
            history_kwargs = mock_supabase.store_user_history.call_args[1]
            assert history_kwargs["session_id"] == "test-session-123"
            assert history_kwargs["model_name"] == "ensemble"
            assert history_kwargs["predicted_label"] == "True"
            assert history_kwargs["confidence"] == 0.95

    def test_storage_graceful_failure_handling(self):
        """Test that database failures are logged but don't crash the endpoint (Requirement 14.3)."""
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = []
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = None

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble, \
                patch('src.api.main.get_supabase_client') as mock_get_supabase:

            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            # Simulate database failure
            mock_supabase = Mock()
            mock_supabase.store_prediction = Mock(
                side_effect=Exception("Database connection failed"))
            mock_supabase.store_user_history = Mock(
                side_effect=Exception("Database connection failed"))
            mock_get_supabase.return_value = mock_supabase

            # Request should still succeed even if storage fails
            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."},
                headers={"X-Session-ID": "test-session-123"}
            )

            # Endpoint should return 200 despite storage failure
            assert response.status_code == 200
            data = response.json()
            assert "article_id" in data
            assert data["primary_prediction"]["label"] == "True"

    def test_storage_without_session_id(self):
        """Test that storage works without session_id (only predictions table) (Requirement 2.6)."""
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = []
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = None

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble, \
                patch('src.api.main.get_supabase_client') as mock_get_supabase:

            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            mock_supabase = Mock()
            mock_supabase.store_prediction = Mock(
                return_value={"id": "test-id"})
            mock_supabase.store_user_history = Mock(
                return_value={"id": "test-history-id"})
            mock_get_supabase.return_value = mock_supabase

            # Request without session_id
            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."}
            )

            assert response.status_code == 200

            # Give background task time to execute
            time.sleep(0.5)

            # Verify store_prediction was called
            assert mock_supabase.store_prediction.called

            # Verify store_user_history was NOT called (no session_id)
            assert not mock_supabase.store_user_history.called

    def test_all_models_fail_returns_500(self):
        """Test that when all three models fail, endpoint returns HTTP 500 (Requirement 14.2)."""
        async def mock_fail(text):
            raise RuntimeError("All models failed to process the request")

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_fail
            mock_get_ensemble.return_value = mock_ensemble

            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."}
            )

            assert response.status_code == 500
            assert "all models failed" in response.json()["detail"].lower()

    def test_partial_model_failures_return_warnings(self):
        """Test that partial model failures return HTTP 200 with warnings (Requirement 14.2)."""
        mock_result = Mock()
        mock_result.hard_voting_label = "True"
        mock_result.hard_voting_confidence = 0.95
        mock_result.soft_voting_label = "True"
        mock_result.soft_voting_confidence = 0.93
        mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
        mock_result.weighted_voting_label = "True"
        mock_result.weighted_voting_confidence = 0.94
        mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}
        mock_result.individual_predictions = [
            Mock(
                model_name="distilbert",
                label="True",
                confidence=0.95,
                scores={"True": 0.95, "Fake": 0.05},
                tokens=[]
            ),
            Mock(
                model_name="roberta",
                label="True",
                confidence=0.91,
                scores={"True": 0.91, "Fake": 0.09},
                tokens=[]
            )
        ]
        mock_result.merged_explanation = []
        mock_result.execution_time_ms = 1500.0
        mock_result.warnings = ["xlnet model failed to process the request"]

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            response = client.post(
                "/predict/ensemble",
                json={"text": "This is a valid news article text for testing."}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify warnings are present
            assert "warnings" in data
            assert data["warnings"] is not None
            assert len(data["warnings"]) > 0
            assert "xlnet" in data["warnings"][0].lower()

            # Verify response still contains valid predictions
            assert "primary_prediction" in data
            assert data["primary_prediction"]["label"] == "True"

            # Verify only 2 models returned predictions (xlnet failed)
            assert len(data["individual_models"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

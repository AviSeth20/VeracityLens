"""
Unit tests for history retrieval endpoint.
Feature: phase-1-enhancements

Tests the GET /history/{session_id} endpoint for various scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timezone

from src.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    with patch('src.api.main.get_supabase_client') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


def test_valid_session_id_returns_200(mock_supabase_client):
    """
    Test that a valid session_id returns HTTP 200 with history data.
    Requirements: 6.1, 6.4
    """
    session_id = str(uuid.uuid4())

    # Mock history data
    mock_history = [
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "article_id": str(uuid.uuid4()),
            "text_preview": "Test article 1",
            "predicted_label": "True",
            "confidence": 0.95,
            "model_name": "ensemble",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "article_id": str(uuid.uuid4()),
            "text_preview": "Test article 2",
            "predicted_label": "Fake",
            "confidence": 0.88,
            "model_name": "distilbert",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    mock_supabase_client.get_user_history.return_value = mock_history

    # Make request
    response = client.get(f"/history/{session_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["session_id"] == session_id
    assert data["count"] == 2
    assert len(data["history"]) == 2
    assert data["history"][0]["predicted_label"] == "True"
    assert data["history"][1]["predicted_label"] == "Fake"


def test_invalid_session_id_format_returns_400(mock_supabase_client):
    """
    Test that an invalid session_id format returns HTTP 400.
    Requirements: 6.6
    """
    invalid_session_ids = [
        "not-a-uuid",
        "12345",
        "invalid-format-here",
        "abc-def-ghi-jkl-mno"
    ]

    for invalid_id in invalid_session_ids:
        response = client.get(f"/history/{invalid_id}")

        assert response.status_code == 400, f"Expected 400 for invalid session_id: {invalid_id}"
        data = response.json()
        assert "Invalid session ID format" in data["detail"]

    # Empty string is a special case - FastAPI returns 404 for missing path parameter
    response = client.get("/history/")
    assert response.status_code == 404  # FastAPI behavior for missing path parameter


def test_empty_history_returns_empty_array(mock_supabase_client):
    """
    Test that a session with no history returns an empty array with HTTP 200.
    Requirements: 6.5
    """
    session_id = str(uuid.uuid4())

    # Mock empty history
    mock_supabase_client.get_user_history.return_value = []

    # Make request
    response = client.get(f"/history/{session_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["session_id"] == session_id
    assert data["count"] == 0
    assert data["history"] == []


def test_limit_parameter_works_correctly(mock_supabase_client):
    """
    Test that the limit parameter correctly limits the number of results.
    Requirements: 6.3
    """
    session_id = str(uuid.uuid4())

    # Mock history data with 50 items
    mock_history = [
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "article_id": str(uuid.uuid4()),
            "text_preview": f"Test article {i}",
            "predicted_label": "True",
            "confidence": 0.9,
            "model_name": "ensemble",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        for i in range(50)
    ]

    mock_supabase_client.get_user_history.return_value = mock_history

    # Test with limit=50
    response = client.get(f"/history/{session_id}?limit=50")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 50
    assert len(data["history"]) == 50

    # Verify the limit was passed to the client
    mock_supabase_client.get_user_history.assert_called_with(session_id, 50)


def test_limit_parameter_default_100(mock_supabase_client):
    """
    Test that the default limit is 100 when not specified.
    Requirements: 6.3
    """
    session_id = str(uuid.uuid4())

    mock_supabase_client.get_user_history.return_value = []

    # Make request without limit parameter
    response = client.get(f"/history/{session_id}")

    assert response.status_code == 200

    # Verify default limit of 100 was used
    mock_supabase_client.get_user_history.assert_called_with(session_id, 100)


def test_limit_parameter_validation(mock_supabase_client):
    """
    Test that limit parameter is validated (1-100 range).
    Requirements: 6.3
    """
    session_id = str(uuid.uuid4())

    # Test limit < 1
    response = client.get(f"/history/{session_id}?limit=0")
    assert response.status_code == 422  # Validation error

    # Test limit > 100
    response = client.get(f"/history/{session_id}?limit=101")
    assert response.status_code == 422  # Validation error

    # Test valid limits
    for valid_limit in [1, 50, 100]:
        mock_supabase_client.get_user_history.return_value = []
        response = client.get(f"/history/{session_id}?limit={valid_limit}")
        assert response.status_code == 200


def test_database_error_returns_500(mock_supabase_client):
    """
    Test that database errors are handled gracefully with HTTP 500.
    Requirements: 6.1
    """
    session_id = str(uuid.uuid4())

    # Mock database error
    mock_supabase_client.get_user_history.side_effect = Exception(
        "Database connection failed")

    # Make request
    response = client.get(f"/history/{session_id}")

    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert "Failed to load history" in data["detail"]


def test_timeout_returns_504(mock_supabase_client):
    """
    Test that timeout after 2 seconds returns HTTP 504.
    Requirements: 6.7
    """
    import asyncio

    session_id = str(uuid.uuid4())

    # Mock timeout by making the function sleep longer than 2 seconds
    def slow_get_history(*args, **kwargs):
        import time
        time.sleep(3)  # Sleep for 3 seconds (longer than 2s timeout)
        return []

    mock_supabase_client.get_user_history.side_effect = slow_get_history

    # Make request
    response = client.get(f"/history/{session_id}")

    # Assertions
    assert response.status_code == 504
    data = response.json()
    assert "timed out" in data["detail"].lower()


def test_history_returns_correct_fields(mock_supabase_client):
    """
    Test that history returns all required fields.
    Requirements: 6.4
    """
    session_id = str(uuid.uuid4())

    # Mock history data with all fields
    mock_history = [
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "article_id": str(uuid.uuid4()),
            "text_preview": "Test article",
            "predicted_label": "True",
            "confidence": 0.95,
            "model_name": "ensemble",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    mock_supabase_client.get_user_history.return_value = mock_history

    # Make request
    response = client.get(f"/history/{session_id}")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Verify all required fields are present
    history_item = data["history"][0]
    required_fields = ["article_id", "text_preview", "predicted_label",
                       "confidence", "model_name", "created_at"]

    for field in required_fields:
        assert field in history_item, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for user history storage methods in Supabase client.
Feature: phase-1-enhancements
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime, timezone

from src.utils.supabase_client import SupabaseClient


class TestUserHistoryStorage:
    """Test suite for user history storage functionality."""

    def test_store_user_history_validates_session_id(self):
        """Test that store_user_history validates UUID format for session_id."""
        mock_client = MagicMock()

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            # Test with invalid session_id
            with pytest.raises(ValueError, match="session_id must be a valid UUID"):
                supabase_client.store_user_history(
                    session_id="invalid-uuid",
                    article_id=str(uuid.uuid4()),
                    text="Test article text",
                    predicted_label="True",
                    confidence=0.95,
                    model_name="ensemble"
                )

    def test_store_user_history_truncates_text_preview(self):
        """Test that store_user_history truncates text to 200 characters."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = mock_execute
        mock_execute.data = [{"id": "test"}]

        captured_data = None

        def capture_insert(data):
            nonlocal captured_data
            captured_data = data
            return mock_insert

        mock_table.insert = capture_insert

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            long_text = "a" * 500
            session_id = str(uuid.uuid4())

            supabase_client.store_user_history(
                session_id=session_id,
                article_id=str(uuid.uuid4()),
                text=long_text,
                predicted_label="Fake",
                confidence=0.85,
                model_name="distilbert"
            )

            assert captured_data is not None
            assert len(captured_data["text_preview"]) == 200
            assert captured_data["text_preview"] == long_text[:200]

    def test_get_user_history_validates_session_id(self):
        """Test that get_user_history validates UUID format for session_id."""
        mock_client = MagicMock()

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            # Test with invalid session_id
            with pytest.raises(ValueError, match="session_id must be a valid UUID"):
                supabase_client.get_user_history(session_id="invalid-uuid")

    def test_get_user_history_orders_by_created_at_desc(self):
        """Test that get_user_history orders results by created_at DESC."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()

        # Setup mock chain
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute
        mock_execute.data = []

        # Track order call
        order_called_with = None

        def capture_order(field, desc=False):
            nonlocal order_called_with
            order_called_with = (field, desc)
            return mock_order

        mock_eq.order = capture_order

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            session_id = str(uuid.uuid4())
            supabase_client.get_user_history(session_id=session_id)

            assert order_called_with is not None
            assert order_called_with[0] == "created_at"
            assert order_called_with[1] is True  # desc=True

    def test_get_user_history_respects_limit(self):
        """Test that get_user_history respects the limit parameter."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()

        # Setup mock chain
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute
        mock_execute.data = []

        # Track limit call
        limit_called_with = None

        def capture_limit(value):
            nonlocal limit_called_with
            limit_called_with = value
            return mock_limit

        mock_order.limit = capture_limit

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            session_id = str(uuid.uuid4())
            supabase_client.get_user_history(session_id=session_id, limit=50)

            assert limit_called_with == 50

    def test_get_user_history_default_limit_100(self):
        """Test that get_user_history uses default limit of 100."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()
        mock_execute = MagicMock()

        # Setup mock chain
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = mock_execute
        mock_execute.data = []

        # Track limit call
        limit_called_with = None

        def capture_limit(value):
            nonlocal limit_called_with
            limit_called_with = value
            return mock_limit

        mock_order.limit = capture_limit

        with patch('src.utils.supabase_client.create_client', return_value=mock_client):
            supabase_client = SupabaseClient()
            supabase_client.client = mock_client

            session_id = str(uuid.uuid4())
            supabase_client.get_user_history(session_id=session_id)

            assert limit_called_with == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

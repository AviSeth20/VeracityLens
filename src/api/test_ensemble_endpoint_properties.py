"""
Property-based tests for the ensemble API endpoint.
Feature: phase-1-enhancements

Uses hypothesis for property-based testing with 100 iterations per property.
Tests Properties 2, 3, and 21 from the design document.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid

from src.api.main import app


client = TestClient(app)


# Strategy for generating valid text inputs
# Text must be at least 10 characters (per Requirement 2.5)
# Use simple sentences with common words to avoid generation issues
@st.composite
def valid_text_strategy(draw):
    """Generate valid text inputs for testing."""
    # Generate a sentence with 3-10 words
    num_words = draw(st.integers(min_value=3, max_value=10))
    words = []
    for _ in range(num_words):
        word = draw(st.text(
            alphabet=st.characters(
                min_codepoint=97, max_codepoint=122),  # lowercase a-z
            min_size=3,
            max_size=10
        ))
        words.append(word)

    text = " ".join(words)
    # Ensure it's at least 10 characters
    if len(text.strip()) < 10:
        text = text + " additional text to meet minimum"
    return text


# Strategy for generating valid session IDs (UUID v4 format)
valid_session_id_strategy = st.uuids().map(str)


def create_mock_ensemble_result(hard_label="True", soft_label="True", weighted_label="True"):
    """Helper function to create a mock ensemble result with all required fields."""
    mock_result = Mock()
    mock_result.hard_voting_label = hard_label
    mock_result.hard_voting_confidence = 0.95
    mock_result.soft_voting_label = soft_label
    mock_result.soft_voting_confidence = 0.93
    mock_result.soft_voting_scores = {"True": 0.93, "Fake": 0.07}
    mock_result.weighted_voting_label = weighted_label
    mock_result.weighted_voting_confidence = 0.94
    mock_result.weighted_voting_scores = {"True": 0.94, "Fake": 0.06}

    # Individual model predictions
    mock_result.individual_predictions = [
        Mock(
            model_name="distilbert",
            label="True",
            confidence=0.92,
            scores={"True": 0.92, "Fake": 0.08},
            tokens=[{"token": "test", "score": 0.5}]
        ),
        Mock(
            model_name="roberta",
            label="True",
            confidence=0.94,
            scores={"True": 0.94, "Fake": 0.06},
            tokens=[{"token": "test", "score": 0.6}]
        ),
        Mock(
            model_name="xlnet",
            label="True",
            confidence=0.96,
            scores={"True": 0.96, "Fake": 0.04},
            tokens=[{"token": "test", "score": 0.7}]
        )
    ]

    # Merged explanation
    mock_result.merged_explanation = [
        {"token": "test", "score": 0.6}
    ]

    mock_result.execution_time_ms = 1500.0
    mock_result.warnings = None

    return mock_result


# Property 2: Ensemble Response Completeness
# **Validates: Requirements 1.5, 1.6, 2.3, 2.4, 3.5, 3.6**
@given(text=valid_text_strategy(), session_id=valid_session_id_strategy)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_ensemble_response_completeness(text, session_id):
    """
    Property 2: Ensemble Response Completeness

    For any valid ensemble prediction, the response shall contain hard voting result,
    soft voting result, weighted voting result, all three individual model predictions
    with confidence scores, and merged token explanations.

    **Validates: Requirements 1.5, 1.6, 2.3, 2.4, 3.5, 3.6**
    """
    mock_result = create_mock_ensemble_result()

    async def mock_predict_ensemble(text):
        return mock_result

    with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
        mock_ensemble = Mock()
        mock_ensemble.predict_ensemble = mock_predict_ensemble
        mock_get_ensemble.return_value = mock_ensemble

        response = client.post(
            "/predict/ensemble",
            json={"text": text},
            headers={"X-Session-ID": session_id}
        )

        # Requirement 2.2: Endpoint returns HTTP 200 for valid input
        assert response.status_code == 200, \
            f"Expected HTTP 200, got {response.status_code}: {response.json() if response.status_code != 200 else ''}"

        data = response.json()

        # Requirement 1.5: Response contains all voting strategy results
        assert "voting_strategies" in data, \
            "Response must contain voting_strategies field"

        voting_strategies = data["voting_strategies"]

        # Hard voting result present
        assert "hard_voting" in voting_strategies, \
            "Voting strategies must contain hard_voting"
        assert "label" in voting_strategies["hard_voting"], \
            "Hard voting must have label"
        assert "confidence" in voting_strategies["hard_voting"], \
            "Hard voting must have confidence"

        # Soft voting result present
        assert "soft_voting" in voting_strategies, \
            "Voting strategies must contain soft_voting"
        assert "label" in voting_strategies["soft_voting"], \
            "Soft voting must have label"
        assert "confidence" in voting_strategies["soft_voting"], \
            "Soft voting must have confidence"
        assert "scores" in voting_strategies["soft_voting"], \
            "Soft voting must have scores dictionary"

        # Weighted voting result present
        assert "weighted_voting" in voting_strategies, \
            "Voting strategies must contain weighted_voting"
        assert "label" in voting_strategies["weighted_voting"], \
            "Weighted voting must have label"
        assert "confidence" in voting_strategies["weighted_voting"], \
            "Weighted voting must have confidence"
        assert "scores" in voting_strategies["weighted_voting"], \
            "Weighted voting must have scores dictionary"

        # Requirement 1.6: Response contains all three individual model predictions
        assert "individual_models" in data, \
            "Response must contain individual_models field"

        individual_models = data["individual_models"]
        assert len(individual_models) == 3, \
            f"Expected 3 individual model predictions, got {len(individual_models)}"

        expected_models = {"distilbert", "roberta", "xlnet"}
        actual_models = {model["model_name"] for model in individual_models}
        assert actual_models == expected_models, \
            f"Expected models {expected_models}, got {actual_models}"

        # Each individual prediction has required fields (Requirements 3.5, 3.6)
        for model in individual_models:
            assert "model_name" in model, \
                "Individual model must have model_name"
            assert "label" in model, \
                f"Model {model['model_name']} must have label"
            assert "confidence" in model, \
                f"Model {model['model_name']} must have confidence"
            assert "scores" in model, \
                f"Model {model['model_name']} must have scores dictionary"
            assert "tokens" in model, \
                f"Model {model['model_name']} must have tokens (explanations)"

            # Confidence must be in valid range
            assert 0.0 <= model["confidence"] <= 1.0, \
                f"Model {model['model_name']} confidence must be in [0, 1]"

            # Scores must be a dictionary
            assert isinstance(model["scores"], dict), \
                f"Model {model['model_name']} scores must be a dictionary"

            # Tokens must be a list
            assert isinstance(model["tokens"], list), \
                f"Model {model['model_name']} tokens must be a list"

        # Requirement 2.3, 2.4: Response contains merged token explanations
        assert "merged_explanation" in data, \
            "Response must contain merged_explanation field"

        merged_explanation = data["merged_explanation"]
        assert isinstance(merged_explanation, list), \
            "Merged explanation must be a list"

        # Additional completeness checks
        assert "article_id" in data, \
            "Response must contain article_id"
        assert "primary_prediction" in data, \
            "Response must contain primary_prediction"
        assert "execution_time_ms" in data, \
            "Response must contain execution_time_ms"


# Property 3: Hard Voting as Primary Prediction
# **Validates: Requirements 1.4, 12.6, 3.4**
@given(text=valid_text_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_hard_voting_as_primary_prediction(text):
    """
    Property 3: Hard Voting as Primary Prediction

    For any ensemble result, the primary prediction label shall match
    the hard voting result.

    **Validates: Requirements 1.4, 12.6, 3.4**
    """
    # Test with different voting outcomes to ensure hard voting is always primary
    test_cases = [
        ("True", "True", "True"),    # All agree
        ("True", "Fake", "Fake"),    # Hard differs from soft/weighted
        ("Fake", "True", "True"),    # Hard differs from soft/weighted
        ("Satire", "Fake", "True"),  # All different
    ]

    for hard_label, soft_label, weighted_label in test_cases:
        mock_result = create_mock_ensemble_result(
            hard_label=hard_label,
            soft_label=soft_label,
            weighted_label=weighted_label
        )

        async def mock_predict_ensemble(text):
            return mock_result

        with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
            mock_ensemble = Mock()
            mock_ensemble.predict_ensemble = mock_predict_ensemble
            mock_get_ensemble.return_value = mock_ensemble

            response = client.post(
                "/predict/ensemble",
                json={"text": text}
            )

            assert response.status_code == 200, \
                f"Expected HTTP 200, got {response.status_code}"

            data = response.json()

            # Requirement 1.4, 12.6, 3.4: Primary prediction matches hard voting
            assert "primary_prediction" in data, \
                "Response must contain primary_prediction"

            primary_label = data["primary_prediction"]["label"]
            hard_voting_label = data["voting_strategies"]["hard_voting"]["label"]

            assert primary_label == hard_voting_label, \
                f"Primary prediction label ({primary_label}) must match hard voting label ({hard_voting_label})"

            # Also verify that primary prediction matches hard voting result exactly
            assert primary_label == hard_label, \
                f"Primary prediction ({primary_label}) must be hard voting result ({hard_label})"


# Property 21: Ensemble Endpoint Behavior
# **Validates: Requirements 2.2, 3.3**
@given(text=valid_text_strategy())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_ensemble_endpoint_behavior(text):
    """
    Property 21: Ensemble Endpoint Behavior

    For any valid text input to /predict/ensemble, the endpoint shall return
    HTTP 200 with a complete ensemble result containing all voting strategies
    and individual predictions.

    **Validates: Requirements 2.2, 3.3**
    """
    mock_result = create_mock_ensemble_result()

    async def mock_predict_ensemble(text):
        return mock_result

    with patch('src.models.ensemble.get_ensemble_classifier') as mock_get_ensemble:
        mock_ensemble = Mock()
        mock_ensemble.predict_ensemble = mock_predict_ensemble
        mock_get_ensemble.return_value = mock_ensemble

        response = client.post(
            "/predict/ensemble",
            json={"text": text}
        )

        # Requirement 2.2: Endpoint returns HTTP 200 for valid input
        assert response.status_code == 200, \
            f"Expected HTTP 200 for valid input, got {response.status_code}"

        data = response.json()

        # Requirement 3.3: Response contains complete ensemble result
        # Verify all required top-level fields are present
        required_fields = [
            "article_id",
            "primary_prediction",
            "voting_strategies",
            "individual_models",
            "merged_explanation",
            "execution_time_ms"
        ]

        for field in required_fields:
            assert field in data, \
                f"Response must contain {field} field"

        # Verify voting_strategies contains all three strategies
        voting_strategies = data["voting_strategies"]
        required_strategies = ["hard_voting", "soft_voting", "weighted_voting"]

        for strategy in required_strategies:
            assert strategy in voting_strategies, \
                f"Voting strategies must contain {strategy}"

            # Each strategy must have label and confidence
            assert "label" in voting_strategies[strategy], \
                f"{strategy} must have label"
            assert "confidence" in voting_strategies[strategy], \
                f"{strategy} must have confidence"

        # Verify individual_models contains all three models
        individual_models = data["individual_models"]
        assert len(individual_models) >= 1, \
            "Response must contain at least one individual model prediction"

        # In normal operation (no failures), should have all 3 models
        if data.get("warnings") is None:
            assert len(individual_models) == 3, \
                f"Expected 3 individual models without warnings, got {len(individual_models)}"

        # Verify response structure is valid JSON
        assert isinstance(data, dict), \
            "Response must be a valid JSON object"

        # Verify article_id is a valid UUID
        try:
            uuid.UUID(data["article_id"])
        except ValueError:
            pytest.fail(
                f"article_id must be a valid UUID, got {data['article_id']}")

        # Verify execution_time_ms is positive
        assert data["execution_time_ms"] > 0, \
            f"execution_time_ms must be positive, got {data['execution_time_ms']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

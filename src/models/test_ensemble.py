"""
Unit tests for ensemble classifier.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from .ensemble import (
    EnsembleClassifier,
    ModelPrediction,
    get_ensemble_classifier
)


@pytest.fixture
def mock_predictions():
    """Create mock predictions for testing voting strategies."""
    return [
        ModelPrediction(
            model_name='distilbert',
            label='Fake',
            confidence=0.85,
            scores={'True': 0.10, 'Fake': 0.85, 'Satire': 0.03, 'Bias': 0.02},
            tokens=[{'token': 'breaking', 'score': 0.9},
                    {'token': 'news', 'score': 0.7}]
        ),
        ModelPrediction(
            model_name='roberta',
            label='Fake',
            confidence=0.82,
            scores={'True': 0.12, 'Fake': 0.82, 'Satire': 0.04, 'Bias': 0.02},
            tokens=[{'token': 'breaking', 'score': 0.8},
                    {'token': 'shocking', 'score': 0.6}]
        ),
        ModelPrediction(
            model_name='xlnet',
            label='Fake',
            confidence=0.88,
            scores={'True': 0.08, 'Fake': 0.88, 'Satire': 0.02, 'Bias': 0.02},
            tokens=[{'token': 'news', 'score': 0.85},
                    {'token': 'shocking', 'score': 0.75}]
        )
    ]


@pytest.fixture
def ensemble():
    """Create ensemble classifier instance."""
    return EnsembleClassifier()


def test_hard_voting_unanimous(ensemble, mock_predictions):
    """Test hard voting when all models agree."""
    label, confidence = ensemble.hard_voting(mock_predictions)
    assert label == 'Fake'
    assert 0.82 <= confidence <= 0.88  # Average of the three confidences


def test_hard_voting_majority(ensemble):
    """Test hard voting with majority vote."""
    predictions = [
        ModelPrediction('distilbert', 'Fake', 0.85, {'Fake': 0.85}, []),
        ModelPrediction('roberta', 'Fake', 0.82, {'Fake': 0.82}, []),
        ModelPrediction('xlnet', 'True', 0.75, {'True': 0.75}, [])
    ]
    label, confidence = ensemble.hard_voting(predictions)
    assert label == 'Fake'
    assert confidence == pytest.approx((0.85 + 0.82) / 2, rel=0.01)


def test_soft_voting(ensemble, mock_predictions):
    """Test soft voting averages probabilities correctly."""
    scores = ensemble.soft_voting(mock_predictions)

    # Check all labels present
    assert 'True' in scores
    assert 'Fake' in scores
    assert 'Satire' in scores
    assert 'Bias' in scores

    # Check Fake has highest score (all models agree)
    assert scores['Fake'] > scores['True']
    assert scores['Fake'] > scores['Satire']
    assert scores['Fake'] > scores['Bias']

    # Check approximate values
    expected_fake = (0.85 + 0.82 + 0.88) / 3
    assert scores['Fake'] == pytest.approx(expected_fake, rel=0.01)


def test_weighted_voting(ensemble, mock_predictions):
    """Test weighted voting applies accuracy weights correctly."""
    scores = ensemble.weighted_voting(mock_predictions)

    # Check all labels present
    assert 'True' in scores
    assert 'Fake' in scores

    # Fake should have highest score
    assert scores['Fake'] > scores['True']

    # Weighted average should be different from simple average
    soft_scores = ensemble.soft_voting(mock_predictions)
    # XLNet has highest weight (0.862) and highest Fake score (0.88)
    # So weighted should be slightly higher than soft
    assert scores['Fake'] >= soft_scores['Fake'] - 0.01


def test_merge_explanations(ensemble, mock_predictions):
    """Test token explanation merging."""
    merged = ensemble._merge_explanations(mock_predictions)

    # Should return list of token dicts
    assert isinstance(merged, list)
    assert len(merged) > 0

    # Check structure
    for token_data in merged:
        assert 'token' in token_data
        assert 'score' in token_data
        assert isinstance(token_data['score'], float)

    # Should be sorted by score descending
    scores = [t['score'] for t in merged]
    assert scores == sorted(scores, reverse=True)

    # Common tokens should be present
    tokens = [t['token'] for t in merged]
    assert 'breaking' in tokens or 'news' in tokens


@pytest.mark.asyncio
async def test_predict_ensemble_success():
    """Test successful ensemble prediction with mocked models."""
    ensemble = EnsembleClassifier()

    # Mock the predict method for each model
    mock_result = {
        'label': 'Fake',
        'confidence': 0.85,
        'scores': {'True': 0.10, 'Fake': 0.85, 'Satire': 0.03, 'Bias': 0.02},
        'tokens': [{'token': 'test', 'score': 0.9}]
    }

    with patch.object(ensemble, '_predict_with_timeout', return_value=mock_result):
        result = await ensemble.predict_ensemble("Test article text")

        # Check result structure
        assert result.hard_voting_label == 'Fake'
        assert 0.0 <= result.hard_voting_confidence <= 1.0
        assert result.soft_voting_label == 'Fake'
        assert 0.0 <= result.soft_voting_confidence <= 1.0
        assert result.weighted_voting_label == 'Fake'
        assert 0.0 <= result.weighted_voting_confidence <= 1.0

        # Check individual predictions
        assert len(result.individual_predictions) == 3
        for pred in result.individual_predictions:
            assert pred.label == 'Fake'
            assert pred.confidence == 0.85

        # Check execution time
        assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_predict_ensemble_partial_failure():
    """Test ensemble handles partial model failures gracefully."""
    ensemble = EnsembleClassifier()

    # Mock one model to fail
    def mock_predict(model_name, text, timeout):
        if model_name == 'roberta':
            raise RuntimeError("Model failed")
        return {
            'label': 'Fake',
            'confidence': 0.85,
            'scores': {'True': 0.10, 'Fake': 0.85, 'Satire': 0.03, 'Bias': 0.02},
            'tokens': [{'token': 'test', 'score': 0.9}]
        }

    with patch.object(ensemble, '_predict_with_timeout', side_effect=mock_predict):
        result = await ensemble.predict_ensemble("Test article text")

        # Should still return result with 2 models
        assert len(result.individual_predictions) == 2
        assert result.warnings is not None
        assert any('roberta' in w for w in result.warnings)


@pytest.mark.asyncio
async def test_predict_ensemble_all_fail():
    """Test ensemble raises error when all models fail."""
    ensemble = EnsembleClassifier()

    with patch.object(ensemble, '_predict_with_timeout', return_value=None):
        with pytest.raises(RuntimeError, match="All models failed"):
            await ensemble.predict_ensemble("Test article text")


def test_get_ensemble_classifier_singleton():
    """Test that get_ensemble_classifier returns singleton instance."""
    classifier1 = get_ensemble_classifier()
    classifier2 = get_ensemble_classifier()
    assert classifier1 is classifier2


def test_ensemble_confidence_bounds(ensemble, mock_predictions):
    """Test that all voting strategies produce confidence in [0, 1]."""
    # Hard voting
    _, hard_conf = ensemble.hard_voting(mock_predictions)
    assert 0.0 <= hard_conf <= 1.0

    # Soft voting
    soft_scores = ensemble.soft_voting(mock_predictions)
    for score in soft_scores.values():
        assert 0.0 <= score <= 1.0

    # Weighted voting
    weighted_scores = ensemble.weighted_voting(mock_predictions)
    for score in weighted_scores.values():
        assert 0.0 <= score <= 1.0


def test_voting_deterministic(ensemble, mock_predictions):
    """Test that voting strategies are deterministic."""
    # Run multiple times
    hard1, conf1 = ensemble.hard_voting(mock_predictions)
    hard2, conf2 = ensemble.hard_voting(mock_predictions)
    assert hard1 == hard2
    assert conf1 == conf2

    soft1 = ensemble.soft_voting(mock_predictions)
    soft2 = ensemble.soft_voting(mock_predictions)
    assert soft1 == soft2

    weighted1 = ensemble.weighted_voting(mock_predictions)
    weighted2 = ensemble.weighted_voting(mock_predictions)
    assert weighted1 == weighted2

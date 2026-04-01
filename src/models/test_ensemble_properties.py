"""
Property-based tests for ensemble classifier.
Feature: phase-1-enhancements

Uses hypothesis for property-based testing with 100 iterations per property.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from .ensemble import get_ensemble_classifier


# Strategy for generating valid text inputs
# Text must be at least 10 characters (per Requirement 2.5)
valid_text_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')),
    min_size=10,
    max_size=500
).filter(lambda x: len(x.strip()) >= 10)


# Property 1: Ensemble Parallel Execution
# **Validates: Requirements 1.1, 1.3**
@pytest.mark.asyncio
@given(text=valid_text_strategy)
@settings(
    max_examples=100,
    deadline=None,  # Disable deadline for model inference
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_ensemble_parallel_execution(text):
    """
    Property 1: Ensemble Parallel Execution

    For any valid text input, when ensemble prediction is invoked,
    all three models (DistilBERT, RoBERTa, XLNet) shall be executed
    and return predictions.

    **Validates: Requirements 1.1, 1.3**
    """
    ensemble = get_ensemble_classifier()

    # Execute ensemble prediction
    result = await ensemble.predict_ensemble(text)

    # Requirement 1.1: All three models invoked
    model_names = {pred.model_name for pred in result.individual_predictions}
    expected_models = {'distilbert', 'roberta', 'xlnet'}

    # If there are warnings, some models may have failed (Req 1.7)
    # But at least one model must succeed
    assert len(result.individual_predictions) >= 1, \
        "At least one model must return a prediction"

    # If no warnings, all three models should have succeeded
    if not result.warnings:
        assert model_names == expected_models, \
            f"Expected all three models, got {model_names}"

    # Requirement 1.3: All voting strategies computed
    assert result.hard_voting_label is not None, \
        "Hard voting label must be present"
    assert result.soft_voting_label is not None, \
        "Soft voting label must be present"
    assert result.weighted_voting_label is not None, \
        "Weighted voting label must be present"

    # All voting strategies should have confidence scores
    assert 0.0 <= result.hard_voting_confidence <= 1.0, \
        "Hard voting confidence must be in [0, 1]"
    assert 0.0 <= result.soft_voting_confidence <= 1.0, \
        "Soft voting confidence must be in [0, 1]"
    assert 0.0 <= result.weighted_voting_confidence <= 1.0, \
        "Weighted voting confidence must be in [0, 1]"

    # Soft and weighted voting should have score dictionaries
    assert isinstance(result.soft_voting_scores, dict), \
        "Soft voting scores must be a dictionary"
    assert isinstance(result.weighted_voting_scores, dict), \
        "Weighted voting scores must be a dictionary"

    # All individual predictions should have required fields
    for pred in result.individual_predictions:
        assert pred.model_name in expected_models, \
            f"Invalid model name: {pred.model_name}"
        assert pred.label is not None, \
            f"Model {pred.model_name} must have a label"
        assert 0.0 <= pred.confidence <= 1.0, \
            f"Model {pred.model_name} confidence must be in [0, 1]"
        assert isinstance(pred.scores, dict), \
            f"Model {pred.model_name} scores must be a dictionary"
        assert isinstance(pred.tokens, list), \
            f"Model {pred.model_name} tokens must be a list"

    # Merged explanation should be present
    assert isinstance(result.merged_explanation, list), \
        "Merged explanation must be a list"

    # Execution time should be recorded
    assert result.execution_time_ms > 0, \
        "Execution time must be positive"


# Property 4: Voting Strategy Correctness
# **Validates: Requirements 12.1, 12.2, 12.3, 1.8**
@pytest.mark.asyncio
@given(text=valid_text_strategy)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_voting_strategy_correctness(text):
    """
    Property 4: Voting Strategy Correctness

    For any set of three model predictions, hard voting shall select the label
    with maximum vote count, soft voting shall average probability scores then
    select maximum, and weighted voting shall apply accuracy weights
    (0.859, 0.858, 0.862) before averaging then selecting maximum.

    **Validates: Requirements 12.1, 12.2, 12.3, 1.8**
    """
    ensemble = get_ensemble_classifier()
    result = await ensemble.predict_ensemble(text)

    # Skip if not all models succeeded (partial failure case)
    if len(result.individual_predictions) < 3:
        return

    predictions = result.individual_predictions

    # Requirement 12.1: Hard voting selects label with maximum vote count
    vote_counts = {}
    for pred in predictions:
        label = pred.label
        vote_counts[label] = vote_counts.get(label, 0) + 1

    expected_hard_label = max(vote_counts.items(), key=lambda x: x[1])[0]
    assert result.hard_voting_label == expected_hard_label, \
        f"Hard voting should select {expected_hard_label}, got {result.hard_voting_label}"

    # Requirement 12.2: Soft voting averages probability scores
    all_labels = set()
    for pred in predictions:
        all_labels.update(pred.scores.keys())

    expected_soft_scores = {}
    for label in all_labels:
        scores = [pred.scores.get(label, 0.0) for pred in predictions]
        expected_soft_scores[label] = sum(scores) / len(scores)

    expected_soft_label = max(
        expected_soft_scores.items(), key=lambda x: x[1])[0]
    assert result.soft_voting_label == expected_soft_label, \
        f"Soft voting should select {expected_soft_label}, got {result.soft_voting_label}"

    # Verify soft voting scores match expected averages (within rounding tolerance)
    for label in all_labels:
        expected = expected_soft_scores[label]
        actual = result.soft_voting_scores[label]
        assert abs(actual - expected) < 0.001, \
            f"Soft voting score for {label} should be {expected:.4f}, got {actual:.4f}"

    # Requirement 12.3 & 1.8: Weighted voting applies accuracy weights
    weights = {
        'distilbert': 0.859,
        'roberta': 0.858,
        'xlnet': 0.862
    }

    expected_weighted_scores = {}
    total_weight = sum(weights[pred.model_name] for pred in predictions)

    for label in all_labels:
        weighted_sum = 0.0
        for pred in predictions:
            score = pred.scores.get(label, 0.0)
            weight = weights[pred.model_name]
            weighted_sum += score * weight
        expected_weighted_scores[label] = weighted_sum / total_weight

    expected_weighted_label = max(
        expected_weighted_scores.items(), key=lambda x: x[1])[0]
    assert result.weighted_voting_label == expected_weighted_label, \
        f"Weighted voting should select {expected_weighted_label}, got {result.weighted_voting_label}"

    # Verify weighted voting scores match expected (within rounding tolerance)
    for label in all_labels:
        expected = expected_weighted_scores[label]
        actual = result.weighted_voting_scores[label]
        assert abs(actual - expected) < 0.001, \
            f"Weighted voting score for {label} should be {expected:.4f}, got {actual:.4f}"


# Property 5: Probability Sum Invariant
# **Validates: Requirements 12.4**
@pytest.mark.asyncio
@given(text=valid_text_strategy)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_probability_sum_invariant(text):
    """
    Property 5: Probability Sum Invariant

    For any ensemble voting result (soft or weighted), the sum of probability
    scores across all classes shall equal 1.0 within 0.001 tolerance.

    **Validates: Requirements 12.4**
    """
    ensemble = get_ensemble_classifier()
    result = await ensemble.predict_ensemble(text)

    # Requirement 12.4: Soft voting probabilities sum to 1.0
    soft_sum = sum(result.soft_voting_scores.values())
    assert abs(soft_sum - 1.0) < 0.001, \
        f"Soft voting probabilities should sum to 1.0, got {soft_sum:.6f}"

    # Requirement 12.4: Weighted voting probabilities sum to 1.0
    weighted_sum = sum(result.weighted_voting_scores.values())
    assert abs(weighted_sum - 1.0) < 0.001, \
        f"Weighted voting probabilities should sum to 1.0, got {weighted_sum:.6f}"

    # All individual model scores should also sum to 1.0
    for pred in result.individual_predictions:
        model_sum = sum(pred.scores.values())
        assert abs(model_sum - 1.0) < 0.001, \
            f"Model {pred.model_name} probabilities should sum to 1.0, got {model_sum:.6f}"


# Property 6: Ensemble Determinism
# **Validates: Requirements 1.9**
@pytest.mark.asyncio
@given(text=valid_text_strategy)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_ensemble_determinism(text):
    """
    Property 6: Ensemble Determinism

    For any valid text input, running ensemble prediction twice shall produce
    identical results (same labels, same confidence scores, same voting outcomes).

    **Validates: Requirements 1.9**
    """
    ensemble = get_ensemble_classifier()

    # Run ensemble prediction twice with the same input
    result1 = await ensemble.predict_ensemble(text)
    result2 = await ensemble.predict_ensemble(text)

    # Requirement 1.9: Same labels for all voting strategies
    assert result1.hard_voting_label == result2.hard_voting_label, \
        f"Hard voting labels differ: {result1.hard_voting_label} vs {result2.hard_voting_label}"
    assert result1.soft_voting_label == result2.soft_voting_label, \
        f"Soft voting labels differ: {result1.soft_voting_label} vs {result2.soft_voting_label}"
    assert result1.weighted_voting_label == result2.weighted_voting_label, \
        f"Weighted voting labels differ: {result1.weighted_voting_label} vs {result2.weighted_voting_label}"

    # Requirement 1.9: Same confidence scores for all voting strategies
    assert abs(result1.hard_voting_confidence - result2.hard_voting_confidence) < 0.0001, \
        f"Hard voting confidence differs: {result1.hard_voting_confidence} vs {result2.hard_voting_confidence}"
    assert abs(result1.soft_voting_confidence - result2.soft_voting_confidence) < 0.0001, \
        f"Soft voting confidence differs: {result1.soft_voting_confidence} vs {result2.soft_voting_confidence}"
    assert abs(result1.weighted_voting_confidence - result2.weighted_voting_confidence) < 0.0001, \
        f"Weighted voting confidence differs: {result1.weighted_voting_confidence} vs {result2.weighted_voting_confidence}"

    # Requirement 1.9: Same voting scores for all classes
    assert result1.soft_voting_scores.keys() == result2.soft_voting_scores.keys(), \
        "Soft voting score keys differ between runs"
    for label in result1.soft_voting_scores.keys():
        assert abs(result1.soft_voting_scores[label] - result2.soft_voting_scores[label]) < 0.0001, \
            f"Soft voting score for {label} differs: {result1.soft_voting_scores[label]} vs {result2.soft_voting_scores[label]}"

    assert result1.weighted_voting_scores.keys() == result2.weighted_voting_scores.keys(), \
        "Weighted voting score keys differ between runs"
    for label in result1.weighted_voting_scores.keys():
        assert abs(result1.weighted_voting_scores[label] - result2.weighted_voting_scores[label]) < 0.0001, \
            f"Weighted voting score for {label} differs: {result1.weighted_voting_scores[label]} vs {result2.weighted_voting_scores[label]}"

    # Requirement 1.9: Same number of individual predictions
    assert len(result1.individual_predictions) == len(result2.individual_predictions), \
        f"Number of individual predictions differs: {len(result1.individual_predictions)} vs {len(result2.individual_predictions)}"

    # Requirement 1.9: Same individual model predictions
    # Sort by model name to ensure consistent comparison
    preds1 = sorted(result1.individual_predictions, key=lambda p: p.model_name)
    preds2 = sorted(result2.individual_predictions, key=lambda p: p.model_name)

    for pred1, pred2 in zip(preds1, preds2):
        assert pred1.model_name == pred2.model_name, \
            f"Model names differ: {pred1.model_name} vs {pred2.model_name}"
        assert pred1.label == pred2.label, \
            f"Model {pred1.model_name} labels differ: {pred1.label} vs {pred2.label}"
        assert abs(pred1.confidence - pred2.confidence) < 0.0001, \
            f"Model {pred1.model_name} confidence differs: {pred1.confidence} vs {pred2.confidence}"

        # Check that all score keys match
        assert pred1.scores.keys() == pred2.scores.keys(), \
            f"Model {pred1.model_name} score keys differ"

        # Check that all scores match
        for label in pred1.scores.keys():
            assert abs(pred1.scores[label] - pred2.scores[label]) < 0.0001, \
                f"Model {pred1.model_name} score for {label} differs: {pred1.scores[label]} vs {pred2.scores[label]}"


# Property 22: Majority Voting Correctness
# **Validates: Requirements 12.8**
@pytest.mark.asyncio
@given(text=valid_text_strategy)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
async def test_majority_voting_correctness(text):
    """
    Property 22: Majority Voting Correctness

    For any ensemble prediction where two models agree on a label and one
    disagrees, hard voting shall return the majority label.

    **Validates: Requirements 12.8**
    """
    ensemble = get_ensemble_classifier()
    result = await ensemble.predict_ensemble(text)

    # Skip if not all models succeeded
    if len(result.individual_predictions) < 3:
        return

    predictions = result.individual_predictions

    # Count votes for each label
    vote_counts = {}
    for pred in predictions:
        label = pred.label
        vote_counts[label] = vote_counts.get(label, 0) + 1

    # Requirement 12.8: If there's a majority (2 or 3 votes), hard voting returns it
    max_votes = max(vote_counts.values())

    # If there's a clear majority (2 or 3 votes for one label)
    if max_votes >= 2:
        majority_label = max(vote_counts.items(), key=lambda x: x[1])[0]
        assert result.hard_voting_label == majority_label, \
            f"Hard voting should return majority label {majority_label}, got {result.hard_voting_label}"

    # Additional check: If two models agree and one disagrees
    if len(vote_counts) == 2 and max_votes == 2:
        # This is the exact scenario: 2 agree, 1 disagrees
        majority_label = max(vote_counts.items(), key=lambda x: x[1])[0]
        assert result.hard_voting_label == majority_label, \
            f"When 2 models agree and 1 disagrees, hard voting should return {majority_label}, got {result.hard_voting_label}"

"""
Ensemble classifier combining DistilBERT, RoBERTa, and XLNet
with parallel execution and multiple voting strategies.
"""

import asyncio
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .inference import get_classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenImportance:
    token: str
    score: float


@dataclass
class ModelPrediction:
    model_name: str
    label: str
    confidence: float
    scores: Dict[str, float]
    tokens: List[Dict]


@dataclass
class EnsembleResult:
    hard_voting_label: str
    hard_voting_confidence: float
    soft_voting_label: str
    soft_voting_confidence: float
    soft_voting_scores: Dict[str, float]
    weighted_voting_label: str
    weighted_voting_confidence: float
    weighted_voting_scores: Dict[str, float]
    individual_predictions: List[ModelPrediction]
    merged_explanation: List[Dict]
    execution_time_ms: float
    warnings: Optional[List[str]] = None


class EnsembleClassifier:
    """Combines predictions from all three models using voting strategies."""

    def __init__(self):
        self.model_names = ['distilbert', 'roberta', 'xlnet']
        self.models = {name: get_classifier(name) for name in self.model_names}
        self.weights = {'distilbert': 0.859, 'roberta': 0.858, 'xlnet': 0.862}
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def predict_ensemble(self, text: str, model_timeout: float = 10.0,
                               total_timeout: float = 15.0) -> EnsembleResult:
        start_time = time.time()
        warnings = []

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self.executor, self._predict_with_timeout, name, text, model_timeout)
            for name in self.model_names
        ]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=total_timeout
            )
        except asyncio.TimeoutError:
            warnings.append("Ensemble prediction exceeded total timeout")
            raise

        valid_predictions = []
        for name, result in zip(self.model_names, results):
            if isinstance(result, Exception):
                warnings.append(f"{name} failed: {str(result)}")
            elif result is None:
                warnings.append(f"{name} returned no result")
            else:
                valid_predictions.append(ModelPrediction(
                    model_name=name,
                    label=result['label'],
                    confidence=result['confidence'],
                    scores=result['scores'],
                    tokens=result['tokens']
                ))

        if not valid_predictions:
            raise RuntimeError("All models failed to process the request")

        hard_label, hard_conf = self.hard_voting(valid_predictions)
        soft_scores = self.soft_voting(valid_predictions)
        soft_label = max(soft_scores.items(), key=lambda x: x[1])[0]
        soft_conf = soft_scores[soft_label]

        weighted_scores = self.weighted_voting(valid_predictions)
        weighted_label = max(weighted_scores.items(), key=lambda x: x[1])[0]
        weighted_conf = weighted_scores[weighted_label]

        merged_tokens = self._merge_explanations(valid_predictions)
        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"Ensemble completed in {execution_time:.2f}ms with {len(valid_predictions)}/{len(self.model_names)} models")
        if warnings:
            logger.warning(f"Ensemble warnings: {warnings}")

        return EnsembleResult(
            hard_voting_label=hard_label,
            hard_voting_confidence=hard_conf,
            soft_voting_label=soft_label,
            soft_voting_confidence=soft_conf,
            soft_voting_scores=soft_scores,
            weighted_voting_label=weighted_label,
            weighted_voting_confidence=weighted_conf,
            weighted_voting_scores=weighted_scores,
            individual_predictions=valid_predictions,
            merged_explanation=merged_tokens,
            execution_time_ms=round(execution_time, 2),
            warnings=warnings if warnings else None
        )

    def _predict_with_timeout(self, model_name: str, text: str, timeout: float) -> Optional[Dict]:
        try:
            return self.models[model_name].predict(text)
        except Exception as e:
            logger.error(f"[ensemble] {model_name} prediction failed: {e}")
            return None

    def hard_voting(self, predictions: List[ModelPrediction]) -> tuple[str, float]:
        votes = {}
        for pred in predictions:
            votes[pred.label] = votes.get(pred.label, 0) + 1
        winning_label = max(votes.items(), key=lambda x: x[1])[0]
        confidences = [
            p.confidence for p in predictions if p.label == winning_label]
        return winning_label, round(sum(confidences) / len(confidences), 4)

    def soft_voting(self, predictions: List[ModelPrediction]) -> Dict[str, float]:
        all_labels = set(
            label for pred in predictions for label in pred.scores)
        return {
            label: round(sum(p.scores.get(label, 0.0)
                         for p in predictions) / len(predictions), 4)
            for label in all_labels
        }

    def weighted_voting(self, predictions: List[ModelPrediction]) -> Dict[str, float]:
        all_labels = set(
            label for pred in predictions for label in pred.scores)
        total_weight = sum(self.weights[p.model_name] for p in predictions)
        return {
            label: round(
                sum(p.scores.get(label, 0.0) *
                    self.weights[p.model_name] for p in predictions) / total_weight,
                4
            )
            for label in all_labels
        }

    def _merge_explanations(self, predictions: List[ModelPrediction]) -> List[Dict]:
        token_scores: Dict[str, float] = {}
        token_counts: Dict[str, int] = {}
        for pred in predictions:
            for td in pred.tokens:
                token = td['token']
                token_scores[token] = token_scores.get(
                    token, 0.0) + td['score']
                token_counts[token] = token_counts.get(token, 0) + 1
        merged = [
            {'token': t, 'score': round(token_scores[t] / token_counts[t], 4)}
            for t in token_scores
        ]
        return sorted(merged, key=lambda x: x['score'], reverse=True)[:10]


_ensemble_classifier: Optional[EnsembleClassifier] = None


def get_ensemble_classifier() -> EnsembleClassifier:
    global _ensemble_classifier
    if _ensemble_classifier is None:
        _ensemble_classifier = EnsembleClassifier()
    return _ensemble_classifier

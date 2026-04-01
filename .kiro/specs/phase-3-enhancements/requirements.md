# Requirements Document: Phase 3 Enhancements

## Introduction

Phase 3 focuses on closing the loop between user feedback and model quality. Building on the feedback collection (Phase 2), Phase 3 introduces:

1. **Active Learning Pipeline** — intelligently select the most valuable feedback samples for retraining
2. **Model Versioning & Registry** — track model versions, accuracy metrics, and deployment history
3. **A/B Testing Framework** — route a percentage of traffic to a challenger model and compare accuracy
4. **Confidence Calibration** — post-process raw softmax scores to better reflect true accuracy
5. **Automated Accuracy Tracking** — continuously monitor model performance against labeled feedback

All features remain within free-tier constraints.

## Glossary

- **Active_Learning**: Strategy for selecting the most informative unlabeled samples for human annotation
- **Uncertainty_Sampling**: Active learning strategy that prioritizes samples where the model is least confident
- **Model_Registry**: Database table tracking model versions, training metadata, and accuracy metrics
- **Challenger_Model**: A newly retrained model being evaluated against the current production model
- **Champion_Model**: The current production model serving predictions
- **A/B_Test**: Traffic split between champion and challenger models to compare real-world accuracy
- **Calibration**: Adjusting model confidence scores so that a 70% confidence prediction is correct ~70% of the time
- **ECE**: Expected Calibration Error — measures how well confidence scores match actual accuracy
- **Drift**: Degradation in model accuracy over time as the distribution of real-world articles shifts

---

## Requirement 1: Active Learning Sample Selection

**User Story:** As a developer, I want the system to identify which predictions are most worth reviewing, so that human annotation effort is focused where it improves the model most.

### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at `/active-learning/samples` that returns the top N predictions where the model was least confident
2. THE endpoint SHALL accept a `limit` parameter (default 20, max 100) and a `strategy` parameter (`uncertainty` or `margin`)
3. WHEN `strategy=uncertainty`, THE endpoint SHALL return predictions sorted by entropy of the probability distribution (highest entropy = most uncertain)
4. WHEN `strategy=margin`, THE endpoint SHALL return predictions sorted by the difference between the top-2 class probabilities (smallest margin = most uncertain)
5. THE endpoint SHALL only return predictions that have not yet received user feedback
6. THE endpoint SHALL require `Authorization: Bearer {ADMIN_TOKEN}` header
7. FOR ALL returned samples, entropy SHALL equal `-sum(p * log(p))` for each class probability (invariant property)
8. FOR ALL returned samples, margin SHALL equal `p_top1 - p_top2` where p_top1 >= p_top2 (invariant property)

---

## Requirement 2: Feedback-Driven Annotation Queue

**User Story:** As a developer, I want a prioritized queue of articles needing human labels, so that I can efficiently annotate the most impactful samples.

### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at `/active-learning/queue` returning uncertain predictions formatted for annotation
2. EACH queue item SHALL include: article_id, text_preview, predicted_label, confidence, scores (all 4 classes), created_at
3. THE endpoint SHALL exclude articles already in the `feedback` table
4. THE Frontend_App SHALL add an "Annotation Queue" view accessible from the Analytics page (admin only, gated by a local `VITE_ADMIN_MODE=true` env var)
5. THE Annotation Queue view SHALL display each article with its text and predicted label, and allow the reviewer to confirm or correct the label with a single click
6. WHEN a reviewer submits a correction, THE Frontend_App SHALL call `POST /feedback` and remove the item from the queue
7. FOR ALL queue items, confidence SHALL be below 0.85 (only uncertain predictions qualify)

---

## Requirement 3: Model Registry

**User Story:** As a developer, I want to track all model versions and their accuracy metrics, so that I can compare models and roll back if needed.

### Acceptance Criteria

1. THE Backend_API SHALL create a `model_registry` table in Supabase with columns: id, model_name, version, accuracy, f1_macro, training_samples, feedback_samples, trained_at, deployed_at, is_active, notes
2. THE Backend_API SHALL expose a GET endpoint at `/models/registry` returning all registered model versions ordered by trained_at DESC
3. THE retraining script (`scripts/retrain.py`) SHALL automatically insert a record into `model_registry` after successful training
4. THE Backend_API SHALL expose a POST endpoint at `/models/registry/{id}/deploy` that sets `is_active=true` for the specified version and `is_active=false` for all others of the same model_name
5. WHEN a model version is deployed, THE inference engine SHALL load the new weights on the next request (without restarting the server)
6. FOR ALL registry records, accuracy SHALL be between 0.0 and 1.0 (invariant property)
7. FOR ALL model_name values, exactly one version SHALL have `is_active=true` at any time (invariant property)

---

## Requirement 4: A/B Testing Framework

**User Story:** As a developer, I want to route a percentage of traffic to a challenger model, so that I can validate improvements before full deployment.

### Acceptance Criteria

1. THE Backend_API SHALL support an A/B test configuration stored in Supabase: challenger_model_name, challenger_version, traffic_split (0.0–1.0), is_active
2. WHEN an A/B test is active, THE Backend_API SHALL route `traffic_split` fraction of `/predict` requests to the challenger model
3. THE routing SHALL be deterministic per session_id — the same session always hits the same model variant
4. THE Backend_API SHALL tag each prediction with `ab_variant: "champion"` or `ab_variant: "challenger"` in the predictions table
5. THE Backend_API SHALL expose a GET endpoint at `/ab-test/results` returning: champion accuracy, challenger accuracy, sample counts, statistical significance (p-value using chi-squared test)
6. THE Backend_API SHALL expose POST endpoints at `/ab-test/start` and `/ab-test/stop` (admin only)
7. WHEN no A/B test is active, ALL traffic SHALL go to the champion model (traffic_split effectively 0)
8. FOR ALL A/B test sessions, the same session_id SHALL always receive the same variant (determinism property)
9. FOR ALL A/B test results, champion_count + challenger_count SHALL equal total predictions during the test period (invariant property)

---

## Requirement 5: Confidence Calibration

**User Story:** As a user, I want confidence scores that accurately reflect the model's true accuracy, so that I can trust the displayed percentages.

### Acceptance Criteria

1. THE retraining script SHALL compute a calibration map (temperature scaling) on the validation set after training
2. THE calibration map SHALL be stored as a `temperature` float value in the `model_registry` table
3. WHEN `temperature` is set for the active model, THE inference engine SHALL apply temperature scaling: `calibrated_logits = logits / temperature` before softmax
4. THE Backend_API SHALL expose a GET endpoint at `/models/calibration` returning the current ECE (Expected Calibration Error) for each model
5. FOR ALL calibrated predictions, the ECE SHALL be lower than the uncalibrated ECE (improvement invariant)
6. WHEN temperature = 1.0, calibrated scores SHALL equal uncalibrated scores (identity property)
7. FOR ALL temperature values, the sum of calibrated softmax probabilities SHALL equal 1.0 within 0.001 tolerance (invariant property)

---

## Requirement 6: Automated Accuracy Monitoring

**User Story:** As a developer, I want automatic alerts when model accuracy drops, so that I can retrain before users notice degradation.

### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at `/monitoring/accuracy` that computes rolling accuracy from feedback where predicted_label == actual_label over the last 7 days
2. THE endpoint SHALL return: rolling_accuracy, total_feedback_last_7d, accuracy_trend (improving/stable/degrading), days_since_last_retrain
3. WHEN rolling_accuracy drops below 0.75, THE Backend_API SHALL log a WARNING with message "Model accuracy below threshold: {accuracy:.2%}"
4. THE AnalyticsPage SHALL display the rolling accuracy gauge and trend indicator
5. THE AnalyticsPage SHALL display a "Retrain recommended" banner when rolling_accuracy < 0.75
6. FOR ALL accuracy computations, rolling_accuracy SHALL equal correct_predictions / total_feedback where total_feedback > 0 (invariant property)
7. WHEN total_feedback_last_7d == 0, THE endpoint SHALL return rolling_accuracy as null and trend as "insufficient_data"

---

## Requirement 7: Drift Detection

**User Story:** As a developer, I want to detect when the distribution of incoming articles shifts significantly, so that I know when the model needs retraining even without labeled feedback.

### Acceptance Criteria

1. THE Backend_API SHALL track the weekly distribution of predicted labels (% True/Fake/Satire/Bias) in a `label_distributions` table
2. THE Backend_API SHALL expose a GET endpoint at `/monitoring/drift` comparing the current week's label distribution to the baseline (first week of deployment)
3. THE drift score SHALL be computed as the Jensen-Shannon divergence between current and baseline distributions
4. WHEN drift score exceeds 0.1, THE endpoint SHALL return `drift_detected: true` with a warning message
5. THE AnalyticsPage SHALL display the drift score and a visual distribution comparison chart
6. FOR ALL drift scores, the value SHALL be between 0.0 and 1.0 (JS divergence is bounded)
7. WHEN current distribution equals baseline, drift score SHALL equal 0.0 (identity property)

---

## Requirement 8: Retraining Automation

**User Story:** As a developer, I want a one-command retraining workflow that handles data export, training, evaluation, and registry update, so that I can retrain in minutes.

### Acceptance Criteria

1. THE `scripts/retrain.py` script SHALL be extended to accept `--auto` flag that: fetches feedback from Supabase, exports CSV, trains the model, evaluates, and registers the result
2. WHEN `--auto` is used, THE script SHALL require at least 50 new feedback corrections since the last retrain (abort with message if fewer)
3. THE script SHALL send a summary to a configurable webhook URL (`RETRAIN_WEBHOOK_URL` env var) on completion: model, accuracy, samples_used, duration
4. THE script SHALL support `--dry-run` flag that prints what would happen without actually training
5. FOR ALL auto retraining runs, the training dataset SHALL include at least 10x more original data than feedback data (to prevent catastrophic forgetting)
6. THE script SHALL output a machine-readable JSON summary to stdout when `--json` flag is passed

---

## Requirement 9: Free Tier Constraints

**User Story:** As a developer, I want all Phase 3 features to stay within free-tier limits.

### Acceptance Criteria

1. THE `model_registry` and `label_distributions` tables SHALL use minimal storage (< 1MB total)
2. THE A/B testing routing SHALL use in-memory state — no additional database queries per request
3. THE calibration temperature scaling SHALL be a single float multiply — negligible compute overhead
4. THE drift detection SHALL run as a background task every 24 hours, not on every request
5. THE `/monitoring/accuracy` endpoint SHALL cache results for 5 minutes to reduce Supabase queries
6. ALL admin endpoints (`/active-learning/*`, `/ab-test/*`, `/models/registry`) SHALL require `ADMIN_TOKEN` to prevent public abuse

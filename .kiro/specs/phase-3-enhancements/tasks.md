# Implementation Plan: Phase 3 Enhancements

## Overview

Phase 3 closes the model improvement loop with active learning, model versioning, A/B testing, confidence calibration, and automated accuracy monitoring.

## Tasks

- [ ] 1. Database Schema Setup
  - [ ] 1.1 Create model_registry table
    - Add SQL migration: `model_registry` table with columns: id, model_name, version, accuracy, f1_macro, training_samples, feedback_samples, temperature, trained_at, deployed_at, is_active, notes
    - Add to `fake-news-api/scripts/setup_supabase.sql`
    - _Requirements: 3.1_

  - [ ] 1.2 Create label_distributions table
    - Add SQL migration: `label_distributions` table with columns: id, week_start, true_pct, fake_pct, satire_pct, bias_pct, total, created_at
    - _Requirements: 7.1_

  - [ ] 1.3 Add ab_variant column to predictions
    - Add migration: `ALTER TABLE predictions ADD COLUMN IF NOT EXISTS ab_variant VARCHAR(20)`
    - _Requirements: 4.4_

  - [ ] 1.4 Add registry methods to SupabaseClient
    - Add `register_model()` method to `supabase_client.py`
    - Add `deploy_model()` method to `supabase_client.py`
    - Add `get_active_model()` method returning current active version per model_name
    - _Requirements: 3.1, 3.3, 3.4_

- [ ] 2. Active Learning Backend
  - [ ] 2.1 Implement uncertainty scoring
    - Add `GET /active-learning/samples` endpoint to `main.py`
    - Implement entropy scoring for `strategy=uncertainty`
    - Implement margin scoring for `strategy=margin`
    - Filter out predictions already in feedback table
    - Require `ADMIN_TOKEN` authorization
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ] 2.2 Implement annotation queue endpoint
    - Add `GET /active-learning/queue` endpoint
    - Return items with confidence < 0.85 not yet in feedback table
    - _Requirements: 2.1, 2.2, 2.3, 2.7_

  - [ ] 2.3 Write unit tests for active learning endpoints
    - Test uncertainty scoring returns highest entropy samples first
    - Test margin scoring returns smallest margin samples first
    - Test items with existing feedback are excluded
    - Test 401 returned without admin token
    - _Requirements: 1.6, 1.7, 1.8, 2.7_

- [ ] 3. Annotation Queue Frontend
  - [ ] 3.1 Create AnnotationQueue page
    - Create `frontend/src/pages/AnnotationQueue.jsx`
    - Display uncertain predictions with text preview and model prediction
    - Add one-click label buttons (True/Fake/Satire/Bias)
    - On label click, call `POST /feedback` and remove from queue
    - Gate behind `VITE_ADMIN_MODE=true` env var
    - _Requirements: 2.4, 2.5, 2.6_

  - [ ] 3.2 Add route and nav link
    - Add `/annotation-queue` route to `main.jsx` with lazy loading
    - Add "Queue" link to Header (only visible when `VITE_ADMIN_MODE=true`)
    - _Requirements: 2.4_

- [ ] 4. Checkpoint — Active Learning complete
  - Verify: fetch uncertain samples, annotate via queue, confirm feedback stored

- [ ] 5. Model Registry Backend
  - [ ] 5.1 Add registry endpoints to API
    - Add `GET /models/registry` endpoint returning all versions ordered by trained_at DESC
    - Add `POST /models/registry/{id}/deploy` endpoint (admin only)
    - _Requirements: 3.2, 3.4_

  - [ ] 5.2 Add dynamic model loading to inference
    - Update `FakeNewsClassifier` to store `temperature` attribute
    - Add `reload_from_registry()` method that resets `_model` and `_tokenizer`
    - Apply temperature scaling in `predict()`: `calibrated_logits = outputs.logits / self.temperature`
    - _Requirements: 3.5, 5.3, 5.6, 5.7_

  - [ ] 5.3 Write unit tests for registry
    - Test `GET /models/registry` returns correct structure
    - Test `POST /models/registry/{id}/deploy` sets is_active correctly
    - Test only one version is active per model_name after deploy
    - _Requirements: 3.6, 3.7_

- [ ] 6. Confidence Calibration
  - [ ] 6.1 Create calibration module
    - Create `fake-news-api/src/models/calibration.py`
    - Implement `find_optimal_temperature()` using grid search over validation set
    - Implement `compute_ece()` for Expected Calibration Error
    - _Requirements: 5.1, 5.2_

  - [ ] 6.2 Integrate calibration into retraining script
    - After training, compute optimal temperature on validation set
    - Store temperature in `model_registry` record
    - Print ECE before and after calibration
    - _Requirements: 5.1, 5.2, 5.5_

  - [ ] 6.3 Add calibration endpoint
    - Add `GET /models/calibration` endpoint returning ECE per model
    - _Requirements: 5.4_

  - [ ] 6.4 Write property tests for calibration
    - Test temperature=1.0 produces identical scores to uncalibrated (identity property)
    - Test calibrated softmax sums to 1.0 within 0.001 tolerance
    - _Requirements: 5.6, 5.7_

- [ ] 7. A/B Testing Framework
  - [ ] 7.1 Create AB router utility
    - Create `fake-news-api/src/utils/ab_router.py`
    - Implement `ABRouter` class with `get_variant(session_id)` using MD5 hash
    - Implement `load_config(supabase_client)` to fetch active A/B test config
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 7.2 Integrate A/B routing into predict endpoint
    - Update `POST /predict` to check `ab_router.get_variant(session_id)`
    - Route to challenger model when variant == "challenger"
    - Tag prediction with `ab_variant` in database
    - _Requirements: 4.2, 4.3, 4.4, 4.7_

  - [ ] 7.3 Add A/B test management endpoints
    - Add `POST /ab-test/start` (admin only) — creates A/B test config in Supabase
    - Add `POST /ab-test/stop` (admin only) — deactivates A/B test
    - Add `GET /ab-test/results` — returns champion vs challenger accuracy comparison
    - _Requirements: 4.5, 4.6_

  - [ ] 7.4 Write property tests for A/B routing
    - Test same session_id always gets same variant (determinism property)
    - Test when no A/B test active, all traffic goes to champion
    - Test traffic split is approximately correct over 1000 sessions
    - _Requirements: 4.7, 4.8, 4.9_

- [ ] 8. Checkpoint — Registry, Calibration, A/B Testing complete
  - Verify: register a model, deploy it, start A/B test, check results endpoint

- [ ] 9. Monitoring & Drift Detection
  - [ ] 9.1 Create drift detector utility
    - Create `fake-news-api/src/utils/drift_detector.py`
    - Implement `jensen_shannon_divergence(p, q)` function
    - _Requirements: 7.3, 7.6, 7.7_

  - [ ] 9.2 Add monitoring endpoints
    - Add `GET /monitoring/accuracy` with 5-minute cache
    - Log WARNING when accuracy < 0.75
    - Add `GET /monitoring/drift` comparing current vs baseline label distribution
    - _Requirements: 6.1, 6.2, 6.3, 6.6, 6.7, 7.2, 7.3, 7.4_

  - [ ] 9.3 Add background drift tracking task
    - On startup, schedule a background task to record weekly label distribution to `label_distributions` table every 24 hours
    - _Requirements: 7.1, 9.4_

  - [ ] 9.4 Write property tests for monitoring
    - Test rolling_accuracy = correct / total (invariant)
    - Test JS divergence = 0 when distributions are identical (identity property)
    - Test JS divergence is between 0 and 1 for all inputs
    - _Requirements: 6.6, 7.6, 7.7_

- [ ] 10. Analytics Dashboard Updates
  - [ ] 10.1 Add accuracy gauge to AnalyticsPage
    - Display rolling 7-day accuracy as a gauge/progress bar
    - Show trend indicator (stable/degrading)
    - Show "Retrain recommended" banner when accuracy < 0.75
    - _Requirements: 6.4, 6.5_

  - [ ] 10.2 Add drift visualization to AnalyticsPage
    - Display current vs baseline label distribution as side-by-side bar charts
    - Display drift score with color coding (green < 0.05, amber 0.05-0.1, red > 0.1)
    - _Requirements: 7.5_

  - [ ] 10.3 Write unit tests for analytics updates
    - Test accuracy gauge renders correct color for each tier
    - Test retrain banner appears when accuracy < 0.75
    - Test drift chart renders with correct data

- [ ] 11. Retraining Script Extensions
  - [ ] 11.1 Add --auto flag to retrain.py
    - Implement `auto_retrain()` function that fetches feedback from Supabase
    - Check minimum sample threshold (50 new corrections)
    - Auto-register result in model_registry after training
    - Send webhook notification on completion
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 11.2 Add --dry-run and --json flags
    - `--dry-run`: print what would happen without training
    - `--json`: output machine-readable summary to stdout
    - _Requirements: 8.4, 8.6_

  - [ ] 11.3 Test retraining automation
    - Run `--dry-run` to verify it prints correct plan
    - Run with synthetic feedback CSV to verify registry insert
    - _Requirements: 8.5_

- [ ] 12. Final Checkpoint — All Phase 3 features complete
  - Run full backend test suite
  - Verify end-to-end: annotate samples → retrain → register → deploy → monitor accuracy
  - Verify A/B test: start test → make predictions → check results → stop test

## Notes

- All admin endpoints require `ADMIN_TOKEN` env var — document in README
- `VITE_ADMIN_MODE=true` must be set in Vercel env vars to show annotation queue in frontend
- Temperature scaling is applied at inference time — no model retraining needed for calibration
- Drift detection runs as a background task — does not affect API response times
- A/B routing uses MD5 hash of session_id — deterministic, no state needed

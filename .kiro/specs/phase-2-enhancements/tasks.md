# Implementation Plan: Phase 2 Enhancements

## Overview

Phase 2 adds three major features to VeracityLens:

1. **URL Analysis** — fetch and analyze articles directly from URLs
2. **Analytics Dashboard** — platform-wide and per-user prediction statistics with charts
3. **Feedback & Retraining** — enhanced feedback collection, export, and model fine-tuning pipeline

## Tasks

- [ ] 1. URL Analysis Backend
  - [ ] 1.1 Create article extractor utility
    - Create `fake-news-api/src/utils/article_extractor.py`
    - Implement `extract_article(url)` using `newspaper3k`
    - Handle fetch errors, non-article pages, and insufficient content (<100 chars)
    - Return `{ text, title, source_domain, word_count }`
    - _Requirements: 1.4, 1.5, 1.6, 1.9, 1.10_

  - [ ] 1.2 Add `/analyze/url` endpoint
    - Add `UrlAnalysisRequest` schema to `fake-news-api/src/api/main.py`
    - Implement `POST /analyze/url` endpoint calling `extract_article()` then `predict()`
    - Store `source_url` in predictions table via background task
    - Return same response schema as `/predict` plus `source_url`, `source_domain`, `extracted_text`
    - _Requirements: 1.3, 1.7, 1.8, 1.9_

  - [ ] 1.3 Add `source_url` column to predictions table
    - Add migration SQL: `ALTER TABLE predictions ADD COLUMN IF NOT EXISTS source_url TEXT`
    - Update `store_prediction()` in `supabase_client.py` to accept and store `source_url`
    - _Requirements: 1.8_

  - [ ] 1.4 Write unit tests for URL analysis endpoint
    - Test valid URL returns 200 with extracted text
    - Test unreachable URL returns 422
    - Test non-article page returns 422
    - Test text too short returns 422
    - _Requirements: 1.6, 1.9, 1.10_

- [ ] 2. URL Analysis Frontend
  - [ ] 2.1 Add URL tab to AnalysisInput component
    - Update `frontend/src/components/AnalysisInput.jsx` with tab switcher (Text / URL)
    - Add URL input field with validation (must start with http:// or https://)
    - Show "Fetching article..." loading message during URL analysis
    - After extraction, switch to Text tab and populate textarea with extracted content
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ] 2.2 Add `analyzeUrl` API function
    - Add `analyzeUrl(url, model)` to `frontend/src/services/api.js`
    - Call `POST /analyze/url` endpoint
    - _Requirements: 1.2_

  - [ ] 2.3 Update App component for URL analysis
    - Update `frontend/src/App.jsx` to handle URL input mode
    - Call `analyzeUrl()` when URL tab is active
    - Display source domain badge on ResultCard when result came from URL
    - _Requirements: 2.3, 2.7_

  - [ ] 2.4 Write unit tests for URL input
    - Test URL tab renders correctly
    - Test invalid URL shows validation error
    - Test successful URL analysis populates text tab
    - _Requirements: 2.5, 2.6_

- [ ] 3. Checkpoint — URL Analysis complete
  - Verify end-to-end: paste a real news URL, confirm article is extracted and classified correctly

- [ ] 4. Analytics Backend
  - [ ] 4.1 Extend `/stats` endpoint
    - Update `get_prediction_stats()` in `supabase_client.py` to return `by_model` and `daily_counts` (last 7 days)
    - Add 60-second in-memory cache to reduce Supabase query load
    - _Requirements: 3.10, 3.11, 3.12, 10.6_

  - [ ] 4.2 Extend `/history/{session_id}` with summary
    - Update history endpoint to compute and return `summary` field: total, by_label, avg_confidence, most_used_model
    - _Requirements: 4.3, 4.4, 4.5_

  - [ ] 4.3 Add `/feedback/stats` endpoint
    - Implement `GET /feedback/stats` returning total_corrections, agreement_rate, corrections_by_label
    - _Requirements: 5.4, 5.5_

  - [ ] 4.4 Write unit tests for extended stats endpoints
    - Test `/stats` returns by_model and daily_counts
    - Test `/history/{id}` returns summary field
    - Test `/feedback/stats` returns agreement_rate
    - _Requirements: 3.11, 3.12, 4.5, 5.6_

- [ ] 5. Analytics Frontend
  - [ ] 5.1 Install Recharts
    - Run `npm install recharts` in `frontend/`
    - _Requirements: 10.3_

  - [ ] 5.2 Create AnalyticsPage component
    - Create `frontend/src/pages/AnalyticsPage.jsx`
    - Display total prediction count
    - Display label distribution pie chart (True/Fake/Satire/Bias) using Recharts PieChart
    - Display model usage bar chart using Recharts BarChart
    - Display 7-day prediction volume trend using Recharts BarChart
    - Display feedback agreement rate
    - Auto-refresh every 60 seconds
    - Handle loading and error states
    - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [ ] 5.3 Add Analytics route and nav link
    - Add "Analytics" link to `frontend/src/components/Header.jsx`
    - Add `/analytics` route to `frontend/src/main.jsx` with lazy loading
    - _Requirements: 3.1, 3.2_

  - [ ] 5.4 Add personal summary to HistoryPage
    - Update `frontend/src/pages/HistoryPage.jsx` to display summary section
    - Show total analyses, most common label, average confidence
    - Show mini label distribution using Recharts PieChart
    - _Requirements: 4.1, 4.2, 4.4_

  - [ ] 5.5 Write unit tests for AnalyticsPage
    - Test loading state renders skeleton
    - Test stats display correctly when data loads
    - Test error state shows retry button
    - _Requirements: 3.8_

- [ ] 6. Checkpoint — Analytics complete
  - Verify charts render correctly with real data from Supabase

- [ ] 7. Feedback Enhancement
  - [ ] 7.1 Add session_id to feedback table
    - Add migration SQL: `ALTER TABLE feedback ADD COLUMN IF NOT EXISTS session_id VARCHAR(36)`
    - Update `store_feedback()` in `supabase_client.py` to accept `session_id`
    - Update `/feedback` endpoint to extract session_id from `X-Session-ID` header
    - _Requirements: 5.2, 5.3_

  - [ ] 7.2 Add `/feedback/export` endpoint
    - Implement `GET /feedback/export` with `Authorization: Bearer {ADMIN_TOKEN}` guard
    - Filter to corrections only (predicted != actual), deduplicate by article_id
    - Return CSV via `StreamingResponse`
    - Add rate limiting: 10 requests per hour
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 10.5_

  - [ ] 7.3 Add ADMIN_TOKEN to environment
    - Add `ADMIN_TOKEN` to `.env.example`
    - Document in README that this must be set in HF Space secrets
    - _Requirements: 6.3_

  - [ ] 7.4 Write unit tests for feedback endpoints
    - Test `/feedback/export` returns 401 without token
    - Test `/feedback/export` returns CSV with correct columns
    - Test `/feedback/stats` returns correct agreement_rate
    - _Requirements: 6.3, 6.7, 5.6, 5.7_

- [ ] 8. Retraining Pipeline
  - [ ] 8.1 Create retrain.py script
    - Create `fake-news-api/scripts/retrain.py`
    - Implement `load_and_merge()` to combine feedback CSV with original training data sample
    - Implement `retrain()` with HuggingFace Trainer
    - Add accuracy regression guard (abort if new accuracy < original - 2%)
    - Save `retrain_log.json` with metrics
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ] 8.2 Test retraining script locally
    - Run with a small feedback CSV (even synthetic) to verify it completes without errors
    - Verify `retrain_log.json` is created with correct fields
    - _Requirements: 7.4, 7.7_

- [ ] 9. Checkpoint — Feedback & Retraining complete
  - Export feedback CSV, verify format is correct for retraining script

- [ ] 10. ResultCard Enhancements
  - [ ] 10.1 Add confidence calibration badge
    - Update `frontend/src/components/ResultCard.jsx` with `ConfidenceBadge` component
    - High (>=90%): green, Moderate (65-89%): amber, Low (<65%): red with caution text
    - Add tooltip explaining confidence score
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 10.2 Add alternative labels section
    - Add collapsible "Alternative predictions" section to ResultCard
    - Show top 3 non-primary labels with their probability scores
    - _Requirements: 8.6_

  - [ ] 10.3 Add Share button
    - Add Share button to ResultCard
    - Copy formatted text to clipboard using `navigator.clipboard.writeText()`
    - Show "Copied!" toast for 2 seconds on success
    - Show modal with text for manual copy when clipboard API unavailable
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 10.4 Add Download Report button
    - Add "Download Report" button to ResultCard
    - Generate and download `.txt` file with prediction details
    - Include: article preview, label, confidence, voting strategies (ensemble), timestamp
    - _Requirements: 9.5, 9.6_

  - [ ] 10.5 Write unit tests for ResultCard enhancements
    - Test ConfidenceBadge renders correct color/text for each tier
    - Test Share button copies correct text to clipboard
    - Test Download Report generates correct file content
    - _Requirements: 8.2, 8.3, 8.4, 9.2, 9.5_

- [ ] 11. Final Checkpoint — All Phase 2 features complete
  - Run full backend test suite
  - Run full frontend test suite
  - Verify end-to-end: URL analysis → analytics dashboard → feedback export → share result

## Notes

- Recharts is the charting library — lightweight and already used in similar React projects
- `newspaper3k` is already in `requirements.txt` — no new backend dependencies needed
- Retraining runs locally, not on HF Spaces — document this clearly
- All new endpoints follow the same error handling patterns established in Phase 1
- Stats caching is in-memory (not Redis) — resets on Space restart, which is acceptable

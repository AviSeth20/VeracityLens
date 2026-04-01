# Requirements Document: Phase 2 Enhancements

## Introduction

Phase 2 builds on the ensemble model, user history, and dark mode delivered in Phase 1. The focus is on three high-value features:

1. **URL Analysis** — users paste a URL and the system fetches and analyzes the article automatically
2. **Analytics Dashboard** — visualize prediction trends, label distributions, and model accuracy over time
3. **Feedback-Driven Retraining Pipeline** — surface user corrections as a curated dataset for periodic model fine-tuning

All features must remain within free-tier constraints (HuggingFace Spaces CPU-only, Supabase 500MB, Vercel free tier).

## Glossary

- **URL_Analyzer**: Backend service that fetches article content from a URL and extracts clean text for classification
- **Article_Extractor**: HTML parsing component that strips boilerplate and returns the main article body
- **Analytics_Dashboard**: Frontend page showing aggregated prediction statistics and trends
- **Feedback_Dataset**: Curated CSV export of user-corrected predictions used for model retraining
- **Retraining_Pipeline**: Script that fine-tunes a model on the feedback dataset and saves updated weights
- **Confidence_Calibration**: Post-processing step that adjusts raw model probabilities to better reflect true accuracy

---

## Requirement 1: URL-Based Article Analysis

**User Story:** As a user, I want to paste a news article URL and have the system automatically fetch and analyze it, so that I don't have to manually copy-paste article text.

### Acceptance Criteria

1. THE Frontend_App SHALL add a URL input tab alongside the existing text input tab in the AnalysisInput component
2. WHEN a user enters a valid HTTP/HTTPS URL and clicks Analyze, THE Frontend_App SHALL call the `/analyze/url` endpoint
3. THE Backend_API SHALL expose a POST endpoint at `/analyze/url` that accepts a URL string
4. WHEN the `/analyze/url` endpoint receives a valid URL, THE URL_Analyzer SHALL fetch the page content within 10 seconds
5. THE Article_Extractor SHALL extract the main article body, stripping navigation, ads, headers, and footers
6. THE Article_Extractor SHALL return at least 100 characters of clean article text or return HTTP 422 with "Could not extract article content"
7. WHEN extraction succeeds, THE Backend_API SHALL run the selected model's prediction on the extracted text and return the same response schema as `/predict`
8. THE Backend_API SHALL store the source URL alongside the prediction in the `predictions` table
9. WHEN the URL is unreachable or returns a non-200 status, THE Backend_API SHALL return HTTP 422 with "Could not fetch article: {reason}"
10. WHEN the URL points to a non-article page (e.g. homepage), THE Backend_API SHALL return HTTP 422 with "Page does not appear to contain a news article"
11. THE Frontend_App SHALL display the extracted article text in the input area after URL analysis so the user can see what was analyzed
12. FOR ALL valid article URLs, fetching then analyzing SHALL produce the same result as manually pasting the extracted text (equivalence property)

---

## Requirement 2: URL Input UI

**User Story:** As a user, I want a clean URL input experience that guides me through the process, so that I know what to expect when analyzing a URL.

### Acceptance Criteria

1. THE Frontend_App SHALL display two tabs in the AnalysisInput component: "Text" and "URL"
2. WHEN the "URL" tab is active, THE Frontend_App SHALL show a URL input field with placeholder "https://example.com/article"
3. WHEN the URL tab is active and the user clicks Analyze, THE Frontend_App SHALL show "Fetching article..." in the loading skeleton
4. WHEN article extraction completes, THE Frontend_App SHALL automatically switch to the "Text" tab and populate the text area with the extracted content
5. THE Frontend_App SHALL validate that the input starts with "http://" or "https://" before submitting
6. WHEN the URL input is invalid format, THE Frontend_App SHALL display "Please enter a valid URL starting with http:// or https://"
7. THE Frontend_App SHALL display the article source domain as a badge on the ResultCard when the result came from URL analysis

---

## Requirement 3: Analytics Dashboard

**User Story:** As a user, I want to see statistics about predictions made on the platform, so that I can understand trends in fake news detection.

### Acceptance Criteria

1. THE Frontend_App SHALL add an "Analytics" navigation link in the Header component
2. WHEN a user clicks "Analytics", THE Frontend_App SHALL navigate to `/analytics` route
3. THE Frontend_App SHALL create an AnalyticsPage component that displays platform-wide prediction statistics
4. THE AnalyticsPage SHALL display a label distribution chart showing the percentage of True/Fake/Satire/Bias predictions
5. THE AnalyticsPage SHALL display total prediction count, updated in real time from the `/stats` endpoint
6. THE AnalyticsPage SHALL display a model usage breakdown showing how often each model (distilbert/roberta/xlnet/ensemble) is used
7. THE AnalyticsPage SHALL display a 7-day prediction volume trend as a bar or line chart
8. WHEN the stats API is unavailable, THE AnalyticsPage SHALL display a graceful error state with a retry button
9. THE AnalyticsPage SHALL auto-refresh statistics every 60 seconds
10. THE Backend_API SHALL extend the `/stats` endpoint to return: total_predictions, by_label counts, by_model counts, and daily_counts for the last 7 days
11. FOR ALL stats responses, the sum of by_label counts SHALL equal total_predictions (invariant property)
12. FOR ALL stats responses, the sum of by_model counts SHALL equal total_predictions (invariant property)

---

## Requirement 4: Personal Analytics

**User Story:** As a user, I want to see my own prediction history statistics, so that I can understand my personal usage patterns.

### Acceptance Criteria

1. THE HistoryPage SHALL display a summary section at the top showing: total analyses, most common predicted label, and average confidence
2. THE HistoryPage SHALL display a mini label distribution chart for the current user's predictions
3. THE Backend_API SHALL extend the `/history/{session_id}` endpoint to include a `summary` field with: total, by_label counts, avg_confidence, most_used_model
4. WHEN a user has no history, THE HistoryPage SHALL show the summary section with all zeros
5. FOR ALL history summaries, the sum of by_label counts SHALL equal total (invariant property)

---

## Requirement 5: Feedback Collection Enhancement

**User Story:** As a user, I want to correct wrong predictions easily, so that I can help improve the model's accuracy.

### Acceptance Criteria

1. THE Frontend_App SHALL display the existing feedback panel on all ResultCard predictions (already exists — ensure it works for ensemble results too)
2. WHEN a user submits feedback, THE Backend_API SHALL store the correction in the `feedback` table with: article_id, predicted_label, actual_label, user_comment, session_id, created_at
3. THE Backend_API SHALL add `session_id` to the feedback table to track which session submitted the correction
4. THE Backend_API SHALL expose a GET endpoint at `/feedback/stats` returning: total_corrections, agreement_rate (% where predicted == actual), corrections_by_label
5. THE AnalyticsPage SHALL display the feedback agreement rate as a model accuracy indicator
6. FOR ALL feedback submissions, the actual_label SHALL be one of: "True", "Fake", "Satire", "Bias" (invariant property)
7. FOR ALL feedback submissions, the article_id SHALL reference an existing prediction (referential integrity property)

---

## Requirement 6: Feedback Dataset Export

**User Story:** As a developer, I want to export user-corrected predictions as a training dataset, so that I can periodically fine-tune the models.

### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at `/feedback/export` that returns a CSV of all feedback records where predicted_label != actual_label
2. THE exported CSV SHALL include columns: article_id, text (from predictions table), actual_label, confidence, model_name, created_at
3. THE `/feedback/export` endpoint SHALL require an `Authorization: Bearer {ADMIN_TOKEN}` header to prevent public access
4. THE Backend_API SHALL filter the export to only include feedback with confidence < 0.95 (uncertain predictions are more valuable for training)
5. THE exported dataset SHALL deduplicate by article_id, keeping the most recent correction
6. WHEN no feedback corrections exist, THE endpoint SHALL return an empty CSV with headers only
7. FOR ALL exported records, the actual_label SHALL differ from the model's predicted_label (invariant property — these are the corrections)

---

## Requirement 7: Retraining Pipeline Script

**User Story:** As a developer, I want a script that fine-tunes a model on the feedback dataset, so that I can improve accuracy without manual intervention.

### Acceptance Criteria

1. THE Retraining_Pipeline SHALL be a Python script at `fake-news-api/scripts/retrain.py`
2. THE script SHALL accept arguments: `--model` (distilbert/roberta/xlnet), `--feedback-csv` (path to exported CSV), `--epochs` (default 3), `--output-dir`
3. THE script SHALL load the feedback CSV, merge it with a sample of the original training data (to prevent catastrophic forgetting), and fine-tune the specified model
4. THE script SHALL evaluate the retrained model on a held-out validation set and print accuracy metrics before saving
5. WHEN the retrained model's accuracy is lower than the original by more than 2%, THE script SHALL abort and print a warning instead of saving
6. THE script SHALL save the retrained model weights to the specified output directory in HuggingFace safetensors format
7. THE script SHALL log training loss, validation accuracy, and per-class F1 scores to a `retrain_log.json` file

---

## Requirement 8: Confidence Calibration Display

**User Story:** As a user, I want to understand how reliable a confidence score is, so that I can better interpret prediction results.

### Acceptance Criteria

1. THE Frontend_App SHALL display a calibration indicator alongside the confidence score on ResultCard
2. WHEN confidence is >= 90%, THE Frontend_App SHALL display "High confidence" in green
3. WHEN confidence is between 65% and 89%, THE Frontend_App SHALL display "Moderate confidence" in amber
4. WHEN confidence is below 65%, THE Frontend_App SHALL display "Low confidence — treat with caution" in red
5. THE Frontend_App SHALL display a tooltip explaining what confidence means: "Probability the model assigns to this classification"
6. THE ResultCard SHALL display the top 3 alternative labels with their probabilities in a collapsible section
7. FOR ALL predictions, the displayed confidence SHALL match the model's raw softmax output for the predicted class (no rounding beyond 1 decimal place)

---

## Requirement 9: Result Sharing

**User Story:** As a user, I want to share a prediction result, so that I can show others what the system found about an article.

### Acceptance Criteria

1. THE Frontend_App SHALL add a "Share" button to the ResultCard component
2. WHEN a user clicks "Share", THE Frontend_App SHALL copy a shareable text to the clipboard in the format: "VeracityLens analyzed this article as [LABEL] with [X]% confidence. Check it at https://veracitylens.vercel.app"
3. WHEN clipboard copy succeeds, THE Frontend_App SHALL display a "Copied to clipboard!" toast notification for 2 seconds
4. WHEN clipboard API is unavailable, THE Frontend_App SHALL display the share text in a modal for manual copying
5. THE Frontend_App SHALL add a "Download Report" button that exports the prediction result as a plain text `.txt` file
6. THE downloaded report SHALL include: article text preview, predicted label, confidence, all voting strategy results (for ensemble), individual model results, and timestamp

---

## Requirement 10: Free Tier Constraints

**User Story:** As a developer, I want all Phase 2 features to stay within free-tier limits, so that the project remains cost-free.

### Acceptance Criteria

1. THE URL_Analyzer SHALL use `requests` with a 10-second timeout — no headless browser or paid scraping service
2. THE Article_Extractor SHALL use `newspaper3k` or `beautifulsoup4` (already in requirements.txt) — no paid APIs
3. THE AnalyticsPage charts SHALL use a lightweight charting library (Recharts, already available via npm) — no paid visualization services
4. THE Retraining_Pipeline SHALL run locally or on a free Colab instance — not on HF Spaces (insufficient CPU for training)
5. THE `/feedback/export` endpoint SHALL be rate-limited to 10 requests per hour to prevent abuse
6. THE Backend_API SHALL cache the `/stats` response for 60 seconds to reduce Supabase query load

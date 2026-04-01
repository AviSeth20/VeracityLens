# Requirements Document

## Introduction

This document specifies the requirements for Phase 1 enhancements to the VeracityLens fake news detection system. The enhancements include an ensemble model combining all three transformer models with voting mechanisms, a user analysis history feature to track predictions, and a dark mode theme toggle. All features must operate within existing free-tier infrastructure constraints.

## Glossary

- **Ensemble_Model**: A meta-classifier that combines predictions from DistilBERT, RoBERTa, and XLNet models using voting strategies
- **Hard_Voting**: A voting strategy where the final prediction is the class with the most votes from individual models
- **Soft_Voting**: A voting strategy where the final prediction is based on averaged probability scores across models
- **Weighted_Voting**: A voting strategy where each model's vote is multiplied by its accuracy weight before aggregation
- **Analysis_History**: A persistent record of user predictions stored in Supabase, linked to browser sessions
- **Session_Tracker**: A browser-based identifier (localStorage) that associates predictions with anonymous users
- **Dark_Mode**: An alternative color scheme optimized for low-light viewing using Tailwind CSS dark classes
- **Theme_Context**: A React Context provider that manages theme state across the application
- **Backend_API**: The FastAPI service running on HuggingFace Spaces
- **Frontend_App**: The React application deployed on Vercel
- **Supabase_Client**: The PostgreSQL database client for storing predictions and history
- **HF_Space**: HuggingFace Spaces free tier deployment environment (2 CPU cores, no GPU)

## Requirements

### Requirement 1: Ensemble Model Inference

**User Story:** As a user, I want the system to combine predictions from all three models, so that I can get more accurate and robust fake news detection results.

#### Acceptance Criteria

1. WHEN a user selects "ensemble" as the model option, THE Ensemble_Model SHALL invoke all three models (DistilBERT, RoBERTa, XLNet) in parallel
2. THE Ensemble_Model SHALL complete inference for all three models within 10 seconds on HF_Space
3. WHEN all three models return predictions, THE Ensemble_Model SHALL compute hard voting, soft voting, and weighted voting results
4. THE Ensemble_Model SHALL return the hard voting result as the primary prediction label
5. THE Ensemble_Model SHALL include all three voting strategy results in the API response
6. THE Ensemble_Model SHALL include individual model predictions and confidence scores in the response
7. WHEN any individual model fails, THE Ensemble_Model SHALL return predictions from the remaining models and log the failure
8. THE Ensemble_Model SHALL use accuracy-based weights (DistilBERT: 0.859, RoBERTa: 0.858, XLNet: 0.862) for weighted voting
9. FOR ALL valid text inputs, running ensemble prediction twice SHALL produce identical results (deterministic property)
10. FOR ALL valid text inputs, the ensemble confidence score SHALL be between 0.0 and 1.0 (invariant property)

### Requirement 2: Ensemble Model API Endpoint

**User Story:** As a frontend developer, I want a dedicated ensemble endpoint, so that I can easily integrate ensemble predictions into the UI.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a POST endpoint at `/predict/ensemble`
2. WHEN the `/predict/ensemble` endpoint receives a valid text input, THE Backend_API SHALL return predictions from all three models
3. THE Backend_API SHALL return a JSON response containing hard_voting, soft_voting, and weighted_voting results
4. THE Backend_API SHALL return individual model predictions with labels, confidence scores, and token explanations
5. WHEN the request text is shorter than 10 characters, THE Backend_API SHALL return HTTP 422 with error message "Text too short to classify"
6. WHEN any model inference fails, THE Backend_API SHALL return partial results with a warning field indicating which models failed
7. THE Backend_API SHALL store ensemble predictions in Supabase with model_name set to "ensemble"
8. THE Backend_API SHALL complete the request within 15 seconds or return HTTP 504 timeout error

### Requirement 3: Ensemble Model Frontend Integration

**User Story:** As a user, I want to select "Ensemble" from the model dropdown, so that I can use the combined predictions from all models.

#### Acceptance Criteria

1. THE Frontend_App SHALL add "Ensemble" as an option in the ModelSelector component
2. WHEN a user selects "Ensemble", THE Frontend_App SHALL display "Ensemble (All 3 Models)" as the selected model
3. WHEN a user clicks "Analyze" with Ensemble selected, THE Frontend_App SHALL call the `/predict/ensemble` endpoint
4. THE Frontend_App SHALL display the hard voting result as the primary prediction in the ResultCard
5. THE Frontend_App SHALL display individual model predictions in an expandable section showing all three model results
6. THE Frontend_App SHALL display voting strategy comparison showing hard, soft, and weighted voting results
7. WHEN ensemble prediction is loading, THE Frontend_App SHALL display "Running 3 models..." in the loading skeleton
8. THE Frontend_App SHALL display token explanations merged from all three models, sorted by average importance score

### Requirement 4: User Analysis History Database Schema

**User Story:** As a system administrator, I want to store user predictions with session tracking, so that users can view their analysis history.

#### Acceptance Criteria

1. THE Supabase_Client SHALL create a table named `user_analysis_history` with columns: id, session_id, article_id, text_preview, predicted_label, confidence, model_name, created_at
2. THE Supabase_Client SHALL create an index on `user_analysis_history(session_id, created_at DESC)`
3. THE Supabase_Client SHALL enable row-level security on `user_analysis_history` with a policy allowing all operations
4. WHEN a prediction is stored, THE Backend_API SHALL save the session_id from the request header `X-Session-ID`
5. THE Backend_API SHALL truncate text_preview to 200 characters before storing
6. THE Backend_API SHALL store the prediction in both `predictions` and `user_analysis_history` tables
7. FOR ALL stored records, the session_id field SHALL NOT be null (invariant property)
8. FOR ALL stored records, the created_at timestamp SHALL be less than or equal to the current time (invariant property)

### Requirement 5: Session Tracking in Frontend

**User Story:** As a user, I want my predictions to be tracked across browser sessions, so that I can view my analysis history even after closing the browser.

#### Acceptance Criteria

1. WHEN the Frontend_App loads for the first time, THE Session_Tracker SHALL generate a unique session ID using UUID v4
2. THE Session_Tracker SHALL store the session ID in browser localStorage under the key `veracitylens_session_id`
3. WHEN the Frontend_App makes a prediction request, THE Session_Tracker SHALL include the session ID in the `X-Session-ID` header
4. THE Session_Tracker SHALL retrieve the existing session ID from localStorage on subsequent visits
5. WHEN localStorage is unavailable, THE Session_Tracker SHALL generate a new session ID for the current browser session only
6. FOR ALL prediction requests, the `X-Session-ID` header SHALL be present (invariant property)
7. FOR ALL session IDs, generating a new ID then storing and retrieving it SHALL return the same ID (round-trip property)

### Requirement 6: User History API Endpoint

**User Story:** As a user, I want to retrieve my past predictions, so that I can review articles I've previously analyzed.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint at `/history/{session_id}`
2. WHEN the endpoint receives a valid session_id, THE Backend_API SHALL return all predictions for that session ordered by created_at DESC
3. THE Backend_API SHALL limit results to 100 most recent predictions per session
4. THE Backend_API SHALL return predictions with fields: article_id, text_preview, predicted_label, confidence, model_name, created_at
5. WHEN the session_id has no predictions, THE Backend_API SHALL return an empty array with HTTP 200
6. WHEN the session_id format is invalid, THE Backend_API SHALL return HTTP 400 with error message "Invalid session ID format"
7. THE Backend_API SHALL complete the request within 2 seconds or return HTTP 504 timeout error
8. FOR ALL valid session IDs, calling the endpoint twice SHALL return the same results if no new predictions were made (idempotence property)

### Requirement 7: User History Frontend Component

**User Story:** As a user, I want to view my analysis history in the UI, so that I can quickly access and review my past predictions.

#### Acceptance Criteria

1. THE Frontend_App SHALL add a "History" navigation link in the Header component
2. WHEN a user clicks "History", THE Frontend_App SHALL navigate to `/history` route
3. THE Frontend_App SHALL create a HistoryPage component that displays the user's prediction history
4. WHEN the HistoryPage loads, THE Frontend_App SHALL fetch predictions using the current session ID
5. THE Frontend_App SHALL display each prediction as a card showing text_preview, predicted_label, confidence, model_name, and created_at
6. THE Frontend_App SHALL display predictions in reverse chronological order (newest first)
7. WHEN a user clicks on a history item, THE Frontend_App SHALL navigate to the home page and pre-fill the text input with the full article text
8. WHEN the history is empty, THE Frontend_App SHALL display "No analysis history yet. Start analyzing news articles to build your history."
9. THE Frontend_App SHALL display a loading skeleton while fetching history data
10. WHEN the API request fails, THE Frontend_App SHALL display an error message "Failed to load history. Please try again."

### Requirement 8: Dark Mode Theme System

**User Story:** As a user, I want to toggle between light and dark themes, so that I can use the application comfortably in different lighting conditions.

#### Acceptance Criteria

1. THE Frontend_App SHALL create a ThemeContext provider that manages theme state (light or dark)
2. THE Theme_Context SHALL store the current theme in localStorage under the key `veracitylens_theme`
3. WHEN the Frontend_App loads, THE Theme_Context SHALL retrieve the saved theme from localStorage or default to "light"
4. WHEN the user's system preference is dark mode and no saved theme exists, THE Theme_Context SHALL default to "dark"
5. THE Theme_Context SHALL provide a toggleTheme function that switches between light and dark modes
6. WHEN the theme changes, THE Theme_Context SHALL update localStorage and apply the theme to the document root
7. THE Frontend_App SHALL apply the "dark" class to the document root element when dark mode is active
8. FOR ALL theme changes, toggling twice SHALL return to the original theme (idempotence property)
9. FOR ALL theme values, saving to localStorage then retrieving SHALL return the same value (round-trip property)

### Requirement 9: Dark Mode UI Styling

**User Story:** As a user, I want all UI components to adapt to dark mode, so that I have a consistent and comfortable viewing experience.

#### Acceptance Criteria

1. THE Frontend_App SHALL apply dark mode styles to all components using Tailwind CSS `dark:` classes
2. WHEN dark mode is active, THE Frontend_App SHALL use background color `#1a1a1a` for the main background
3. WHEN dark mode is active, THE Frontend_App SHALL use text color `#f5f5f5` for primary text
4. WHEN dark mode is active, THE Frontend_App SHALL use background color `#2a2a2a` for card components
5. WHEN dark mode is active, THE Frontend_App SHALL use border color `#3a3a3a` for borders and dividers
6. WHEN dark mode is active, THE Frontend_App SHALL maintain the brand color `#d97757` for accent elements
7. THE Frontend_App SHALL ensure all text has sufficient contrast ratio (WCAG AA: 4.5:1 for normal text, 3:1 for large text)
8. THE Frontend_App SHALL apply smooth transitions (200ms) when switching between light and dark modes
9. WHEN dark mode is active, THE Frontend_App SHALL invert the color scheme for charts and visualizations while maintaining readability

### Requirement 10: Dark Mode Toggle Control

**User Story:** As a user, I want a visible toggle button to switch between light and dark modes, so that I can easily change the theme.

#### Acceptance Criteria

1. THE Frontend_App SHALL add a theme toggle button in the Header component
2. THE Frontend_App SHALL display a moon icon when light mode is active
3. THE Frontend_App SHALL display a sun icon when dark mode is active
4. WHEN a user clicks the toggle button, THE Frontend_App SHALL switch to the opposite theme
5. THE Frontend_App SHALL animate the icon transition with a 300ms rotation effect
6. THE Frontend_App SHALL display a tooltip "Switch to dark mode" when hovering over the button in light mode
7. THE Frontend_App SHALL display a tooltip "Switch to light mode" when hovering over the button in dark mode
8. THE Frontend_App SHALL ensure the toggle button is accessible via keyboard (Tab navigation and Enter/Space activation)
9. THE Frontend_App SHALL announce theme changes to screen readers using aria-live regions

### Requirement 11: Free Tier Resource Constraints

**User Story:** As a system administrator, I want all Phase 1 features to operate within free tier limits, so that the project remains bootstrapped and cost-free.

#### Acceptance Criteria

1. THE Ensemble_Model SHALL run on HF_Space without requiring GPU resources
2. THE Backend_API SHALL complete ensemble predictions within the 60-second HuggingFace Spaces request timeout
3. THE Supabase_Client SHALL store user_analysis_history within the 500MB free tier storage limit
4. THE Supabase_Client SHALL execute history queries within the free tier rate limits (no more than 100 requests per minute per session)
5. THE Frontend_App SHALL store session IDs and theme preferences in localStorage without requiring external storage services
6. THE Backend_API SHALL use connection pooling to stay within Supabase's 60 concurrent connection limit
7. WHEN the Supabase storage approaches 450MB (90% of limit), THE Backend_API SHALL log a warning
8. THE Backend_API SHALL implement request throttling to prevent exceeding HuggingFace Spaces rate limits

### Requirement 12: Ensemble Model Voting Strategy Correctness

**User Story:** As a developer, I want to verify that voting strategies produce mathematically correct results, so that ensemble predictions are reliable.

#### Acceptance Criteria

1. FOR ALL valid inputs, THE Ensemble_Model SHALL ensure hard voting selects the label with the maximum vote count
2. FOR ALL valid inputs, THE Ensemble_Model SHALL ensure soft voting averages probability scores across all models before selecting the maximum
3. FOR ALL valid inputs, THE Ensemble_Model SHALL ensure weighted voting applies accuracy weights (0.859, 0.858, 0.862) before averaging
4. FOR ALL valid inputs, THE Ensemble_Model SHALL ensure the sum of weighted voting probabilities for all classes equals 1.0 (within 0.001 tolerance)
5. WHEN all three models predict the same label, THE Ensemble_Model SHALL return that label with confidence equal to the average of individual confidences
6. WHEN models disagree, THE Ensemble_Model SHALL return the hard voting result as the primary prediction
7. FOR ALL valid inputs, the ensemble confidence SHALL be greater than or equal to the minimum individual model confidence (metamorphic property)
8. FOR ALL valid inputs, if two models agree and one disagrees, hard voting SHALL return the majority label (confluence property)

### Requirement 13: History Data Integrity

**User Story:** As a developer, I want to ensure history data remains consistent and accurate, so that users can trust their analysis records.

#### Acceptance Criteria

1. FOR ALL stored predictions, THE Backend_API SHALL ensure article_id is unique within the user_analysis_history table
2. FOR ALL stored predictions, THE Backend_API SHALL ensure predicted_label is one of: "True", "Fake", "Satire", "Bias"
3. FOR ALL stored predictions, THE Backend_API SHALL ensure confidence is between 0.0 and 1.0 inclusive
4. FOR ALL stored predictions, THE Backend_API SHALL ensure text_preview length is less than or equal to 200 characters
5. WHEN a prediction is stored, THE Backend_API SHALL verify the session_id matches UUID v4 format
6. WHEN retrieving history, THE Backend_API SHALL return predictions in descending order by created_at (newest first)
7. FOR ALL history queries, filtering by session_id then counting results SHALL return a value less than or equal to 100 (metamorphic property)
8. FOR ALL valid session IDs, storing a prediction then immediately retrieving history SHALL include that prediction (round-trip property)

### Requirement 14: Error Handling and Resilience

**User Story:** As a user, I want the system to handle errors gracefully, so that I receive helpful feedback when something goes wrong.

#### Acceptance Criteria

1. WHEN any individual model in the ensemble fails, THE Ensemble_Model SHALL continue with remaining models and return partial results
2. WHEN all three models fail, THE Backend_API SHALL return HTTP 500 with error message "All models failed to process the request"
3. WHEN the Supabase connection fails during history storage, THE Backend_API SHALL log the error but still return the prediction result
4. WHEN the Supabase connection fails during history retrieval, THE Backend_API SHALL return HTTP 503 with error message "History service temporarily unavailable"
5. WHEN localStorage is unavailable in the browser, THE Frontend_App SHALL generate a session ID for the current session only and display a warning
6. WHEN the theme toggle fails, THE Frontend_App SHALL revert to the previous theme and display an error toast
7. WHEN the history API returns an error, THE Frontend_App SHALL display a user-friendly error message and provide a retry button
8. THE Backend_API SHALL implement exponential backoff for Supabase connection retries (max 3 attempts)

### Requirement 15: Performance Optimization

**User Story:** As a user, I want fast response times for all features, so that I can analyze news efficiently.

#### Acceptance Criteria

1. THE Ensemble_Model SHALL execute all three model inferences in parallel using asyncio or threading
2. THE Backend_API SHALL cache model instances in memory to avoid reloading on each request
3. THE Backend_API SHALL use database connection pooling with a minimum of 2 and maximum of 10 connections
4. THE Frontend_App SHALL implement lazy loading for the HistoryPage component to reduce initial bundle size
5. THE Frontend_App SHALL debounce theme toggle clicks to prevent rapid state changes (300ms debounce)
6. THE Frontend_App SHALL use React.memo for ResultCard and HistoryCard components to prevent unnecessary re-renders
7. WHEN fetching history, THE Backend_API SHALL use indexed queries on (session_id, created_at DESC) for optimal performance
8. THE Backend_API SHALL return history results within 500ms for sessions with up to 100 predictions

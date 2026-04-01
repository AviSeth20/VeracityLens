# Implementation Plan: Phase 1 Enhancements

## Overview

This implementation plan covers three major features for the VeracityLens fake news detection system:

1. **Ensemble Model**: Parallel inference combining DistilBERT, RoBERTa, and XLNet with multiple voting strategies
2. **User Analysis History**: Session-based tracking and persistent storage of predictions
3. **Dark Mode**: Complete theme system with light/dark toggle

All features operate within free-tier infrastructure constraints (HuggingFace Spaces CPU-only, Supabase 500MB limit, Vercel free tier).

## Tasks

- [x] 1. Phase 1: Ensemble Model Backend Implementation
  - [x] 1.1 Create ensemble classifier with parallel execution
    - Create `fake-news-api/src/models/ensemble.py` with `EnsembleClassifier` class
    - Implement `predict_ensemble()` method using `asyncio.gather()` for parallel model execution
    - Implement `EnsembleResult` and `ModelPrediction` dataclasses
    - Add timeout handling (10s per model, 15s total)
    - Add error handling for partial model failures
    - _Requirements: 1.1, 1.2, 1.7, 14.1_

  - [x] 1.2 Write property test for ensemble parallel execution
    - **Property 1: Ensemble Parallel Execution**
    - **Validates: Requirements 1.1, 1.3**

  - [x] 1.3 Implement voting strategies
    - Implement `hard_voting()` method (select label with most votes)
    - Implement `soft_voting()` method (average probability scores)
    - Implement `weighted_voting()` method (apply accuracy weights: 0.859, 0.858, 0.862)
    - Implement token explanation merging sorted by average importance
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.8, 12.1, 12.2, 12.3_

  - [x] 1.4 Write property tests for voting strategy correctness
    - **Property 4: Voting Strategy Correctness**
    - **Property 5: Probability Sum Invariant**
    - **Property 22: Majority Voting Correctness**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.8, 1.8**

  - [x] 1.5 Write property test for ensemble determinism
    - **Property 6: Ensemble Determinism**
    - **Validates: Requirements 1.9**

- [x] 2. Phase 1: Ensemble Model API Endpoint
  - [x] 2.1 Create ensemble API endpoint and schemas
    - Add `EnsemblePredictionRequest` and `EnsemblePredictionResponse` models to `fake-news-api/src/api/main.py`
    - Add `VotingStrategies` and `VotingResult` models
    - Implement POST `/predict/ensemble` endpoint
    - Extract session_id from `X-Session-ID` header
    - Add input validation (text length >= 10 characters)
    - Add timeout handling (return HTTP 504 after 15s)
    - _Requirements: 2.1, 2.2, 2.5, 2.8_

  - [x] 2.2 Integrate ensemble endpoint with storage
    - Create `store_ensemble_prediction()` background task
    - Store prediction in both `predictions` and `user_analysis_history` tables
    - Handle database connection failures gracefully (log but still return prediction)
    - Return warnings array when models fail
    - _Requirements: 2.3, 2.4, 2.6, 2.7, 14.3_

  - [x] 2.3 Write property tests for ensemble response completeness
    - **Property 2: Ensemble Response Completeness**
    - **Property 3: Hard Voting as Primary Prediction**
    - **Property 21: Ensemble Endpoint Behavior**
    - **Validates: Requirements 1.5, 1.6, 2.3, 2.4, 3.4, 3.5, 3.6**

  - [x] 2.4 Write unit tests for ensemble endpoint
    - Test valid request returns HTTP 200 with complete response
    - Test text < 10 characters returns HTTP 422
    - Test all models fail returns HTTP 500
    - Test partial model failures return warnings
    - _Requirements: 2.5, 14.2_

- [x] 3. Checkpoint - Ensemble backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Phase 1: Ensemble Model Frontend Integration
  - [x] 4.1 Add ensemble option to model selector
    - Update `frontend/src/components/ModelSelector.jsx` MODELS array
    - Add ensemble option: `{ id: "ensemble", label: "Ensemble", desc: "All 3 Models · Most Accurate", badge: "Best" }`
    - _Requirements: 3.1, 3.2_

  - [x] 4.2 Create ensemble API client function
    - Add `analyzeEnsemble(text)` function to `frontend/src/services/api.js`
    - Update API client to call `/predict/ensemble` endpoint
    - _Requirements: 3.3_

  - [x] 4.3 Update App component for ensemble support
    - Update `frontend/src/App.jsx` to handle "ensemble" model selection
    - Call `analyzeEnsemble()` when ensemble is selected
    - Update loading message to "Running 3 models..." for ensemble
    - _Requirements: 3.3, 3.7_

  - [x] 4.4 Create ensemble result display components
    - Update `frontend/src/components/ResultCard.jsx` with `EnsembleResultView` component
    - Create `VotingStrategyCard` component for voting comparison
    - Create `ModelPredictionCard` component for individual model results
    - Display hard voting as primary prediction
    - Add expandable section for voting strategies comparison
    - Display individual model predictions with confidence scores
    - Display merged token explanations sorted by importance
    - _Requirements: 3.4, 3.5, 3.6, 3.8_

  - [x] 4.5 Write unit tests for ensemble frontend components
    - Test ModelSelector shows ensemble option
    - Test App calls correct endpoint for ensemble
    - Test ResultCard displays ensemble results correctly
    - Test voting strategies expandable section
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Phase 2: User Analysis History Database Setup
  - [x] 5.1 Create user_analysis_history table
    - Update `fake-news-api/scripts/setup_supabase.sql` with new table definition
    - Add columns: id, session_id, article_id, text_preview, predicted_label, confidence, model_name, created_at
    - Add CHECK constraints for predicted_label and confidence
    - Add UNIQUE constraint on article_id
    - Add foreign key to predictions table
    - Create index on (session_id, created_at DESC)
    - Enable row-level security with allow_all policy
    - _Requirements: 4.1, 4.2, 4.3, 4.7, 4.8_

  - [x] 5.2 Run database migration
    - Execute SQL migration script on Supabase
    - Verify table creation and indexes
    - Test with sample data insertion
    - _Requirements: 4.1_

  - [x] 5.3 Write property tests for history data integrity
    - **Property 13: History Data Integrity**
    - **Property 23: Article ID Uniqueness**
    - **Validates: Requirements 4.7, 4.8, 13.1, 13.2, 13.3, 13.4, 13.5**

- [x] 6. Phase 2: User History Backend Implementation
  - [x] 6.1 Add history storage methods to Supabase client
    - Update `fake-news-api/src/utils/supabase_client.py` with `store_user_history()` method
    - Implement text preview truncation to 200 characters
    - Validate session_id UUID v4 format
    - Add `get_user_history()` method with limit parameter (default 100)
    - Order results by created_at DESC
    - _Requirements: 4.5, 4.6, 6.2, 6.3_

  - [x] 6.2 Update prediction endpoints to store history
    - Update all prediction endpoints in `fake-news-api/src/api/main.py` to extract session_id from headers
    - Add background task to store predictions in user_analysis_history table
    - Handle missing session_id gracefully
    - _Requirements: 4.4, 4.6, 2.7_

  - [x] 6.3 Write property tests for text preview truncation
    - **Property 12: Text Preview Truncation**
    - **Validates: Requirements 4.5, 13.4**

  - [x] 6.4 Write property test for dual table storage
    - **Property 11: Dual Table Storage**
    - **Validates: Requirements 2.7, 4.6**

- [x] 7. Phase 2: User History API Endpoint
  - [x] 7.1 Create history retrieval endpoint
    - Add GET `/history/{session_id}` endpoint to `fake-news-api/src/api/main.py`
    - Validate session_id UUID format (return HTTP 400 if invalid)
    - Add limit query parameter (1-100, default 100)
    - Return empty array with HTTP 200 for sessions with no history
    - Add timeout handling (return HTTP 504 after 2s)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x] 7.2 Write property tests for history retrieval
    - **Property 14: History Ordering**
    - **Property 15: History Result Limit**
    - **Property 16: History Query Idempotence**
    - **Property 17: History Round-Trip**
    - **Validates: Requirements 6.2, 6.3, 6.8, 13.6, 13.7, 13.8**

  - [x] 7.3 Write unit tests for history endpoint
    - Test valid session_id returns HTTP 200
    - Test invalid session_id format returns HTTP 400
    - Test empty history returns empty array
    - Test limit parameter works correctly
    - _Requirements: 6.1, 6.5, 6.6_

- [x] 8. Checkpoint - History backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Phase 2: Session Tracking Frontend Implementation
  - [x] 9.1 Create session tracker utility
    - Create `frontend/src/utils/sessionTracker.js` with `SessionTracker` class
    - Implement `initializeSession()` to generate or retrieve UUID v4
    - Store session_id in localStorage under key `veracitylens_session_id`
    - Handle localStorage unavailable (fall back to in-memory session)
    - Implement `getSessionId()` and `resetSession()` methods
    - Export singleton instance
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

  - [x] 9.2 Add session ID to API requests
    - Update `frontend/src/services/api.js` request interceptor
    - Add `X-Session-ID` header with session ID from sessionTracker
    - _Requirements: 5.3, 5.6_

  - [x] 9.3 Write property tests for session tracking
    - **Property 9: Session ID Header Presence**
    - **Property 10: Session ID Round-Trip**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.6, 5.7**

  - [x] 9.4 Write unit tests for session tracker
    - Test session ID generation creates valid UUID v4
    - Test session ID persists to localStorage
    - Test session ID retrieval from localStorage
    - Test localStorage unavailable fallback
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 14.5_

- [x] 10. Phase 2: User History Frontend Components
  - [x] 10.1 Create history page component
    - Create `frontend/src/pages/HistoryPage.jsx` component
    - Implement `loadHistory()` to fetch predictions using session ID
    - Display loading skeleton while fetching
    - Display error message with retry button on failure
    - Display empty state when no history exists
    - Display history items as cards in reverse chronological order
    - _Requirements: 7.3, 7.4, 7.5, 7.6, 7.8, 7.9, 7.10_

  - [x] 10.2 Create history card component
    - Create `HistoryCard` component in `HistoryPage.jsx`
    - Display text_preview, predicted_label, confidence, model_name, created_at
    - Add click handler to navigate to home with pre-filled text
    - Style with appropriate colors based on prediction label
    - Add hover animation
    - _Requirements: 7.5, 7.7_

  - [x] 10.3 Add history navigation to header
    - Update `frontend/src/components/Header.jsx` to add "History" link
    - Add navigation to `/history` route
    - _Requirements: 7.1, 7.2_

  - [x] 10.4 Add history route to app
    - Update `frontend/src/main.jsx` to add `/history` route
    - Configure route to render HistoryPage component
    - _Requirements: 7.2_

  - [x] 10.5 Add getUserHistory API function
    - Add `getUserHistory(sessionId, limit)` function to `frontend/src/services/api.js`
    - Call GET `/history/{session_id}` endpoint
    - _Requirements: 6.1_

  - [x] 10.6 Write property test for history fetch on page load
    - **Property 25: History Fetch on Page Load**
    - **Validates: Requirements 7.4, 7.5**

  - [x] 10.7 Write unit tests for history page
    - Test loading state displays skeleton
    - Test error state displays error message and retry button
    - Test empty state displays helpful message
    - Test history items display correctly
    - Test clicking history item navigates to home
    - _Requirements: 7.3, 7.5, 7.7, 7.8, 7.9, 7.10_

- [x] 11. Phase 3: Dark Mode Theme Context
  - [x] 11.1 Create theme context provider
    - Create `frontend/src/contexts/ThemeContext.jsx` with `ThemeProvider` component
    - Implement theme state management (light/dark)
    - Store theme in localStorage under key `veracitylens_theme`
    - Retrieve saved theme on initialization or default to system preference
    - Implement `toggleTheme()` function
    - Apply "dark" class to document root when dark mode active
    - Export `useTheme()` hook
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 11.2 Write property tests for theme operations
    - **Property 18: Theme Toggle Idempotence**
    - **Property 19: Theme Persistence Round-Trip**
    - **Property 20: Dark Mode Class Application**
    - **Validates: Requirements 8.2, 8.6, 8.7, 8.8, 8.9**

  - [x] 11.3 Write unit tests for theme context
    - Test theme initializes from localStorage
    - Test theme defaults to system preference when no saved theme
    - Test toggleTheme switches between light and dark
    - Test theme persists to localStorage
    - Test dark class applied to document root
    - Test localStorage unavailable fallback
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 14.6_

- [x] 12. Phase 3: Dark Mode UI Implementation
  - [x] 12.1 Wrap app with ThemeProvider
    - Update `frontend/src/main.jsx` to wrap app with `ThemeProvider`
    - _Requirements: 8.1_

  - [x] 12.2 Add theme toggle button to header
    - Update `frontend/src/components/Header.jsx` with theme toggle button
    - Display moon icon in light mode, sun icon in dark mode
    - Add click handler to call `toggleTheme()`
    - Add 300ms rotation animation on toggle
    - Add tooltips for accessibility
    - Add keyboard navigation support (Tab, Enter, Space)
    - Add aria-live region for screen reader announcements
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [x] 12.3 Write unit tests for theme toggle button
    - Test button displays correct icon for current theme
    - Test clicking button toggles theme
    - Test keyboard navigation works
    - Test tooltips display correctly
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.8_

- [x] 13. Phase 3: Dark Mode Styling
  - [x] 13.1 Update Tailwind configuration
    - Update `frontend/tailwind.config.js` to enable class-based dark mode
    - Add `darkMode: "class"` configuration
    - _Requirements: 9.1_

  - [x] 13.2 Add dark mode styles to App component
    - Update `frontend/src/App.jsx` with dark mode background colors
    - Add `dark:bg-[#1a1a1a]` to main background
    - Add `dark:text-[#f5f5f5]` to primary text
    - Add smooth transitions (200ms)
    - _Requirements: 9.1, 9.2, 9.3, 9.8_

  - [x] 13.3 Add dark mode styles to Header and Footer
    - Update `frontend/src/components/Header.jsx` with dark mode styles
    - Update `frontend/src/components/Footer.jsx` with dark mode styles
    - Use `dark:bg-[#2a2a2a]` for header/footer background
    - Use `dark:text-[#f5f5f5]` for text
    - Use `dark:border-[#3a3a3a]` for borders
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.8_

  - [x] 13.4 Add dark mode styles to input and card components
    - Update `frontend/src/components/AnalysisInput.jsx` with dark mode styles
    - Update `frontend/src/components/ResultCard.jsx` with dark mode styles
    - Update `frontend/src/components/ModelSelector.jsx` with dark mode styles
    - Use `dark:bg-[#2a2a2a]` for card backgrounds
    - Use `dark:border-[#3a3a3a]` for borders
    - Ensure accent color `#d97757` remains unchanged
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8_

  - [x] 13.5 Add dark mode styles to remaining components
    - Update `frontend/src/components/StatsBar.jsx` with dark mode styles
    - Update `frontend/src/components/LiveNewsFeed.jsx` with dark mode styles
    - Update `frontend/src/components/LoadingSkeleton.jsx` with dark mode colors
    - Update `frontend/src/pages/HistoryPage.jsx` with dark mode styles
    - Ensure all text meets WCAG AA contrast ratios (4.5:1 normal, 3:1 large)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.7, 9.8_

  - [x] 13.6 Add dark mode styles to global CSS
    - Update `frontend/src/index.css` with dark mode CSS variables
    - Add transition styles for smooth theme switching
    - _Requirements: 9.8_

  - [x] 13.7 Write visual regression tests for dark mode
    - Test all components render correctly in dark mode
    - Test contrast ratios meet WCAG AA standards
    - Test transitions are smooth
    - _Requirements: 9.7, 9.8_

- [x] 14. Checkpoint - Dark mode complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Phase 4: Integration and Optimization
  - [x] 15.1 Add performance optimizations
    - Add React.memo to `ResultCard` component
    - Add React.memo to `HistoryCard` component
    - Add lazy loading for `HistoryPage` component
    - Add debounce to theme toggle (300ms)
    - Optimize database queries with connection pooling (2-10 connections)
    - _Requirements: 15.1, 15.3, 15.4, 15.5, 15.6_

  - [x] 15.2 Add comprehensive error handling
    - Add React Error Boundary to catch rendering errors
    - Add exponential backoff for Supabase retries (max 3 attempts)
    - Improve error messages for all failure scenarios
    - Add retry logic for transient failures
    - Add logging for all errors
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

  - [x] 15.3 Add resource monitoring
    - Add logging for ensemble execution time
    - Add logging for database storage usage
    - Add warning when Supabase storage approaches 450MB (90% of 500MB limit)
    - Add request throttling to prevent rate limit violations
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.7, 11.8_

  - [x] 15.4 Write integration tests
    - Test end-to-end ensemble prediction flow
    - Test end-to-end history storage and retrieval flow
    - Test theme persistence across page reloads
    - Test session tracking across multiple predictions
    - _Requirements: All requirements_

  - [x] 15.5 Run all property tests with 100 iterations
    - Verify all 25 properties pass with 100 iterations
    - Fix any failures discovered
    - _Requirements: All requirements_

- [x] 16. Final checkpoint - All features complete
  - Ensure all tests pass, verify test coverage meets goals (85%+ backend, 80%+ frontend), ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties (25 total)
- Unit tests validate specific examples and edge cases
- Backend uses Python with FastAPI, frontend uses React with JavaScript
- All features must operate within free-tier constraints (HF Spaces CPU-only, Supabase 500MB, Vercel free tier)

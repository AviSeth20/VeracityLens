import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import * as api from './services/api'

/**
 * Unit tests for App component ensemble integration
 * 
 * **Validates: Requirements 3.2, 3.3**
 * 
 * Tests:
 * - App calls analyzeEnsemble when ensemble model is selected
 * - App calls analyzeNews for individual models
 * - App displays loading message for ensemble predictions
 * - App displays ensemble results correctly
 */

// Mock the API module
vi.mock('./services/api', () => ({
  analyzeNews: vi.fn(),
  analyzeEnsemble: vi.fn(),
  getStats: vi.fn(),
}))

// Mock child components to avoid rendering issues in tests
vi.mock('./components/Header', () => ({
  default: () => <div data-testid="mock-header">Header</div>,
}))

vi.mock('./components/Footer', () => ({
  default: () => <div data-testid="mock-footer">Footer</div>,
}))

vi.mock('./components/StatsBar', () => ({
  default: () => <div data-testid="mock-stats">Stats</div>,
}))

vi.mock('./components/LiveNewsFeed', () => ({
  default: () => <div data-testid="mock-news-feed">News Feed</div>,
}))

vi.mock('./components/AnalysisInput', () => ({
  default: ({ value, onChange, onAnalyze, onClear, isLoading }) => (
    <div data-testid="mock-analysis-input">
      <textarea
        placeholder="Paste article text here..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      <button onClick={onAnalyze} disabled={isLoading}>
        {isLoading ? 'Analyzing...' : 'Analyze'}
      </button>
      <button onClick={onClear}>Clear</button>
    </div>
  ),
}))

vi.mock('./components/LoadingSkeleton', () => ({
  default: ({ message }) => (
    <div data-testid="mock-loading">{message || 'Loading...'}</div>
  ),
}))

vi.mock('./components/ResultCard', () => ({
  default: ({ result }) => (
    <div data-testid="mock-result-card">
      Result: {result.label || result.primary_prediction?.label}
    </div>
  ),
}))

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}))

describe('App - Ensemble Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getStats.mockResolvedValue({
      total_predictions: 100,
      accuracy: 0.85,
    })
  })

  it('should call analyzeEnsemble when ensemble model is selected', async () => {
    const user = userEvent.setup()
    const mockEnsembleResult = {
      article_id: 'test-123',
      primary_prediction: {
        label: 'Fake',
        confidence: 0.92,
        scores: { True: 0.05, Fake: 0.92, Satire: 0.02, Bias: 0.01 },
      },
      voting_strategies: {
        hard_voting: { label: 'Fake', confidence: 0.92, scores: {} },
        soft_voting: { label: 'Fake', confidence: 0.90, scores: {} },
        weighted_voting: { label: 'Fake', confidence: 0.91, scores: {} },
      },
      individual_models: [],
      merged_explanation: [],
    }

    api.analyzeEnsemble.mockResolvedValue(mockEnsembleResult)

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    // Select ensemble model
    const ensembleButton = screen.getByRole('button', { name: /ensemble/i })
    await user.click(ensembleButton)

    // Enter text
    const textarea = screen.getByPlaceholderText(/paste article text/i)
    await user.type(textarea, 'This is a test article about fake news detection.')

    // Click analyze
    const analyzeButton = screen.getByRole('button', { name: /analyze/i })
    await user.click(analyzeButton)

    // Verify analyzeEnsemble was called
    await waitFor(() => {
      expect(api.analyzeEnsemble).toHaveBeenCalledWith(
        'This is a test article about fake news detection.'
      )
    })

    // Verify analyzeNews was NOT called
    expect(api.analyzeNews).not.toHaveBeenCalled()
  })

  it('should call analyzeNews for individual models', async () => {
    const user = userEvent.setup()
    const mockResult = {
      article_id: 'test-456',
      label: 'True',
      confidence: 0.88,
      scores: { True: 0.88, Fake: 0.08, Satire: 0.02, Bias: 0.02 },
      model_used: 'distilbert',
    }

    api.analyzeNews.mockResolvedValue(mockResult)

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    // DistilBERT is selected by default
    // Enter text
    const textarea = screen.getByPlaceholderText(/paste article text/i)
    await user.type(textarea, 'This is a test article.')

    // Click analyze
    const analyzeButton = screen.getByRole('button', { name: /analyze/i })
    await user.click(analyzeButton)

    // Verify analyzeNews was called with correct model
    await waitFor(() => {
      expect(api.analyzeNews).toHaveBeenCalledWith(
        'This is a test article.',
        'distilbert'
      )
    })

    // Verify analyzeEnsemble was NOT called
    expect(api.analyzeEnsemble).not.toHaveBeenCalled()
  })

  it('should display "Running 3 models..." when ensemble is loading', async () => {
    const user = userEvent.setup()
    
    // Make the API call hang so we can see loading state
    api.analyzeEnsemble.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    )

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    // Select ensemble
    const ensembleButton = screen.getByRole('button', { name: /ensemble/i })
    await user.click(ensembleButton)

    // Enter text and analyze
    const textarea = screen.getByPlaceholderText(/paste article text/i)
    await user.type(textarea, 'Test article')

    const analyzeButton = screen.getByRole('button', { name: /analyze/i })
    await user.click(analyzeButton)

    // Check for ensemble-specific loading message
    await waitFor(() => {
      expect(screen.getByText(/running 3 models/i)).toBeInTheDocument()
    })
  })

  it('should not call any API when text is empty', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )

    // Click analyze without entering text
    const analyzeButton = screen.getByRole('button', { name: /analyze/i })
    await user.click(analyzeButton)

    // Verify no API calls were made
    expect(api.analyzeEnsemble).not.toHaveBeenCalled()
    expect(api.analyzeNews).not.toHaveBeenCalled()
  })
})

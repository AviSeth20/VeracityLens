import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResultCard from './ResultCard'

/**
 * Unit tests for ResultCard component ensemble display
 * 
 * **Validates: Requirements 3.3, 3.4**
 * 
 * Tests:
 * - ResultCard displays ensemble results with primary prediction
 * - ResultCard shows voting strategies in expandable section
 * - ResultCard displays individual model predictions
 * - ResultCard shows merged token explanations
 * - ResultCard handles non-ensemble results correctly
 */

// Mock API functions
vi.mock('../services/api', () => ({
  submitFeedback: vi.fn(),
  explainPrediction: vi.fn(),
}))

describe('ResultCard - Ensemble Display', () => {
  const mockEnsembleResult = {
    article_id: 'test-123',
    primary_prediction: {
      label: 'Fake',
      confidence: 0.92,
      scores: { True: 0.05, Fake: 0.92, Satire: 0.02, Bias: 0.01 },
    },
    voting_strategies: {
      hard_voting: {
        label: 'Fake',
        confidence: 0.92,
        scores: { True: 0.05, Fake: 0.92, Satire: 0.02, Bias: 0.01 },
      },
      soft_voting: {
        label: 'Fake',
        confidence: 0.90,
        scores: { True: 0.07, Fake: 0.90, Satire: 0.02, Bias: 0.01 },
      },
      weighted_voting: {
        label: 'Fake',
        confidence: 0.91,
        scores: { True: 0.06, Fake: 0.91, Satire: 0.02, Bias: 0.01 },
      },
    },
    individual_models: [
      {
        model_name: 'distilbert',
        label: 'Fake',
        confidence: 0.89,
        scores: { True: 0.08, Fake: 0.89, Satire: 0.02, Bias: 0.01 },
      },
      {
        model_name: 'roberta',
        label: 'Fake',
        confidence: 0.93,
        scores: { True: 0.04, Fake: 0.93, Satire: 0.02, Bias: 0.01 },
      },
      {
        model_name: 'xlnet',
        label: 'Fake',
        confidence: 0.94,
        scores: { True: 0.03, Fake: 0.94, Satire: 0.02, Bias: 0.01 },
      },
    ],
    merged_explanation: [
      { token: 'fake', score: 0.85 },
      { token: 'news', score: 0.72 },
      { token: 'misleading', score: 0.68 },
    ],
  }

  it('should display primary prediction from hard voting', () => {
    render(<ResultCard result={mockEnsembleResult} />)

    // Check primary prediction label (should appear in the main heading)
    const headings = screen.getAllByText('Likely Fake')
    expect(headings.length).toBeGreaterThan(0)

    // Check confidence percentage (92%)
    expect(screen.getByText('92')).toBeInTheDocument()

    // Check ensemble badge
    expect(screen.getByText('ensemble')).toBeInTheDocument()
  })

  it('should display voting strategies comparison section', () => {
    render(<ResultCard result={mockEnsembleResult} />)

    // Check for voting strategies section header
    expect(screen.getByText(/voting strategies comparison/i)).toBeInTheDocument()
  })

  it('should expand voting strategies when clicked', async () => {
    const user = userEvent.setup()
    render(<ResultCard result={mockEnsembleResult} />)

    // Initially, voting strategy details should not be visible
    expect(screen.queryByText('Hard Voting')).not.toBeInTheDocument()

    // Click to expand
    const expandButton = screen.getByRole('button', {
      name: /voting strategies comparison/i,
    })
    await user.click(expandButton)

    // Now voting strategies should be visible
    expect(screen.getByText('Hard Voting')).toBeInTheDocument()
    expect(screen.getByText('Soft Voting')).toBeInTheDocument()
    expect(screen.getByText('Weighted Voting')).toBeInTheDocument()

    // Check descriptions
    expect(screen.getByText('Majority vote from all models')).toBeInTheDocument()
    expect(screen.getByText('Average probability scores')).toBeInTheDocument()
    expect(screen.getByText('Accuracy-weighted average')).toBeInTheDocument()
  })

  it('should display individual model predictions section', () => {
    render(<ResultCard result={mockEnsembleResult} />)

    // Check for individual models section header
    expect(screen.getByText(/individual model predictions/i)).toBeInTheDocument()
  })

  it('should expand individual model predictions when clicked', async () => {
    const user = userEvent.setup()
    render(<ResultCard result={mockEnsembleResult} />)

    // Initially, model details should not be visible
    expect(screen.queryByText('distilbert')).not.toBeInTheDocument()

    // Click to expand
    const expandButton = screen.getByRole('button', {
      name: /individual model predictions/i,
    })
    await user.click(expandButton)

    // Now individual models should be visible
    expect(screen.getByText('distilbert')).toBeInTheDocument()
    expect(screen.getByText('roberta')).toBeInTheDocument()
    expect(screen.getByText('xlnet')).toBeInTheDocument()

    // Check confidence values are displayed
    expect(screen.getByText('89%')).toBeInTheDocument()
    expect(screen.getByText('93%')).toBeInTheDocument()
    expect(screen.getByText('94%')).toBeInTheDocument()
  })

  it('should display merged token explanations', () => {
    render(<ResultCard result={mockEnsembleResult} />)

    // Check for merged explanations section
    expect(screen.getByText(/merged token explanations/i)).toBeInTheDocument()

    // Check that tokens are displayed
    expect(screen.getByText('fake')).toBeInTheDocument()
    expect(screen.getByText('news')).toBeInTheDocument()
    expect(screen.getByText('misleading')).toBeInTheDocument()
  })

  it('should handle non-ensemble results correctly', () => {
    const mockSingleResult = {
      article_id: 'test-456',
      label: 'True',
      confidence: 0.88,
      scores: { True: 0.88, Fake: 0.08, Satire: 0.02, Bias: 0.02 },
      model_used: 'distilbert',
    }

    render(<ResultCard result={mockSingleResult} />)

    // Should display single model result (check that it appears at least once)
    const trueLabels = screen.getAllByText('Verified True')
    expect(trueLabels.length).toBeGreaterThan(0)
    
    expect(screen.getByText('88')).toBeInTheDocument()
    expect(screen.getByText('distilbert')).toBeInTheDocument()

    // Should NOT display ensemble-specific sections
    expect(screen.queryByText(/voting strategies comparison/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/individual model predictions/i)).not.toBeInTheDocument()

    // Should display tabs for single model
    expect(screen.getByText('Prediction')).toBeInTheDocument()
    expect(screen.getByText('Probabilities')).toBeInTheDocument()
    expect(screen.getByText('Explain')).toBeInTheDocument()
  })

  it('should not display tabs for ensemble results', () => {
    render(<ResultCard result={mockEnsembleResult} />)

    // Tabs should not be present for ensemble results
    expect(screen.queryByText('Prediction')).not.toBeInTheDocument()
    expect(screen.queryByText('Probabilities')).not.toBeInTheDocument()
    expect(screen.queryByText('Explain')).not.toBeInTheDocument()
  })

  it('should display correct confidence values for voting strategies', async () => {
    const user = userEvent.setup()
    render(<ResultCard result={mockEnsembleResult} />)

    // Expand voting strategies
    const expandButton = screen.getByRole('button', {
      name: /voting strategies comparison/i,
    })
    await user.click(expandButton)

    // Check confidence percentages
    expect(screen.getByText('92%')).toBeInTheDocument() // hard voting
    expect(screen.getByText('90%')).toBeInTheDocument() // soft voting
    expect(screen.getByText('91%')).toBeInTheDocument() // weighted voting
  })
})

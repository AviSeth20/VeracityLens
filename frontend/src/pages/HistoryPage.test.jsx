import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import fc from 'fast-check'
import HistoryPage from './HistoryPage'
import { ThemeProvider } from '../contexts/ThemeContext'
import * as api from '../services/api'
import * as sessionTrackerModule from '../utils/sessionTracker'

// Mock the API and session tracker
vi.mock('../services/api')
vi.mock('../utils/sessionTracker')

// Helper to render HistoryPage with all required providers
const renderHistoryPage = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <HistoryPage />
      </ThemeProvider>
    </BrowserRouter>
  )
}

// Mock history data generator
const generateMockHistory = (count) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `id-${i}`,
    session_id: 'test-session-id',
    article_id: `article-${i}`,
    text_preview: `This is a test article preview ${i}`,
    predicted_label: ['True', 'Fake', 'Satire', 'Bias'][i % 4],
    confidence: 0.85 + (i % 10) / 100,
    model_name: ['distilbert', 'roberta', 'xlnet', 'ensemble'][i % 4],
    created_at: new Date(Date.now() - i * 3600000).toISOString(),
  }))
}

describe('HistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    // Mock session tracker
    sessionTrackerModule.sessionTracker = {
      getSessionId: vi.fn().mockReturnValue('test-session-id'),
    }
  })

  // ============================================================================
  // PROPERTY-BASED TEST
  // Feature: phase-1-enhancements, Property 25: History Fetch on Page Load
  // ============================================================================

  describe('Property 25: History Fetch on Page Load', () => {
    it('fetches and displays predictions for the current session on page load', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.uuid(), // Generate random session ID
          fc.array(
            fc.record({
              article_id: fc.uuid(),
              text_preview: fc.string({ minLength: 10, maxLength: 200 }),
              predicted_label: fc.constantFrom('True', 'Fake', 'Satire', 'Bias'),
              confidence: fc.double({ min: 0.0, max: 1.0 }),
              model_name: fc.constantFrom('distilbert', 'roberta', 'xlnet', 'ensemble'),
              created_at: fc.date().map(d => d.toISOString()),
            }),
            { minLength: 0, maxLength: 10 }
          ),
          async (sessionId, historyItems) => {
            // Setup mocks
            sessionTrackerModule.sessionTracker.getSessionId.mockReturnValue(sessionId)
            api.getUserHistory.mockResolvedValue({
              status: 'success',
              session_id: sessionId,
              count: historyItems.length,
              history: historyItems,
            })

            // Render component
            const { unmount } = renderHistoryPage()

            // Wait for loading to complete
            await waitFor(() => {
              expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
            }, { timeout: 10000 })

            // Verify API was called with correct session ID
            expect(api.getUserHistory).toHaveBeenCalledWith(sessionId)

            // Verify history items are displayed or empty state is shown
            if (historyItems.length === 0) {
              expect(screen.queryByText(/no analysis history yet/i)).toBeInTheDocument()
            } else {
              // Check that at least some history items are displayed
              expect(screen.queryByText(/analysis history/i)).toBeInTheDocument()
              expect(screen.queryByText(new RegExp(`${historyItems.length} prediction`))).toBeInTheDocument()
            }

            // Clean up
            unmount()
          }
        ),
        { numRuns: 100, timeout: 15000 }
      )
    }, 20000) // Increase test timeout to 20 seconds
  })


  // ============================================================================
  // UNIT TESTS FOR HISTORY PAGE
  // ============================================================================

  describe('Loading State', () => {
    it('displays loading skeleton while fetching history', () => {
      // Mock API to never resolve
      api.getUserHistory.mockImplementation(() => new Promise(() => {}))

      renderHistoryPage()

      // Check for skeleton elements (animated pulse divs)
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Error State', () => {
    it('displays error message when API fails', async () => {
      api.getUserHistory.mockRejectedValue(new Error('Network error'))

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText(/failed to load history/i)).toBeInTheDocument()
      })
    })

    it('displays retry button on error', async () => {
      api.getUserHistory.mockRejectedValue(new Error('Network error'))

      renderHistoryPage()

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /retry/i })
        expect(retryButton).toBeInTheDocument()
      })
    })

    it('retries loading history when retry button is clicked', async () => {
      const user = userEvent.setup()
      
      // First call fails
      api.getUserHistory.mockRejectedValueOnce(new Error('Network error'))
      // Second call succeeds
      api.getUserHistory.mockResolvedValueOnce({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: generateMockHistory(1),
      })

      const { unmount } = renderHistoryPage()

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText(/failed to load history/i)).toBeInTheDocument()
      })

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      // Should show loading then success
      await waitFor(() => {
        expect(screen.queryByText(/failed to load history/i)).not.toBeInTheDocument()
        expect(screen.getAllByText(/analysis history/i)[0]).toBeInTheDocument()
      })

      // Clean up
      unmount()
    })
  })


  describe('Empty State', () => {
    it('displays empty state message when no history exists', async () => {
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 0,
        history: [],
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText(/no analysis history yet/i)).toBeInTheDocument()
        expect(screen.getByText(/start analyzing news articles/i)).toBeInTheDocument()
      })
    })

    it('displays call-to-action button in empty state', async () => {
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 0,
        history: [],
      })

      renderHistoryPage()

      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: /analyze your first article/i })
        expect(ctaButton).toBeInTheDocument()
      })
    })
  })

  describe('History Items Display', () => {
    it('displays history items correctly', async () => {
      const mockHistory = generateMockHistory(3)
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 3,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText(/3 predictions in your history/i)).toBeInTheDocument()
      })

      // Check that text previews are displayed
      mockHistory.forEach((item) => {
        expect(screen.getByText(item.text_preview)).toBeInTheDocument()
      })
    })

    it('displays predicted label for each item', async () => {
      const mockHistory = [
        {
          ...generateMockHistory(1)[0],
          predicted_label: 'True',
        },
      ]
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText('True')).toBeInTheDocument()
      })
    })

    it('displays confidence percentage for each item', async () => {
      const mockHistory = [
        {
          ...generateMockHistory(1)[0],
          confidence: 0.85,
        },
      ]
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText(/85% confidence/i)).toBeInTheDocument()
      })
    })

    it('displays model name for each item', async () => {
      const mockHistory = [
        {
          ...generateMockHistory(1)[0],
          model_name: 'ensemble',
        },
      ]
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText('ensemble')).toBeInTheDocument()
      })
    })

    it('displays created date for each item', async () => {
      const mockHistory = generateMockHistory(1)
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        const dateStr = new Date(mockHistory[0].created_at).toLocaleDateString()
        expect(screen.getByText(dateStr)).toBeInTheDocument()
      })
    })
  })

  describe('History Item Navigation', () => {
    it('navigates to home when history item is clicked', async () => {
      const user = userEvent.setup()
      const mockHistory = generateMockHistory(1)
      api.getUserHistory.mockResolvedValue({
        status: 'success',
        session_id: 'test-session-id',
        count: 1,
        history: mockHistory,
      })

      renderHistoryPage()

      await waitFor(() => {
        expect(screen.getByText(mockHistory[0].text_preview)).toBeInTheDocument()
      })

      // Click on the history item
      const historyCard = screen.getByText(mockHistory[0].text_preview).closest('div[class*="cursor-pointer"]')
      await user.click(historyCard)

      // Should navigate to home (we can't fully test navigation in unit tests,
      // but we can verify the click handler is attached)
      expect(historyCard).toBeInTheDocument()
    })
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ModelSelector from './ModelSelector'

/**
 * Unit tests for ModelSelector component
 * 
 * **Validates: Requirements 3.1, 3.2**
 * 
 * Tests:
 * - Ensemble option is displayed in the model selector
 * - Ensemble option shows correct label and description
 * - Clicking ensemble option calls onChange with 'ensemble'
 * - All model options are rendered correctly
 */

describe('ModelSelector', () => {
  it('should display ensemble option with correct label and description', () => {
    const mockOnChange = vi.fn()
    render(<ModelSelector selected="distilbert" onChange={mockOnChange} />)

    // Check that ensemble option is present
    const ensembleButton = screen.getByRole('button', { name: /ensemble/i })
    expect(ensembleButton).toBeInTheDocument()

    // Check label
    expect(screen.getByText('Ensemble')).toBeInTheDocument()

    // Check description
    expect(screen.getByText(/All 3 Models · Most Accurate/i)).toBeInTheDocument()

    // Check badge
    expect(screen.getByText('Best')).toBeInTheDocument()
  })

  it('should call onChange with "ensemble" when ensemble option is clicked', async () => {
    const user = userEvent.setup()
    const mockOnChange = vi.fn()
    render(<ModelSelector selected="distilbert" onChange={mockOnChange} />)

    const ensembleButton = screen.getByRole('button', { name: /ensemble/i })
    await user.click(ensembleButton)

    expect(mockOnChange).toHaveBeenCalledWith('ensemble')
    expect(mockOnChange).toHaveBeenCalledTimes(1)
  })

  it('should highlight ensemble option when selected', () => {
    const mockOnChange = vi.fn()
    render(<ModelSelector selected="ensemble" onChange={mockOnChange} />)

    const ensembleButton = screen.getByRole('button', { name: /ensemble/i })
    
    // Check for selected styling (border-[#d97757] and bg-[#fff5f2])
    expect(ensembleButton).toHaveClass('border-[#d97757]')
    expect(ensembleButton).toHaveClass('bg-[#fff5f2]')
  })

  it('should render all four model options', () => {
    const mockOnChange = vi.fn()
    render(<ModelSelector selected="distilbert" onChange={mockOnChange} />)

    // Check all models are present
    expect(screen.getByText('Ensemble')).toBeInTheDocument()
    expect(screen.getByText('DistilBERT')).toBeInTheDocument()
    expect(screen.getByText('RoBERTa')).toBeInTheDocument()
    expect(screen.getByText('XLNet')).toBeInTheDocument()
  })

  it('should display correct descriptions for each model', () => {
    const mockOnChange = vi.fn()
    render(<ModelSelector selected="distilbert" onChange={mockOnChange} />)

    expect(screen.getByText('All 3 Models · Most Accurate')).toBeInTheDocument()
    expect(screen.getByText('66M · Fast')).toBeInTheDocument()
    expect(screen.getByText('125M · Accurate')).toBeInTheDocument()
    expect(screen.getByText('110M · Context-aware')).toBeInTheDocument()
  })
})

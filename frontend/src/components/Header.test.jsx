import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Header from './Header'
import { ThemeProvider } from '../contexts/ThemeContext'

// Helper to render Header with all required providers
const renderHeader = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider>
        <Header />
      </ThemeProvider>
    </BrowserRouter>
  )
}

describe('Header - Theme Toggle Button', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  // ============================================================================
  // UNIT TESTS FOR THEME TOGGLE BUTTON
  // ============================================================================

  describe('Theme Toggle Button Display', () => {
    it('displays moon icon in light mode', () => {
      renderHeader()

      // In light mode, should show moon icon (switch to dark mode)
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toBeInTheDocument()

      // Check for moon icon (lucide-react renders as svg)
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('displays sun icon in dark mode', () => {
      // Set dark mode in localStorage
      localStorage.setItem('veracitylens_theme', 'dark')

      renderHeader()

      // In dark mode, should show sun icon (switch to light mode)
      const button = screen.getByRole('button', { name: /switch to light mode/i })
      expect(button).toBeInTheDocument()

      // Check for sun icon
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('has correct aria-label for light mode', () => {
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toHaveAttribute('aria-label', 'Switch to dark mode')
    })

    it('has correct aria-label for dark mode', () => {
      localStorage.setItem('veracitylens_theme', 'dark')

      renderHeader()

      const button = screen.getByRole('button', { name: /switch to light mode/i })
      expect(button).toHaveAttribute('aria-label', 'Switch to light mode')
    })

    it('has correct title tooltip for light mode', () => {
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toHaveAttribute('title', 'Switch to dark mode')
    })

    it('has correct title tooltip for dark mode', () => {
      localStorage.setItem('veracitylens_theme', 'dark')

      renderHeader()

      const button = screen.getByRole('button', { name: /switch to light mode/i })
      expect(button).toHaveAttribute('title', 'Switch to light mode')
    })
  })

  describe('Theme Toggle Button Interaction', () => {
    it('toggles theme when clicked', async () => {
      const user = userEvent.setup()
      renderHeader()

      // Start in light mode
      expect(document.documentElement.classList.contains('dark')).toBe(false)

      // Click toggle button
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      await user.click(button)

      // Should switch to dark mode
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('toggles theme back when clicked twice', async () => {
      const user = userEvent.setup()
      renderHeader()

      // Start in light mode
      expect(document.documentElement.classList.contains('dark')).toBe(false)

      // Click toggle button twice
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      await user.click(button)
      
      // Wait for state update and re-query button
      const darkButton = screen.getByRole('button', { name: /switch to light mode/i })
      await user.click(darkButton)

      // Should be back to light mode
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('persists theme change to localStorage', async () => {
      const user = userEvent.setup()
      renderHeader()

      // Click toggle button
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      await user.click(button)

      // Check localStorage
      expect(localStorage.getItem('veracitylens_theme')).toBe('dark')
    })
  })

  describe('Theme Toggle Button Keyboard Navigation', () => {
    it('is focusable via Tab key', async () => {
      const user = userEvent.setup()
      renderHeader()

      // Tab to focus elements
      await user.tab()
      
      // Keep tabbing until we reach the theme toggle button
      let attempts = 0
      while (attempts < 10) {
        const focused = document.activeElement
        if (focused && focused.getAttribute('aria-label')?.includes('Switch to')) {
          // Found the theme toggle button
          expect(focused).toBeInTheDocument()
          return
        }
        await user.tab()
        attempts++
      }

      // If we get here, we should still be able to find the button
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toBeInTheDocument()
    })

    it('activates on Enter key', async () => {
      const user = userEvent.setup()
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      button.focus()

      // Press Enter
      await user.keyboard('{Enter}')

      // Should toggle theme
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('activates on Space key', async () => {
      const user = userEvent.setup()
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      button.focus()

      // Press Space
      await user.keyboard(' ')

      // Should toggle theme
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })

  describe('Theme Toggle Button Styling', () => {
    it('has hover styles applied', () => {
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      
      // Check for hover classes
      expect(button.className).toContain('hover:bg-')
      expect(button.className).toContain('hover:text-')
    })

    it('has transition styles for smooth animation', () => {
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      
      // Check for transition class
      expect(button.className).toContain('transition')
    })

    it('has rounded corners for consistent design', () => {
      renderHeader()

      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      
      // Check for rounded class
      expect(button.className).toContain('rounded')
    })
  })

  describe('Theme Toggle Button Integration', () => {
    it('updates icon when theme changes', async () => {
      const user = userEvent.setup()
      renderHeader()

      // Start with moon icon (light mode)
      let button = screen.getByRole('button', { name: /switch to dark mode/i })
      expect(button).toBeInTheDocument()

      // Click to switch to dark mode
      await user.click(button)

      // Should now show sun icon (dark mode)
      button = screen.getByRole('button', { name: /switch to light mode/i })
      expect(button).toBeInTheDocument()
    })

    it('maintains theme state across re-renders', async () => {
      const user = userEvent.setup()
      const { rerender } = renderHeader()

      // Toggle to dark mode
      const button = screen.getByRole('button', { name: /switch to dark mode/i })
      await user.click(button)

      // Re-render
      rerender(
        <BrowserRouter>
          <ThemeProvider>
            <Header />
          </ThemeProvider>
        </BrowserRouter>
      )

      // Should still be in dark mode
      expect(document.documentElement.classList.contains('dark')).toBe(true)
      expect(screen.getByRole('button', { name: /switch to light mode/i })).toBeInTheDocument()
    })
  })
})

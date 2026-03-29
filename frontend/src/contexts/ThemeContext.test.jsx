import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import fc from 'fast-check'
import { ThemeProvider, useTheme } from './ThemeContext'

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  // ============================================================================
  // PROPERTY-BASED TESTS
  // ============================================================================

  describe('Property Tests', () => {
    // Feature: phase-1-enhancements, Property 18: Theme Toggle Idempotence
    it('Property 18: Toggling theme twice returns to original state', () => {
      fc.assert(
        fc.property(fc.constantFrom('light', 'dark'), (initialTheme) => {
          const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
          })

          // Set initial theme
          act(() => {
            while (result.current.theme !== initialTheme) {
              result.current.toggleTheme()
            }
          })

          const startTheme = result.current.theme

          // Toggle twice
          act(() => {
            result.current.toggleTheme()
            result.current.toggleTheme()
          })

          // Should return to original
          expect(result.current.theme).toBe(startTheme)
        }),
        { numRuns: 100 }
      )
    })

    // Feature: phase-1-enhancements, Property 19: Theme Persistence Round-Trip
    it('Property 19: Saving theme to localStorage then retrieving returns same value', () => {
      fc.assert(
        fc.property(fc.constantFrom('light', 'dark'), (themeValue) => {
          // Store to localStorage
          localStorage.setItem('veracitylens_theme', themeValue)

          // Retrieve from localStorage
          const retrieved = localStorage.getItem('veracitylens_theme')

          // Should match original
          expect(retrieved).toBe(themeValue)
        }),
        { numRuns: 100 }
      )
    })

    // Feature: phase-1-enhancements, Property 20: Dark Mode Class Application
    it('Property 20: Dark theme applies "dark" class, light theme removes it', () => {
      fc.assert(
        fc.property(fc.constantFrom('light', 'dark'), (themeValue) => {
          const { result } = renderHook(() => useTheme(), {
            wrapper: ThemeProvider,
          })

          // Set theme
          act(() => {
            while (result.current.theme !== themeValue) {
              result.current.toggleTheme()
            }
          })

          // Check document root class
          if (themeValue === 'dark') {
            expect(document.documentElement.classList.contains('dark')).toBe(true)
          } else {
            expect(document.documentElement.classList.contains('dark')).toBe(false)
          }
        }),
        { numRuns: 100 }
      )
    })
  })

  // ============================================================================
  // UNIT TESTS
  // ============================================================================

  describe('Unit Tests', () => {
    it('initializes theme from localStorage when available', () => {
      localStorage.setItem('veracitylens_theme', 'dark')

      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      expect(result.current.theme).toBe('dark')
      expect(result.current.isDark).toBe(true)
    })

    it('defaults to light theme when no saved theme exists', () => {
      // Mock matchMedia to return false for dark mode preference
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      expect(result.current.theme).toBe('light')
      expect(result.current.isDark).toBe(false)
    })

    it('defaults to dark theme when system preference is dark', () => {
      // Mock matchMedia to return true for dark mode preference
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      expect(result.current.theme).toBe('dark')
      expect(result.current.isDark).toBe(true)
    })

    it('toggleTheme switches from light to dark', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      // Start with light
      act(() => {
        while (result.current.theme !== 'light') {
          result.current.toggleTheme()
        }
      })

      expect(result.current.theme).toBe('light')

      // Toggle to dark
      act(() => {
        result.current.toggleTheme()
      })

      expect(result.current.theme).toBe('dark')
      expect(result.current.isDark).toBe(true)
    })

    it('toggleTheme switches from dark to light', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      // Start with dark
      act(() => {
        while (result.current.theme !== 'dark') {
          result.current.toggleTheme()
        }
      })

      expect(result.current.theme).toBe('dark')

      // Toggle to light
      act(() => {
        result.current.toggleTheme()
      })

      expect(result.current.theme).toBe('light')
      expect(result.current.isDark).toBe(false)
    })

    it('persists theme to localStorage on change', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      act(() => {
        result.current.toggleTheme()
      })

      const saved = localStorage.getItem('veracitylens_theme')
      expect(saved).toBe(result.current.theme)
    })

    it('applies dark class to document root when dark mode is active', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      // Set to dark
      act(() => {
        while (result.current.theme !== 'dark') {
          result.current.toggleTheme()
        }
      })

      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('removes dark class from document root when light mode is active', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      // Set to light
      act(() => {
        while (result.current.theme !== 'light') {
          result.current.toggleTheme()
        }
      })

      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('handles localStorage unavailable gracefully', () => {
      // Mock localStorage to throw error
      const originalSetItem = Storage.prototype.setItem
      Storage.prototype.setItem = vi.fn(() => {
        throw new Error('localStorage unavailable')
      })

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const { result } = renderHook(() => useTheme(), {
        wrapper: ThemeProvider,
      })

      act(() => {
        result.current.toggleTheme()
      })

      // Should still work, just log warning
      expect(consoleSpy).toHaveBeenCalledWith('Failed to persist theme preference')

      // Restore
      Storage.prototype.setItem = originalSetItem
      consoleSpy.mockRestore()
    })

    it('throws error when useTheme is used outside ThemeProvider', () => {
      expect(() => {
        renderHook(() => useTheme())
      }).toThrow('useTheme must be used within ThemeProvider')
    })
  })
})

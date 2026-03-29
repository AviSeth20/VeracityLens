import React, { createContext, useContext, useState, useEffect, useRef } from 'react'

const ThemeContext = createContext()

const THEME_KEY = 'veracitylens_theme'
const DEBOUNCE_DELAY = 300

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY)
      if (saved === 'light' || saved === 'dark') return saved
    } catch {
      console.warn('localStorage unavailable for theme')
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  const debounceTimerRef = useRef(null)

  useEffect(() => {
    const root = document.documentElement
    theme === 'dark' ? root.classList.add('dark') : root.classList.remove('dark')
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      console.warn('Failed to persist theme preference')
    }
  }, [theme])

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
    }
  }, [])

  const toggleTheme = () => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
    debounceTimerRef.current = setTimeout(() => {
      setTheme(prev => prev === 'light' ? 'dark' : 'light')
      debounceTimerRef.current = null
    }, DEBOUNCE_DELAY)
  }

  return (
    <ThemeContext.Provider value={{ theme, isDark: theme === 'dark', toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}

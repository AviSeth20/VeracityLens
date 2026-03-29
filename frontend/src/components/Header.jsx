import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Github, Moon, Sun } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'

const NAV = [
  { label: 'Analyze', to: '/' },
  { label: 'Live News', to: '/news' },
  { label: 'History', to: '/history' },
]

export default function Header() {
  const navigate = useNavigate()
  const { isDark, toggleTheme } = useTheme()

  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="sticky top-0 z-50 bg-[#faf9f7]/90 dark:bg-[#1c1917]/90 backdrop-blur-md border-b border-[#ede9e2] dark:border-[#44403c]"
    >
      <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <button onClick={() => navigate('/')} className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: 8, scale: 1.05 }}
            transition={{ type: 'spring', stiffness: 300 }}
            className="w-9 h-9 bg-[#d97757] rounded-xl flex items-center justify-center shadow-sm"
          >
            <Brain className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className="text-[15px] font-semibold text-[#1a1a1a] dark:text-[#fafaf9] tracking-tight">
              VeracityLens
            </h1>
            <p className="text-[11px] text-[#8a8a8a] dark:text-[#a8a29e] leading-none mt-0.5">
              AI-Powered News Verification
            </p>
          </div>
        </button>

        {/* Nav */}
        <nav className="hidden sm:flex items-center gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  isActive
                    ? 'bg-[#ede9e2] dark:bg-[#292524] text-[#1a1a1a] dark:text-[#fafaf9] font-medium'
                    : 'text-[#5a5a5a] dark:text-[#a8a29e] hover:bg-[#ede9e2] dark:hover:bg-[#292524]'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          <button
            onClick={toggleTheme}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            className="ml-1 p-1.5 text-[#5a5a5a] dark:text-[#a8a29e] hover:text-[#1a1a1a] dark:hover:text-[#fafaf9] hover:bg-[#ede9e2] dark:hover:bg-[#292524] rounded-lg transition-all"
          >
            <motion.div
              initial={false}
              animate={{ rotate: isDark ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </motion.div>
          </button>
          <a
            href="https://github.com/AviSeth20/VeracityLens"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-1 p-1.5 text-[#5a5a5a] dark:text-[#a8a29e] hover:text-[#1a1a1a] dark:hover:text-[#fafaf9] hover:bg-[#ede9e2] dark:hover:bg-[#292524] rounded-lg transition-colors"
          >
            <Github className="w-4 h-4" />
          </a>
        </nav>
      </div>
    </motion.header>
  )
}

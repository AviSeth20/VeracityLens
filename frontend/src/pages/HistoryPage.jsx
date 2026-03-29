import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Clock, TrendingUp, CheckCircle, AlertTriangle, Zap, Eye } from 'lucide-react'
import { getUserHistory } from '../services/api'
import { sessionTracker } from '../utils/sessionTracker'

const CONFIG = {
  True: {
    icon: CheckCircle,
    color: '#16a34a',
    badge: 'bg-emerald-100 text-emerald-700',
  },
  Fake: {
    icon: AlertTriangle,
    color: '#dc2626',
    badge: 'bg-red-100 text-red-700',
  },
  Satire: {
    icon: Zap,
    color: '#7c3aed',
    badge: 'bg-violet-100 text-violet-700',
  },
  Bias: {
    icon: Eye,
    color: '#d97706',
    badge: 'bg-amber-100 text-amber-700',
  },
}

function LoadingHistorySkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="mb-8">
        <div className="h-8 bg-[#f5f3ef] dark:bg-[#292524] rounded w-64 mb-2 animate-pulse" />
        <div className="h-4 bg-[#f5f3ef] dark:bg-[#292524] rounded w-48 animate-pulse" />
      </div>
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-[#1c1917] border border-[#ede9e2] dark:border-[#44403c] rounded-xl p-5 animate-pulse"
          >
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-[#f5f3ef] dark:bg-[#292524] rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-[#f5f3ef] dark:bg-[#292524] rounded w-3/4" />
                <div className="h-3 bg-[#f5f3ef] dark:bg-[#292524] rounded w-full" />
                <div className="h-3 bg-[#f5f3ef] dark:bg-[#292524] rounded w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ErrorMessage({ message, onRetry }) {
  return (
    <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-xl px-5 py-4">
      <p className="text-sm text-red-700 dark:text-red-400 mb-3">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
      >
        Retry
      </button>
    </div>
  )
}

const HistoryCard = React.memo(function HistoryCard({ item, onClick }) {
  const config = CONFIG[item.predicted_label] || CONFIG.True
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className="bg-white dark:bg-[#1c1917] border border-[#ede9e2] dark:border-[#44403c] rounded-xl p-5 cursor-pointer hover:shadow-md dark:hover:shadow-stone-900/50 transition-all"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: `${config.color}18` }}
            >
              <Icon className="w-4 h-4" style={{ color: config.color }} />
            </div>
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${config.badge}`}>
              {item.predicted_label}
            </span>
            <span className="text-xs text-[#8a8a8a] dark:text-[#a8a29e]">
              {item.model_name}
            </span>
          </div>

          <p className="text-sm text-[#3a3a3a] dark:text-[#d6d3d1] line-clamp-2 mb-2">
            {item.text_preview}
          </p>

          <div className="flex items-center gap-4 text-xs text-[#8a8a8a] dark:text-[#a8a29e]">
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {Math.round(item.confidence * 100)}% confidence
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(item.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
})

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      const sessionId = sessionTracker.getSessionId()
      const data = await getUserHistory(sessionId)
      setHistory(data.history || [])
    } catch (err) {
      setError('Failed to load history. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleItemClick = (item) => {
    // Navigate to home with pre-filled text
    navigate('/', {
      state: {
        prefill: item.text_preview,
        articleId: item.article_id,
      },
    })
  }

  if (loading) {
    return <LoadingHistorySkeleton />
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10">
        <ErrorMessage message={error} onRetry={loadHistory} />
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10 text-center">
        <Clock className="w-16 h-16 text-[#c8bfb0] dark:text-[#78716c] mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-[#3a3a3a] dark:text-[#d6d3d1] mb-2">
          No analysis history yet
        </h2>
        <p className="text-[#8a8a8a] dark:text-[#a8a29e] mb-6">
          Start analyzing news articles to build your history.
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 bg-[#d97757] text-white rounded-lg hover:bg-[#c4623e] transition-colors"
        >
          Analyze Your First Article
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#faf9f7] dark:bg-[#0c0a09] transition-colors duration-200">
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#1a1a1a] dark:text-[#fafaf9] mb-2">
            Analysis History
          </h1>
          <p className="text-[#8a8a8a] dark:text-[#a8a29e]">
            {history.length} prediction{history.length !== 1 ? 's' : ''} in your history
          </p>
        </div>

        <div className="space-y-4">
          {history.map((item) => (
            <HistoryCard
              key={item.article_id}
              item={item}
              onClick={() => handleItemClick(item)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

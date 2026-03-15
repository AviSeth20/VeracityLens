import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle, AlertTriangle, Zap, Eye,
  ExternalLink, RefreshCw, Newspaper, ArrowLeft, Clock
} from 'lucide-react'
import { getNewspaper } from '../services/api'

const SECTIONS = [
  {
    key: 'True',
    label: 'Verified News',
    icon: CheckCircle,
    color: '#16a34a',
    bg: '#f0fdf4',
    border: '#bbf7d0',
    badgeBg: 'bg-emerald-100',
    badgeText: 'text-emerald-700',
    bar: 'bg-emerald-500',
    desc: 'Articles classified as factual and credible',
  },
  {
    key: 'Fake',
    label: 'Misinformation',
    icon: AlertTriangle,
    color: '#dc2626',
    bg: '#fef2f2',
    border: '#fecaca',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-700',
    bar: 'bg-red-500',
    desc: 'Articles flagged as potentially false or misleading',
  },
  {
    key: 'Satire',
    label: 'Satire & Parody',
    icon: Zap,
    color: '#7c3aed',
    bg: '#faf5ff',
    border: '#e9d5ff',
    badgeBg: 'bg-violet-100',
    badgeText: 'text-violet-700',
    bar: 'bg-violet-500',
    desc: 'Comedic or satirical content about current events',
  },
  {
    key: 'Bias',
    label: 'Biased Reporting',
    icon: Eye,
    color: '#d97706',
    bg: '#fffbeb',
    border: '#fde68a',
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-700',
    bar: 'bg-amber-500',
    desc: 'Articles with detectable political or ideological slant',
  },
]

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function ConfidencePill({ value, bar }) {
  const pct = Math.round((value ?? 0) * 100)
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 bg-[#ede9e2] rounded-full h-1 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className={`h-full rounded-full ${bar}`}
        />
      </div>
      <span className="text-[10px] tabular-nums text-[#8a8a8a]">{pct}%</span>
    </div>
  )
}

function ArticleCard({ item, section, index, onAnalyze }) {
  const { article, prediction } = item
  const conf = prediction?.confidence ?? 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white border border-[#ede9e2] rounded-xl overflow-hidden hover:shadow-md transition-shadow group"
    >
      {/* Accent line */}
      <div className="h-0.5 w-full" style={{ backgroundColor: section.color }} />

      <div className="p-4">
        {/* Source + time */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-semibold text-[#8a8a8a] uppercase tracking-wide">
            {article.source || 'Unknown'}
          </span>
          <div className="flex items-center gap-1 text-[10px] text-[#c8bfb0]">
            <Clock className="w-3 h-3" />
            {timeAgo(article.published_at)}
          </div>
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-[#1a1a1a] leading-snug mb-2 line-clamp-3">
          {article.title}
        </h3>

        {/* Description */}
        {article.description && (
          <p className="text-xs text-[#5a5a5a] leading-relaxed line-clamp-2 mb-3">
            {article.description}
          </p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-[#f5f3ef]">
          <ConfidencePill value={conf} bar={section.bar} />

          <div className="flex items-center gap-2">
            <button
              onClick={() => onAnalyze(article.content || article.description || article.title)}
              className="text-[10px] font-medium px-2.5 py-1 rounded-lg border border-[#ede9e2] text-[#5a5a5a] hover:border-[#d97757] hover:text-[#d97757] transition-colors"
            >
              Analyze
            </button>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#c8bfb0] hover:text-[#d97757] transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function SectionSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="bg-white border border-[#ede9e2] rounded-xl p-4 animate-pulse">
          <div className="h-2 bg-[#f5f3ef] rounded w-1/3 mb-3" />
          <div className="h-3 bg-[#f5f3ef] rounded w-full mb-2" />
          <div className="h-3 bg-[#f5f3ef] rounded w-4/5 mb-2" />
          <div className="h-3 bg-[#f5f3ef] rounded w-2/3" />
        </div>
      ))}
    </div>
  )
}

export default function NewsPage() {
  const navigate = useNavigate()
  const [grouped, setGrouped]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const [lastFetch, setLastFetch] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getNewspaper(6)
      setGrouped(data.grouped)
      setLastFetch(new Date())
    } catch (e) {
      setError('Could not load news. Make sure the API is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleAnalyze = (text) => {
    // Navigate to home with text pre-filled via state
    navigate('/', { state: { prefill: text } })
  }

  return (
    <div className="min-h-screen bg-[#faf9f7]">
      {/* Page header */}
      <div className="bg-white border-b border-[#ede9e2] sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="text-[#8a8a8a] hover:text-[#1a1a1a] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <Newspaper className="w-5 h-5 text-[#d97757]" />
            <div>
              <h1 className="text-base font-semibold text-[#1a1a1a]">Live Newspaper</h1>
              <p className="text-[11px] text-[#8a8a8a]">
                Current news classified by AI · {lastFetch ? `Updated ${timeAgo(lastFetch.toISOString())}` : 'Loading…'}
              </p>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 text-sm text-[#5a5a5a] hover:text-[#1a1a1a] border border-[#ede9e2] bg-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
          >
            <motion.div
              animate={loading ? { rotate: 360 } : { rotate: 0 }}
              transition={{ duration: 0.8, ease: 'linear', repeat: loading ? Infinity : 0 }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </motion.div>
            Refresh
          </motion.button>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-12">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {SECTIONS.map((section) => {
          const Icon = section.icon
          const articles = grouped?.[section.key] ?? []

          return (
            <motion.section
              key={section.key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              {/* Section header */}
              <div
                className="flex items-center gap-3 mb-5 pb-3 border-b-2"
                style={{ borderColor: section.color }}
              >
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: section.bg }}
                >
                  <Icon className="w-5 h-5" style={{ color: section.color }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-[#1a1a1a]">{section.label}</h2>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${section.badgeBg} ${section.badgeText}`}
                    >
                      {loading ? '…' : articles.length} articles
                    </span>
                  </div>
                  <p className="text-xs text-[#8a8a8a]">{section.desc}</p>
                </div>
              </div>

              {/* Articles grid */}
              {loading ? (
                <SectionSkeleton />
              ) : articles.length === 0 ? (
                <div className="text-sm text-[#8a8a8a] py-4 text-center border border-dashed border-[#ede9e2] rounded-xl">
                  No articles classified as {section.label.toLowerCase()} right now
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {articles.map((item, i) => (
                    <ArticleCard
                      key={item.article?.url || i}
                      item={item}
                      section={section}
                      index={i}
                      onAnalyze={handleAnalyze}
                    />
                  ))}
                </div>
              )}
            </motion.section>
          )
        })}
      </main>
    </div>
  )
}

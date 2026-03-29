import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Radio, ExternalLink, RefreshCw, ChevronRight, AlertCircle } from 'lucide-react'
import { fetchNews } from '../services/api'

const TOPICS = ['breaking news', 'politics', 'technology', 'science', 'world']

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000)
  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function stripGNewsTruncation(text) {
  if (!text) return ''
  // GNews appends " [X chars]" at the end — strip it
  return text.replace(/\s*\[\d+\s+chars?\]\s*$/i, '').trim()
}

function buildArticleText(article) {
  const title = (article.title || '').trim()
  const description = stripGNewsTruncation(article.description || '')
  const content = stripGNewsTruncation(article.content || '')

  // Build full text from all available parts, deduplicating
  const parts = []
  if (title) parts.push(title)
  if (description && description !== title) parts.push(description)
  if (content && content !== description && content !== title) parts.push(content)

  const full = parts.join(' ').trim()

  // Trim to end cleanly on a sentence boundary (at least 5 sentences worth)
  const sentences = full.match(/[^.!?]+[.!?]+/g) || []
  if (sentences.length >= 5) {
    return sentences.slice(0, Math.max(5, sentences.length)).join(' ').trim()
  }

  // Fewer than 5 sentences — return everything we have
  return full
}

export default function LiveNewsFeed({ onSelectArticle }) {
  const [articles, setArticles]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError]         = useState(null)
  const [topic, setTopic]         = useState('breaking news')

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const data = await fetchNews(topic, 8)
      setArticles(data.articles || [])
    } catch (e) {
      setError('Could not load news. Is the API running?')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [topic])

  useEffect(() => { load() }, [load])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.35 }}
      className="bg-white dark:bg-[#1c1917] border border-[#ede9e2] dark:border-[#44403c] rounded-2xl overflow-hidden shadow-sm"
    >
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-[#f5f3ef] dark:border-[#44403c] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="w-2 h-2 bg-[#d97757] rounded-full"
          />
          <Radio className="w-3.5 h-3.5 text-[#6a6a6a] dark:text-[#a8a29e]" />
          <span className="text-xs font-medium text-[#3a3a3a] dark:text-[#d6d3d1] uppercase tracking-wide">
            Live News
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => load(true)}
          disabled={refreshing}
          className="text-[#6a6a6a] dark:text-[#a8a29e] hover:text-[#1a1a1a] dark:hover:text-[#e7e5e4] transition-colors disabled:opacity-50"
        >
          <motion.div
            animate={refreshing ? { rotate: 360 } : { rotate: 0 }}
            transition={{ duration: 0.8, ease: 'linear', repeat: refreshing ? Infinity : 0 }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </motion.div>
        </motion.button>
      </div>

      {/* Topic pills */}
      <div className="px-4 py-2.5 border-b border-[#f5f3ef] dark:border-[#44403c] flex gap-1.5 overflow-x-auto scrollbar-none">
        {TOPICS.map((t) => (
          <button
            key={t}
            onClick={() => setTopic(t)}
            className={`flex-shrink-0 text-[10px] font-medium px-2.5 py-1 rounded-full transition-all ${
              topic === t
                ? 'bg-[#d97757] text-white'
                : 'bg-[#f5f3ef] dark:bg-[#292524] text-[#3a3a3a] dark:text-[#a8a29e] hover:bg-[#ede9e2] dark:hover:bg-[#44403c]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Articles */}
      <div className="divide-y divide-[#f5f3ef] dark:divide-[#44403c]">
        {loading && (
          <div className="px-5 py-8 flex flex-col gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="space-y-1.5 animate-pulse">
                <div className="h-3 bg-[#f5f3ef] dark:bg-[#292524] rounded w-full" />
                <div className="h-3 bg-[#f5f3ef] dark:bg-[#292524] rounded w-3/4" />
                <div className="h-2 bg-[#f5f3ef] dark:bg-[#292524] rounded w-1/3 mt-1" />
              </div>
            ))}
          </div>
        )}

        {error && !loading && (
          <div className="px-5 py-6 flex items-start gap-2 text-xs text-[#6a6a6a] dark:text-[#a8a29e]">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-400" />
            {error}
          </div>
        )}

        {!loading && !error && articles.length === 0 && (
          <div className="px-5 py-6 text-xs text-[#6a6a6a] dark:text-[#a8a29e] text-center">
            No articles found for "{topic}"
          </div>
        )}

        <AnimatePresence>
          {!loading && articles.map((article, i) => (
            <motion.div
              key={article.url || i}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="group"
            >
              <button
                onClick={() => onSelectArticle(buildArticleText(article))}
                className="w-full text-left px-5 py-3.5 hover:bg-[#faf9f7] dark:hover:bg-[#292524] transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs text-[#1a1a1a] dark:text-[#e7e5e4] leading-relaxed line-clamp-2 flex-1">
                    {article.title}
                  </p>
                  <ChevronRight className="w-3 h-3 text-[#c8bfb0] dark:text-[#78716c] group-hover:text-[#d97757] flex-shrink-0 mt-0.5 transition-colors" />
                </div>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-[10px] text-[#6a6a6a] dark:text-[#a8a29e] font-medium">
                    {article.source}
                  </span>
                  <span className="text-[10px] text-[#c8bfb0] dark:text-[#78716c]">·</span>
                  <span className="text-[10px] text-[#c8bfb0] dark:text-[#78716c]">
                    {timeAgo(article.published_at)}
                  </span>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="ml-auto text-[#c8bfb0] dark:text-[#78716c] hover:text-[#d97757] transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

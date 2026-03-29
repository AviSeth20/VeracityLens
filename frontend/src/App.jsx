import React, { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useLocation } from 'react-router-dom'

import Header from './components/Header'
import Footer from './components/Footer'
import AnalysisInput from './components/AnalysisInput'
import ResultCard from './components/ResultCard'
import LoadingSkeleton from './components/LoadingSkeleton'
import ModelSelector from './components/ModelSelector'
import StatsBar from './components/StatsBar'
import LiveNewsFeed from './components/LiveNewsFeed'
import { analyzeNews, analyzeEnsemble, getStats, pingApi } from './services/api'

export default function App() {
  const location = useLocation()
  const [input, setInput]         = useState('')
  const [model, setModel]         = useState('distilbert')
  const [result, setResult]       = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError]         = useState(null)
  const [stats, setStats]         = useState(null)

  // Pre-fill from Live News page "Analyze" button
  useEffect(() => {
    if (location.state?.prefill) {
      setInput(location.state.prefill)
      setResult(null)
      window.history.replaceState({}, '')
    }
  }, [location.state])

  useEffect(() => {
    pingApi()
    getStats().then(setStats).catch(() => {})
  }, [])

  const handleAnalyze = async () => {
    if (!input.trim()) return
    setIsLoading(true)
    setResult(null)
    setError(null)
    try {
      // Call analyzeEnsemble() when ensemble is selected
      const data = model === 'ensemble' 
        ? await analyzeEnsemble(input)
        : await analyzeNews(input, model)
      setResult({ ...data, _text: input })
      // Refresh stats after a prediction
      getStats().then(setStats).catch(() => {})
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Is the API running?')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClear = () => {
    setInput('')
    setResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-[#faf9f7] dark:bg-[#0c0a09] flex flex-col transition-colors duration-200">
      <Header />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-10">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-[#1a1a1a] dark:text-[#fafaf9] tracking-tight mb-3">
            Detect Fake News with{' '}
            <span className="text-[#d97757]">AI Precision</span>
          </h2>
          <p className="text-[#3a3a3a] dark:text-[#d6d3d1] text-base max-w-xl mx-auto leading-relaxed">
            Transformer models analyze news content to identify truth, misinformation,
            satire, and bias — with token-level explainability.
          </p>
        </motion.div>

        {/* Stats */}
        <div className="mb-6">
          <StatsBar stats={stats} />
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Left: input + result */}
          <div className="lg:col-span-2 space-y-5">
            <ModelSelector selected={model} onChange={setModel} />

            <AnalysisInput
              value={input}
              onChange={setInput}
              onAnalyze={handleAnalyze}
              onClear={handleClear}
              isLoading={isLoading}
            />

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Result / skeleton */}
            <AnimatePresence mode="wait">
              {isLoading && (
                <motion.div key="skeleton">
                  <LoadingSkeleton message={model === 'ensemble' ? 'Running 3 models...' : undefined} />
                </motion.div>
              )}
              {!isLoading && result && (
                <motion.div key="result">
                  <ResultCard result={result} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: live news */}
          <div className="lg:col-span-1">
            <LiveNewsFeed onSelectArticle={(text) => { setInput(text); setResult(null) }} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

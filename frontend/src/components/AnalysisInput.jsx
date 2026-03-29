import React, { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Zap, RotateCcw, Link } from 'lucide-react'

const SAMPLES = [
  {
    label: 'True News',
    text: 'Scientists announce breakthrough in renewable energy storage technology, promising to revolutionize solar power efficiency by 40%.',
  },
  {
    label: 'Fake News',
    text: 'Local mayor reveals shocking conspiracy involving aliens controlling city council meetings. Watch this exclusive interview!',
  },
  {
    label: 'Satire',
    text: 'Nation\'s Economists Recommend Just Spending Less Money On Things That Cost Money.',
  },
  {
    label: 'Bias',
    text: 'The radical left-wing government once again destroys the economy with reckless spending that only benefits their elite donors.',
  },
]

export default function AnalysisInput({ value, onChange, onAnalyze, onClear, isLoading }) {
  const textareaRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 280) + 'px'
  }, [value])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="bg-white dark:bg-[#1c1917] rounded-2xl border border-[#ede9e2] dark:border-[#44403c] shadow-sm overflow-hidden"
    >
      {/* Card header */}
      <div className="px-6 pt-5 pb-4 border-b border-[#f5f3ef] dark:border-[#44403c]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#d97757]" />
          <span className="text-sm font-medium text-[#1a1a1a] dark:text-[#fafaf9]">Analyze News Content</span>
        </div>
        <p className="text-xs text-[#6a6a6a] dark:text-[#a8a29e] mt-1">
          Paste a news article, headline, or claim to verify
        </p>
      </div>

      {/* Textarea */}
      <div className="px-6 pt-4 pb-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste news article, headline, or claim here…"
          rows={4}
          className="w-full resize-none bg-transparent text-[15px] text-[#1a1a1a] dark:text-[#fafaf9] placeholder-[#b0a494] dark:placeholder-[#78716c] outline-none leading-relaxed scrollbar-thin"
          style={{ minHeight: '100px' }}
        />
      </div>

      {/* Actions */}
      <div className="px-6 pb-5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={onAnalyze}
            disabled={isLoading || !value.trim()}
            className="flex items-center gap-2 bg-[#d97757] hover:bg-[#c4623e] disabled:bg-[#ddd7cc] disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors shadow-sm"
          >
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex items-center gap-2"
                >
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing…</span>
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex items-center gap-2"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Analyze</span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={onClear}
            className="flex items-center gap-1.5 text-sm text-[#6a6a6a] dark:text-[#a8a29e] hover:text-[#1a1a1a] dark:hover:text-gray-100 px-3 py-2.5 rounded-xl hover:bg-[#f5f3ef] dark:hover:bg-gray-800 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear</span>
          </motion.button>
        </div>

        <span className="text-xs text-[#b0a494] dark:text-gray-500">
          {value.length > 0 ? `${value.length} chars` : ''}
        </span>
      </div>

      {/* Sample inputs */}
      <AnimatePresence>
        {!value && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-[#f5f3ef] dark:border-[#44403c] px-6 py-4"
          >
            <p className="text-xs text-[#6a6a6a] dark:text-[#a8a29e] mb-3 font-medium uppercase tracking-wide">
              Try a sample
            </p>
            <div className="grid grid-cols-2 gap-2">
              {SAMPLES.map((s, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ backgroundColor: '#f5f3ef', borderColor: '#c8bfb0' }}
                  onClick={() => onChange(s.text)}
                  className="text-left p-3 border border-[#ede9e2] dark:border-[#57534e] rounded-xl transition-colors dark:hover:bg-gray-800"
                >
                  <div className="text-xs font-medium text-[#3a3a3a] dark:text-[#d6d3d1] mb-1">{s.label}</div>
                  <div className="text-xs text-[#6a6a6a] dark:text-[#a8a29e] line-clamp-2 leading-relaxed">
                    {s.text}
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

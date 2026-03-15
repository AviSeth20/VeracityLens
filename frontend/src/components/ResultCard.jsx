import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle, AlertTriangle, Zap, Eye,
  BarChart2, MessageSquare, Send, X, ThumbsUp,
  Lightbulb, Loader2, Brain
} from 'lucide-react'
import { submitFeedback, explainPrediction } from '../services/api'

const CONFIG = {
  True:   { icon: CheckCircle,  color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', badge: 'bg-emerald-100 text-emerald-700', bar: 'bg-emerald-500', label: 'Verified True' },
  Fake:   { icon: AlertTriangle,color: '#dc2626', bg: '#fef2f2', border: '#fecaca', badge: 'bg-red-100 text-red-700',     bar: 'bg-red-500',     label: 'Likely Fake' },
  Satire: { icon: Zap,          color: '#7c3aed', bg: '#faf5ff', border: '#e9d5ff', badge: 'bg-violet-100 text-violet-700',bar: 'bg-violet-500',  label: 'Satire' },
  Bias:   { icon: Eye,          color: '#d97706', bg: '#fffbeb', border: '#fde68a', badge: 'bg-amber-100 text-amber-700',  bar: 'bg-amber-500',   label: 'Biased Content' },
}

const LABELS = ['True', 'Fake', 'Satire', 'Bias']
const TABS   = ['Prediction', 'Probabilities', 'Explain']

function ConfidenceBar({ value, barClass }) {
  return (
    <div className="w-full bg-[#ede9e2] rounded-full h-1.5 overflow-hidden">
      <motion.div
        initial={{ width: 0 }} animate={{ width: `${value}%` }}
        transition={{ duration: 0.9, ease: 'easeOut', delay: 0.3 }}
        className={`h-full rounded-full ${barClass}`}
      />
    </div>
  )
}

/* ── Inline highlighted text (used for both attention and SHAP) ──────────── */
function HighlightedText({ words, getColor }) {
  if (!words || words.length === 0) return null
  return (
    <div className="text-sm leading-8 text-[#1a1a1a] select-text whitespace-normal break-words">
      {words.map((w, i) => {
        const { bg, title } = getColor(w)
        return (
          <span
            key={i}
            title={title}
            style={{ backgroundColor: bg }}
            className="rounded px-0.5 mx-[2px] cursor-default"
          >
            {w.word}
          </span>
        )
      })}
    </div>
  )
}

/* ── Explain tab ─────────────────────────────────────────────────────────── */
function ExplainTab({ result, cfg }) {
  const [attention, setAttention]     = useState(null)
  const [shap, setShap]               = useState(null)
  const [shapText, setShapText]       = useState('')
  const [loadingAttn, setLoadingAttn] = useState(false)
  const [loadingShap, setLoadingShap] = useState(false)
  const [attnError, setAttnError]     = useState(null)
  const [shapError, setShapError]     = useState(null)

  const text = result._text || ''

  const loadAttention = async () => {
    if (attention || loadingAttn) return
    setLoadingAttn(true)
    setAttnError(null)
    try {
      const data = await explainPrediction(text, result.model_used, false)
      setAttention(data.attention || [])
    } catch {
      setAttnError('Failed to load attention data.')
    } finally {
      setLoadingAttn(false)
    }
  }

  const loadShap = async () => {
    if (loadingShap) return
    setLoadingShap(true)
    setShapError(null)
    try {
      const data = await explainPrediction(text, result.model_used, true)
      setShap(data.shap || [])
      setShapText(data.explanation_text || '')
    } catch {
      setShapError('SHAP explanation failed.')
    } finally {
      setLoadingShap(false)
    }
  }

  // Auto-load attention on mount
  React.useEffect(() => { if (text) loadAttention() }, [text])

  return (
    <div className="space-y-4">
      {/* Attention section */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Lightbulb className="w-3.5 h-3.5 text-[#8a8a8a]" />
          <span className="text-xs font-medium text-[#5a5a5a] uppercase tracking-wide">Attention Highlights</span>
        </div>
        {loadingAttn && (
          <div className="flex items-center gap-2 text-xs text-[#8a8a8a]">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading…
          </div>
        )}
        {attnError && <p className="text-xs text-red-500">{attnError}</p>}
        {attention && attention.length > 0 && (
          <HighlightedText
            words={attention}
            getColor={(w) => {
              const alpha = Math.round(w.attention * 200).toString(16).padStart(2, '0')
              return {
                bg: `${cfg.color}${alpha}`,
                title: `attention: ${(w.attention * 100).toFixed(1)}%`,
              }
            }}
          />
        )}
        {attention && attention.length === 0 && (
          <p className="text-xs text-[#8a8a8a]">No attention data available.</p>
        )}
      </div>

      {/* SHAP section */}
      <div className="border-t border-[#ede9e2]/60 pt-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Brain className="w-3.5 h-3.5 text-[#8a8a8a]" />
            <span className="text-xs font-medium text-[#5a5a5a] uppercase tracking-wide">Deep SHAP Explanation</span>
          </div>
          {!shap && (
            <button
              onClick={loadShap}
              disabled={loadingShap || !text}
              className="flex items-center gap-1.5 text-xs bg-[#1a1a1a] hover:bg-[#333] disabled:bg-[#ddd7cc] disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              {loadingShap
                ? <><Loader2 className="w-3 h-3 animate-spin" /> Running…</>
                : <><Brain className="w-3 h-3" /> Explain Deeply</>
              }
            </button>
          )}
        </div>
        {!shap && !loadingShap && (
          <p className="text-xs text-[#8a8a8a]">Click "Explain Deeply" to run SHAP analysis using RoBERTa (~15s on CPU).</p>
        )}
        {shapError && <p className="text-xs text-red-500">{shapError}</p>}
        {shapText && (
          <motion.p
            initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-sm text-[#3a3a3a] leading-relaxed bg-white/60 rounded-xl px-4 py-3 border border-[#ede9e2]"
          >
            {shapText}
          </motion.p>
        )}
        {shap && shap.length === 0 && <p className="text-xs text-[#8a8a8a]">No SHAP data returned.</p>}
      </div>
    </div>
  )
}

/* ── Feedback panel ──────────────────────────────────────────────────────── */
function FeedbackPanel({ articleId, predictedLabel }) {
  const [open, setOpen]       = useState(false)
  const [selected, setSelected] = useState(null)
  const [comment, setComment] = useState('')
  const [status, setStatus]   = useState('idle')

  const handleSubmit = async () => {
    if (!selected) return
    setStatus('submitting')
    try {
      await submitFeedback(articleId, predictedLabel, selected, comment)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'done') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        className="flex items-center gap-2 text-sm text-emerald-600 px-6 pb-5">
        <ThumbsUp className="w-4 h-4" />
        Thanks — feedback recorded.
      </motion.div>
    )
  }

  return (
    <div className="px-6 pb-5">
      <div className="border-t border-[#ede9e2]/60 pt-4">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-2 text-xs text-[#8a8a8a] hover:text-[#1a1a1a] transition-colors"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          {open ? 'Hide feedback' : 'Was this prediction correct?'}
          {open && <X className="w-3 h-3 ml-1" />}
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }} className="overflow-hidden"
            >
              <div className="pt-3 space-y-3">
                <div>
                  <p className="text-xs text-[#5a5a5a] mb-2">What is the correct label?</p>
                  <div className="flex flex-wrap gap-2">
                    {LABELS.map((label) => (
                      <button
                        key={label}
                        onClick={() => setSelected(label)}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                          selected === label
                            ? 'border-[#d97757] bg-[#fff5f2] text-[#d97757] font-medium'
                            : 'border-[#ede9e2] text-[#5a5a5a] hover:border-[#c8bfb0]'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <textarea
                  value={comment} onChange={(e) => setComment(e.target.value)}
                  placeholder="Optional comment…" rows={2}
                  className="w-full text-xs text-[#1a1a1a] placeholder-[#b0a494] bg-white border border-[#ede9e2] rounded-lg px-3 py-2 resize-none outline-none focus:border-[#d97757] transition-colors"
                />
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSubmit}
                    disabled={!selected || status === 'submitting'}
                    className="flex items-center gap-1.5 text-xs bg-[#d97757] hover:bg-[#c4623e] disabled:bg-[#ddd7cc] disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    <Send className="w-3 h-3" />
                    {status === 'submitting' ? 'Sending…' : 'Submit'}
                  </button>
                  {status === 'error' && (
                    <span className="text-xs text-red-500">Failed to submit. Try again.</span>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

/* ── Main ResultCard ─────────────────────────────────────────────────────── */
export default function ResultCard({ result }) {
  const [activeTab, setActiveTab] = useState('Prediction')

  const label      = result.label || result.category
  const confidence = result.confidence != null
    ? Math.round(result.confidence * 100)
    : result.confidence_pct ?? result.confidence

  const cfg    = CONFIG[label] || CONFIG.True
  const Icon   = cfg.icon
  const scores = result.scores || {}

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="rounded-2xl border overflow-hidden shadow-sm"
      style={{ borderColor: cfg.border, backgroundColor: cfg.bg }}
    >
      {/* Top accent bar */}
      <motion.div
        initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        style={{ backgroundColor: cfg.color, transformOrigin: 'left' }}
        className="h-1 w-full"
      />

      {/* Header */}
      <div className="px-6 pt-5 pb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ scale: 0, rotate: -20 }} animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 18, delay: 0.1 }}
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${cfg.color}18` }}
          >
            <Icon className="w-5 h-5" style={{ color: cfg.color }} />
          </motion.div>
          <div>
            <motion.h3
              initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
              className="font-semibold text-[#1a1a1a] text-base"
            >
              {cfg.label}
            </motion.h3>
            <div className="flex items-center gap-2 mt-0.5">
              <motion.span
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.badge}`}
              >
                {label}
              </motion.span>
              {result.model_used && (
                <span className="text-[10px] text-[#8a8a8a] bg-white border border-[#ede9e2] px-2 py-0.5 rounded-full">
                  {result.model_used}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Confidence */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          className="text-right flex-shrink-0"
        >
          <div className="text-3xl font-bold text-[#1a1a1a] tabular-nums">
            {confidence}<span className="text-lg font-medium text-[#8a8a8a]">%</span>
          </div>
          <div className="text-[11px] text-[#8a8a8a] mt-0.5">confidence</div>
          <div className="w-24 mt-2">
            <ConfidenceBar value={confidence} barClass={cfg.bar} />
          </div>
        </motion.div>
      </div>

      {/* Tabs */}
      <div className="px-6">
        <div className="flex gap-1 border-b border-[#ede9e2]">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`text-xs px-3 py-2 border-b-2 transition-colors -mb-px ${
                activeTab === tab
                  ? 'border-[#d97757] text-[#d97757] font-medium'
                  : 'border-transparent text-[#8a8a8a] hover:text-[#1a1a1a]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="px-6 py-4">
        <AnimatePresence mode="wait">
          {activeTab === 'Prediction' && (
            <motion.div key="pred"
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}
            >
              <p className="text-sm text-[#5a5a5a]">
                The model classified this article as{' '}
                <span className="text-[#1a1a1a] font-medium">{cfg.label}</span> with{' '}
                <span className="text-[#1a1a1a] font-medium">{confidence}%</span> confidence
                {result.model_used && (
                  <> using {result.model_used}</>
                )}.
              </p>
            </motion.div>
          )}

          {activeTab === 'Probabilities' && (
            <motion.div key="probs"
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}
            >
              {Object.keys(scores).length > 0 ? (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart2 className="w-4 h-4 text-[#8a8a8a]" />
                    <span className="text-xs font-medium text-[#5a5a5a] uppercase tracking-wide">Class Probabilities</span>
                  </div>
                  {Object.entries(scores)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cls, prob], i) => {
                      const c = CONFIG[cls] || CONFIG.True
                      return (
                        <motion.div key={cls}
                          initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.07 }}
                          className="flex items-center gap-3"
                        >
                          <span className="text-xs text-[#5a5a5a] w-12 flex-shrink-0">{cls}</span>
                          <div className="flex-1 bg-[#ede9e2] rounded-full h-1.5 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }} animate={{ width: `${prob * 100}%` }}
                              transition={{ duration: 0.7, ease: 'easeOut', delay: 0.1 + i * 0.07 }}
                              className={`h-full rounded-full ${c.bar}`}
                            />
                          </div>
                          <span className="text-xs tabular-nums text-[#8a8a8a] w-10 text-right">
                            {(prob * 100).toFixed(1)}%
                          </span>
                        </motion.div>
                      )
                    })}
                </div>
              ) : (
                <p className="text-xs text-[#8a8a8a]">No probability data available.</p>
              )}
            </motion.div>
          )}

          {activeTab === 'Explain' && (
            <motion.div key="explain"
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}
            >
              <ExplainTab result={result} cfg={cfg} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Feedback */}
      <FeedbackPanel articleId={result.article_id} predictedLabel={label} />
    </motion.div>
  )
}

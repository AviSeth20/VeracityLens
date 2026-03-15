import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, AlertTriangle, Zap, Eye } from 'lucide-react'

const DEFS = [
  { label: 'True',   icon: CheckCircle,  color: '#16a34a', bg: '#f0fdf4' },
  { label: 'Fake',   icon: AlertTriangle, color: '#dc2626', bg: '#fef2f2' },
  { label: 'Satire', icon: Zap,          color: '#7c3aed', bg: '#faf5ff' },
  { label: 'Bias',   icon: Eye,          color: '#d97706', bg: '#fffbeb' },
]

function fmt(n) {
  if (n == null) return '—'
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

export default function StatsBar({ stats }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="grid grid-cols-2 sm:grid-cols-4 gap-3"
    >
      {DEFS.map((s, i) => {
        const Icon  = s.icon
        const count = stats?.by_label?.[s.label] ?? null
        return (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + i * 0.08 }}
            whileHover={{ y: -2, boxShadow: '0 4px 16px rgba(0,0,0,0.06)' }}
            className="bg-white border border-[#ede9e2] rounded-xl px-4 py-3 flex items-center gap-3 cursor-default transition-shadow"
          >
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: s.bg }}
            >
              <Icon className="w-4 h-4" style={{ color: s.color }} />
            </div>
            <div>
              <div className="text-base font-semibold text-[#1a1a1a] tabular-nums">
                {fmt(count)}
              </div>
              <div className="text-[11px] text-[#8a8a8a]">{s.label}</div>
            </div>
          </motion.div>
        )
      })}
    </motion.div>
  )
}

import React from 'react'
import { motion } from 'framer-motion'
import { Cpu } from 'lucide-react'

const MODELS = [
  { id: 'distilbert', label: 'DistilBERT', desc: '66M · Fast', badge: 'Recommended' },
  { id: 'roberta', label: 'RoBERTa', desc: '125M · Accurate', badge: null },
  { id: 'xlnet', label: 'XLNet', desc: '110M · Context-aware', badge: null },
]

export default function ModelSelector({ selected, onChange }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="bg-white border border-[#ede9e2] rounded-2xl px-5 py-4 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-3">
        <Cpu className="w-4 h-4 text-[#8a8a8a]" />
        <span className="text-xs font-medium text-[#5a5a5a] uppercase tracking-wide">
          Model
        </span>
      </div>
      <div className="flex gap-2 flex-wrap">
        {MODELS.map((m) => (
          <motion.button
            key={m.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onChange(m.id)}
            className={`relative flex flex-col items-start px-4 py-2.5 rounded-xl border text-left transition-all ${
              selected === m.id
                ? 'border-[#d97757] bg-[#fff5f2] shadow-sm'
                : 'border-[#ede9e2] hover:border-[#c8bfb0] hover:bg-[#faf9f7]'
            }`}
          >
            {m.badge && (
              <span className="absolute -top-2 -right-1 text-[9px] font-semibold bg-[#d97757] text-white px-1.5 py-0.5 rounded-full">
                {m.badge}
              </span>
            )}
            <span
              className={`text-sm font-medium ${
                selected === m.id ? 'text-[#d97757]' : 'text-[#1a1a1a]'
              }`}
            >
              {m.label}
            </span>
            <span className="text-[11px] text-[#8a8a8a] mt-0.5">{m.desc}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

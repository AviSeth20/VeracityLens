import React from 'react'
import { motion } from 'framer-motion'
import { Brain, Github } from 'lucide-react'

export default function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8 }}
      className="border-t border-[#ede9e2] bg-white/60 backdrop-blur-sm mt-16"
    >
      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-[#d97757] rounded-lg flex items-center justify-center">
            <Brain className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-sm font-medium text-[#5a5a5a]">VeracityLens</span>
        </div>

        <p className="text-xs text-[#8a8a8a] text-center">
          Powered by DistilBERT · RoBERTa · XLNet &nbsp;·&nbsp; Explainable AI
        </p>

        <a
          href="https://github.com/AviSeth20/fake-news-detection"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs text-[#8a8a8a] hover:text-[#1a1a1a] transition-colors"
        >
          <Github className="w-3.5 h-3.5" />
          <span>GitHub</span>
        </a>
      </div>
    </motion.footer>
  )
}

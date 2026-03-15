import React from 'react'
import { motion } from 'framer-motion'

function SkeletonLine({ width = 'w-full', height = 'h-3' }) {
  return (
    <div className={`${width} ${height} rounded-full shimmer-bg`} />
  )
}

export default function LoadingSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-2xl border border-[#ede9e2] shadow-sm overflow-hidden"
    >
      {/* Top accent bar shimmer */}
      <div className="h-1 w-full shimmer-bg" />

      <div className="px-6 pt-5 pb-4 flex items-start justify-between gap-4">
        {/* Left: icon + label */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl shimmer-bg flex-shrink-0" />
          <div className="space-y-2">
            <SkeletonLine width="w-28" height="h-4" />
            <SkeletonLine width="w-16" height="h-3" />
          </div>
        </div>
        {/* Right: score */}
        <div className="text-right space-y-2">
          <SkeletonLine width="w-16" height="h-8" />
          <SkeletonLine width="w-24" height="h-1.5" />
        </div>
      </div>

      <div className="mx-6 border-t border-[#f5f3ef]" />

      <div className="px-6 py-4 space-y-2">
        <SkeletonLine width="w-32" height="h-3" />
        <SkeletonLine />
        <SkeletonLine width="w-4/5" />
      </div>

      <div className="px-6 pb-4 space-y-2">
        <SkeletonLine width="w-36" height="h-3" />
        <SkeletonLine />
        <SkeletonLine width="w-3/4" />
      </div>

      <div className="px-6 pb-5">
        <SkeletonLine width="w-32" height="h-3" />
        <div className="grid grid-cols-3 gap-2 mt-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-9 rounded-lg shimmer-bg" />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

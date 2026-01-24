'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ActivityItem } from '@/lib/types';

interface ActivityFeedProps {
  activities: ActivityItem[];
  isLoading?: boolean;
}

// Skeleton item component
function SkeletonItem({ index }: { index: number }) {
  const widths = ['w-3/4', 'w-2/3', 'w-4/5', 'w-1/2', 'w-3/5'];
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-start gap-2 py-1 px-1 -mx-1"
    >
      {/* Timestamp skeleton */}
      <div className="shrink-0 w-[72px] h-4 bg-[#21262d] rounded animate-pulse" />

      {/* Type indicator skeleton */}
      <div className="shrink-0 w-14 h-4 bg-[#21262d] rounded animate-pulse" />

      {/* Message skeleton */}
      <div className={`h-4 bg-[#21262d] rounded animate-pulse ${widths[index % widths.length]}`} />
    </motion.div>
  );
}

export function ActivityFeed({ activities, isLoading = false }: ActivityFeedProps) {
  const { t } = useI18n();

  const typeStyles: Record<string, { color: string; prefix: string; icon: string }> = {
    trend: { color: 'text-[#00ffff]', prefix: 'SIGNAL', icon: '◈' },
    idea: { color: 'text-[#f1fa8c]', prefix: 'IDEA', icon: '◆' },
    plan: { color: 'text-[#bd93f9]', prefix: 'PLAN', icon: '◇' },
    debate: { color: 'text-[#ff6b35]', prefix: 'DEBATE', icon: '◉' },
    dev: { color: 'text-[#39ff14]', prefix: 'DEV', icon: '●' },
    system: { color: 'text-[#6b7280]', prefix: 'SYS', icon: '○' },
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[#bd93f9] text-xs">#</span>
          <span className="text-[#6b7280] text-xs">Real-time activity stream</span>
        </div>
        <motion.div
          className="flex items-center gap-1.5"
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="status-dot online" style={{ width: 6, height: 6 }} />
          <span className="text-[10px] text-[#39ff14] uppercase tracking-wider">
            {t('activity.streaming')}
          </span>
        </motion.div>
      </div>

      {/* Activity log */}
      <div className="h-64 overflow-y-auto text-xs space-y-0.5">
        {isLoading ? (
          // Skeleton loading state
          <>
            {Array.from({ length: 8 }).map((_, index) => (
              <SkeletonItem key={index} index={index} />
            ))}
          </>
        ) : (
          // Real data
          activities.map((activity, index) => {
            const style = typeStyles[activity.type] || typeStyles.system;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className="flex items-start gap-2 py-1 hover:bg-[#21262d]/50 px-1 -mx-1 transition-colors"
              >
                {/* Timestamp */}
                <span className="text-[#6b7280] shrink-0 tabular-nums">
                  [{activity.time}]
                </span>

                {/* Type indicator */}
                <span className={`${style.color} shrink-0 w-14 flex items-center gap-1`}>
                  <span>{style.icon}</span>
                  <span className="uppercase text-[10px] tracking-wide">{style.prefix}</span>
                </span>

                {/* Message */}
                <span className="text-[#c0c0c0] flex-1">
                  {activity.message}
                </span>
              </motion.div>
            );
          })
        )}

        {/* Cursor */}
        <motion.div
          className="flex items-center gap-2 py-1 text-[#39ff14]"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          <span className="text-[#6b7280]">[--:--:--]</span>
          <span>▋</span>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="mt-3 pt-2 border-t border-[#21262d] flex items-center justify-between text-[10px]">
        <span className="text-[#6b7280]">
          {isLoading ? 'Loading events...' : `Showing last ${activities.length} events`}
        </span>
        <div className="flex items-center gap-3">
          {Object.entries(typeStyles).slice(0, 4).map(([key, style]) => (
            <span key={key} className={`${style.color} flex items-center gap-1`}>
              <span>{style.icon}</span>
              <span className="uppercase">{key}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

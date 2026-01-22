'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { PipelineStage } from '@/lib/types';

interface PipelineProps {
  stages: PipelineStage[];
}

export function Pipeline({ stages }: PipelineProps) {
  const { t } = useI18n();

  const statusColors = {
    active: {
      border: 'border-[#39ff14]',
      bg: 'bg-[#39ff14]/10',
      text: 'text-[#39ff14]',
      glow: 'shadow-[0_0_15px_rgba(57,255,20,0.3)]',
    },
    completed: {
      border: 'border-[#6b7280]',
      bg: 'bg-[#21262d]',
      text: 'text-[#c0c0c0]',
      glow: '',
    },
    idle: {
      border: 'border-[#21262d]',
      bg: 'bg-[#0d1117]',
      text: 'text-[#6b7280]',
      glow: '',
    },
  };

  return (
    <div className="card-cli p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-[#00ffff] text-xs">$</span>
          <span className="text-[#c0c0c0] text-xs">moss-ao pipeline --status</span>
        </div>
        <span className="tag tag-green">RUNNING</span>
      </div>

      {/* Pipeline visualization */}
      <div className="overflow-x-auto pb-2">
        <div className="flex items-center justify-center gap-2 min-w-max px-4">
          {stages.map((stage, index) => {
            const colors = statusColors[stage.status] || statusColors.idle;

            return (
              <div key={stage.id} className="flex items-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={`
                    relative flex flex-col items-center justify-center
                    w-20 h-20 sm:w-24 sm:h-24
                    border ${colors.border} ${colors.bg}
                    transition-all duration-300
                    ${stage.status === 'active' ? colors.glow : ''}
                  `}
                >
                  {/* Active indicator */}
                  {stage.status === 'active' && (
                    <motion.div
                      className="absolute inset-0 border border-[#39ff14]"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  )}

                  {/* Count */}
                  <span className={`text-xl sm:text-2xl font-bold ${colors.text}`}>
                    {stage.count}
                  </span>

                  {/* Stage name */}
                  <span className="text-[10px] text-[#6b7280] mt-1 uppercase tracking-wider">
                    {stage.name}
                  </span>

                  {/* Status indicator */}
                  <div className={`
                    absolute -top-1 -right-1 w-2 h-2
                    ${stage.status === 'active' ? 'bg-[#39ff14]' : 'bg-[#21262d]'}
                  `}>
                    {stage.status === 'active' && (
                      <motion.div
                        className="absolute inset-0 bg-[#39ff14]"
                        animate={{ scale: [1, 1.5, 1], opacity: [1, 0, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      />
                    )}
                  </div>
                </motion.div>

                {/* Connector */}
                {index < stages.length - 1 && (
                  <div className="relative w-8 sm:w-12 h-0.5 bg-[#21262d] mx-1">
                    {stage.status === 'active' && (
                      <motion.div
                        className="absolute inset-y-0 left-0 bg-[#39ff14]"
                        initial={{ width: 0 }}
                        animate={{ width: '100%' }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          ease: 'linear',
                        }}
                      />
                    )}
                    <motion.div
                      className="absolute top-1/2 h-1.5 w-1.5 -translate-y-1/2 bg-[#39ff14]"
                      animate={{ x: [0, 32, 0] }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'linear',
                      }}
                      style={{ display: stage.status === 'active' ? 'block' : 'none' }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-[#21262d] flex flex-wrap justify-center gap-4 text-[10px]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-[#39ff14]" />
          <span className="text-[#6b7280] uppercase tracking-wider">{t('pipeline.active')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-[#6b7280]" />
          <span className="text-[#6b7280] uppercase tracking-wider">{t('pipeline.completed')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 border border-[#21262d]" />
          <span className="text-[#6b7280] uppercase tracking-wider">{t('pipeline.idle')}</span>
        </div>
      </div>
    </div>
  );
}

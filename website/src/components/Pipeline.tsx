'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { useModal } from '@/components/modals/useModal';
import { ApiClient, type PipelineLiveResponse } from '@/lib/api';
import type { PipelineStage } from '@/lib/types';

interface PipelineProps {
  stages: PipelineStage[];
}

export function Pipeline({ stages }: PipelineProps) {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [liveData, setLiveData] = useState<PipelineLiveResponse | null>(null);
  const [isLive, setIsLive] = useState(false);

  // Fetch live pipeline data
  useEffect(() => {
    async function fetchLive() {
      const response = await ApiClient.getPipelineLive();
      if (response.data) {
        setLiveData(response.data);
        setIsLive(true);
      }
    }

    fetchLive();
    const interval = setInterval(fetchLive, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleStageClick = (stage: PipelineStage) => {
    openModal('pipeline', {
      id: `pipeline-${stage.id}`,
      title: `${stage.name} Pipeline`,
      stageId: stage.id,
      stageName: stage.name,
      count: stage.count,
      status: stage.status,
    });
  };

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

  // Use live data if available, otherwise fall back to props
  const displayStages = liveData ? [
    {
      id: 'signals',
      name: 'Signals',
      count: liveData.stages.signals.count,
      status: liveData.stages.signals.status as 'active' | 'completed' | 'idle',
      rate: liveData.stages.signals.rate,
    },
    {
      id: 'trends',
      name: 'Trends',
      count: liveData.stages.trends.count,
      status: liveData.stages.trends.status as 'active' | 'completed' | 'idle',
      rate: liveData.stages.trends.rate,
    },
    {
      id: 'ideas',
      name: 'Ideas',
      count: liveData.stages.ideas.count,
      status: liveData.stages.ideas.status as 'active' | 'completed' | 'idle',
      rate: liveData.stages.ideas.rate,
    },
    {
      id: 'plans',
      name: 'Plans',
      count: liveData.stages.plans.count,
      status: liveData.stages.plans.status as 'active' | 'completed' | 'idle',
      rate: liveData.stages.plans.rate,
    },
    {
      id: 'projects',
      name: 'Projects',
      count: liveData.stages.projects?.count || 0,
      status: (liveData.stages.projects?.status || 'idle') as 'active' | 'completed' | 'idle',
      rate: liveData.stages.projects?.rate || '',
    },
  ] : [...stages.map(s => ({ ...s, rate: '' })), { id: 'projects', name: 'Projects', count: 0, status: 'idle' as const, rate: '' }];

  const conversionRates = liveData?.conversion_rates;

  return (
    <div className="card-cli p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-[#00ffff] text-xs">$</span>
          <span className="text-[#c0c0c0] text-xs">moss-ao pipeline --status</span>
        </div>
        <div className="flex items-center gap-2">
          {isLive && (
            <motion.span
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-[#39ff14] text-xs flex items-center gap-1"
            >
              <span className="w-1.5 h-1.5 bg-[#39ff14] rounded-full" />
              LIVE
            </motion.span>
          )}
          <span className="tag tag-green">RUNNING</span>
        </div>
      </div>

      {/* Pipeline visualization */}
      <div className="overflow-x-auto pb-2">
        <div className="flex items-center justify-center gap-2 min-w-max px-4">
          {displayStages.map((stage, index) => {
            const colors = statusColors[stage.status] || statusColors.idle;

            return (
              <div key={stage.id} className="flex items-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleStageClick(stage as PipelineStage)}
                  className={`
                    relative flex flex-col items-center justify-center
                    w-20 h-20 sm:w-24 sm:h-24
                    border ${colors.border} ${colors.bg}
                    transition-all duration-300 cursor-pointer
                    hover:border-[#39ff14]/50
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
                    {stage.count.toLocaleString()}
                  </span>

                  {/* Stage name */}
                  <span className="text-[10px] text-[#6b7280] mt-1 uppercase tracking-wider">
                    {stage.name}
                  </span>

                  {/* Rate badge */}
                  {stage.rate && (
                    <span className="text-[8px] text-[#39ff14] mt-0.5">
                      {stage.rate}
                    </span>
                  )}

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

                {/* Connector with conversion rate */}
                {index < displayStages.length - 1 && (
                  <div className="relative w-8 sm:w-12 mx-1">
                    <div className="h-0.5 bg-[#21262d]">
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
                    {/* Conversion rate label */}
                    {conversionRates && (
                      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[8px] text-[#6b7280] whitespace-nowrap">
                        {index === 0 && `${conversionRates.signals_to_trends}%`}
                        {index === 1 && `${conversionRates.trends_to_ideas}%`}
                        {index === 2 && `${conversionRates.ideas_to_plans}%`}
                        {index === 3 && `${conversionRates.plans_to_projects || 0}%`}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Conversion rates summary */}
      {conversionRates && (
        <div className="mt-6 pt-3 border-t border-[#21262d]">
          <div className="text-[10px] text-[#6b7280] text-center mb-2">
            {t('pipeline.conversionRates')}
          </div>
          <div className="flex justify-center items-center gap-2 text-xs text-[#c0c0c0]">
            <span>{conversionRates.signals_to_trends}%</span>
            <span className="text-[#39ff14]">→</span>
            <span>{conversionRates.trends_to_ideas}%</span>
            <span className="text-[#39ff14]">→</span>
            <span>{conversionRates.ideas_to_plans}%</span>
            <span className="text-[#39ff14]">→</span>
            <span>{conversionRates.plans_to_projects || 0}%</span>
          </div>
        </div>
      )}

      {/* Currently processing */}
      {liveData?.processing && liveData.processing.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[#21262d]">
          <div className="text-[10px] text-[#6b7280] uppercase tracking-wider mb-2">
            {t('pipeline.currentlyProcessing')}
          </div>
          <div className="space-y-1.5 max-h-24 overflow-y-auto">
            <AnimatePresence mode="popLayout">
              {liveData.processing.map((item, idx) => (
                <motion.div
                  key={`${item.type}-${item.title}-${idx}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="flex items-center gap-2 text-xs"
                >
                  <span className={`font-mono px-1.5 py-0.5 rounded text-[10px] ${
                    item.type === 'SIGNAL' ? 'bg-[#00ffff]/20 text-[#00ffff]' :
                    item.type === 'TREND' ? 'bg-[#bd93f9]/20 text-[#bd93f9]' :
                    item.type === 'DEBATE' ? 'bg-[#ff6b35]/20 text-[#ff6b35]' :
                    item.type === 'PROJECT' ? 'bg-[#bd93f9]/20 text-[#bd93f9]' :
                    'bg-[#39ff14]/20 text-[#39ff14]'
                  }`}>
                    [{item.type}]
                  </span>
                  <span className="text-[#c0c0c0] flex-1 truncate">{item.title}</span>
                  <span className="text-[#6b7280] text-[10px]">({item.time_ago})</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

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

'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';

interface SignalNode {
  id: string;
  title: string;
  score: number;
  source?: string;
}

interface TrendNode {
  id: string;
  name: string;
  score: number;
  signal_count: number;
}

interface IdeaNode {
  id: string;
  title: string;
  score: number;
  status: string;
}

interface PlanNode {
  id: string;
  title: string;
  version: number;
  status: string;
}

interface LineageData {
  signals: SignalNode[];
  trend?: TrendNode | null;
  idea: IdeaNode;
  plans: PlanNode[];
}

interface SignalLineageProps {
  lineage: LineageData;
  onNodeClick?: (type: string, id: string) => void;
}

export function SignalLineage({ lineage, onNodeClick }: SignalLineageProps) {
  const { t } = useI18n();

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-[#39ff14] border-[#39ff14]';
    if (score >= 6) return 'text-[#00ffff] border-[#00ffff]';
    if (score >= 4) return 'text-[#ff6b35] border-[#ff6b35]';
    return 'text-[#6b7280] border-[#6b7280]';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'promoted':
      case 'approved':
      case 'completed':
        return 'bg-[#39ff14]/20 text-[#39ff14]';
      case 'scored':
      case 'draft':
        return 'bg-[#00ffff]/20 text-[#00ffff]';
      case 'in-progress':
        return 'bg-[#ff6b35]/20 text-[#ff6b35]';
      default:
        return 'bg-[#6b7280]/20 text-[#6b7280]';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('signalLineage.title')}
        </span>
      </div>

      {/* Lineage Tree */}
      <div className="relative">
        {/* Signals Column */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
          {/* Signals */}
          <div className="space-y-2">
            <div className="text-[10px] text-[#00ffff] uppercase tracking-wider mb-2 flex items-center gap-1">
              <span>SIGNALS</span>
              <span className="text-[#6b7280]">({lineage.signals.length})</span>
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-2">
              {lineage.signals.map((signal, idx) => (
                <motion.div
                  key={signal.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => onNodeClick?.('signal', signal.id)}
                  className={`
                    p-2 rounded border bg-black/20 cursor-pointer
                    hover:bg-[#00ffff]/10 transition-colors
                    ${getScoreColor(signal.score)}
                  `}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-[#6b7280]">{signal.source}</span>
                    <span className={`text-xs font-bold ${getScoreColor(signal.score).split(' ')[0]}`}>
                      {signal.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="text-xs text-[#c0c0c0] line-clamp-2">
                    {signal.title}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Connector: Signals → Trend */}
          <div className="hidden md:flex items-center justify-center">
            <div className="flex flex-col items-center">
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 0.3, duration: 0.3 }}
                className="w-full h-0.5 bg-gradient-to-r from-[#00ffff] to-[#bd93f9]"
              />
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-[#bd93f9] text-lg mt-1"
              >
                →
              </motion.span>
            </div>
          </div>

          {/* Trend */}
          <div className="md:col-span-1">
            <div className="text-[10px] text-[#bd93f9] uppercase tracking-wider mb-2">
              TREND
            </div>
            {lineage.trend ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 }}
                onClick={() => onNodeClick?.('trend', lineage.trend!.id)}
                className={`
                  p-3 rounded border-2 bg-[#bd93f9]/10 cursor-pointer
                  hover:bg-[#bd93f9]/20 transition-colors border-[#bd93f9]
                `}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-[#6b7280]">
                    {lineage.trend.signal_count} {t('signalLineage.signals')}
                  </span>
                  <span className="text-sm font-bold text-[#bd93f9]">
                    {lineage.trend.score.toFixed(1)}
                  </span>
                </div>
                <div className="text-sm text-[#c0c0c0] font-medium">
                  {lineage.trend.name}
                </div>
              </motion.div>
            ) : (
              <div className="p-3 rounded border border-dashed border-[#21262d] text-center">
                <span className="text-xs text-[#6b7280]">{t('signalLineage.noTrend')}</span>
              </div>
            )}
          </div>

          {/* Idea & Plans */}
          <div className="space-y-3">
            {/* Idea */}
            <div>
              <div className="text-[10px] text-[#39ff14] uppercase tracking-wider mb-2">
                IDEA
              </div>
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 }}
                onClick={() => onNodeClick?.('idea', lineage.idea.id)}
                className={`
                  p-3 rounded border-2 bg-[#39ff14]/10 cursor-pointer
                  hover:bg-[#39ff14]/20 transition-colors border-[#39ff14]
                `}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${getStatusColor(lineage.idea.status)}`}>
                    {lineage.idea.status}
                  </span>
                  <span className="text-sm font-bold text-[#39ff14]">
                    {lineage.idea.score.toFixed(1)}
                  </span>
                </div>
                <div className="text-sm text-[#c0c0c0] font-medium line-clamp-2">
                  {lineage.idea.title}
                </div>
              </motion.div>
            </div>

            {/* Plans */}
            {lineage.plans.length > 0 && (
              <div>
                <div className="text-[10px] text-[#00ffff] uppercase tracking-wider mb-2 flex items-center gap-1">
                  <span>PLANS</span>
                  <span className="text-[#6b7280]">({lineage.plans.length})</span>
                </div>
                <div className="space-y-1.5">
                  {lineage.plans.map((plan, idx) => (
                    <motion.div
                      key={plan.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 + idx * 0.1 }}
                      onClick={() => onNodeClick?.('plan', plan.id)}
                      className="p-2 rounded border border-[#00ffff] bg-[#00ffff]/10 cursor-pointer hover:bg-[#00ffff]/20 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-[#00ffff] font-bold">v{plan.version}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${getStatusColor(plan.status)}`}>
                          {plan.status}
                        </span>
                      </div>
                      <div className="text-xs text-[#c0c0c0] mt-1 truncate">
                        {plan.title}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile connectors */}
        <div className="md:hidden flex flex-col items-center gap-2 my-4">
          <span className="text-[#39ff14]">↓</span>
        </div>
      </div>

      {/* Legend */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="pt-3 border-t border-[#21262d] flex flex-wrap justify-center gap-4 text-[10px]"
      >
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#00ffff]" />
          <span className="text-[#6b7280]">Signal</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#bd93f9]" />
          <span className="text-[#6b7280]">Trend</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#39ff14]" />
          <span className="text-[#6b7280]">Idea</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#00ffff]" />
          <span className="text-[#6b7280]">Plan</span>
        </div>
      </motion.div>
    </div>
  );
}

// Compact version for cards showing just the count summary
export function SignalLineageCompact({ signalCount, hasTrend, planCount }: {
  signalCount: number;
  hasTrend: boolean;
  planCount: number;
}) {
  return (
    <div className="flex items-center gap-1 text-xs">
      <span className="text-[#00ffff]">{signalCount}</span>
      <span className="text-[#6b7280]">→</span>
      <span className={hasTrend ? 'text-[#bd93f9]' : 'text-[#6b7280]'}>
        {hasTrend ? '1' : '0'}
      </span>
      <span className="text-[#6b7280]">→</span>
      <span className="text-[#39ff14]">1</span>
      <span className="text-[#6b7280]">→</span>
      <span className="text-[#00ffff]">{planCount}</span>
    </div>
  );
}

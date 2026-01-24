'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { UsageResponse } from '@/lib/api';

interface CostDashboardProps {
  usage: UsageResponse;
  showDetails?: boolean;
}

interface ProviderStats {
  name: string;
  cost: number;
  requests: number;
  inputTokens: number;
  outputTokens: number;
  color: string;
}

export function CostDashboard({ usage, showDetails = false }: CostDashboardProps) {
  const { t } = useI18n();

  const providerStats = useMemo(() => {
    const stats: ProviderStats[] = [];
    const colors: Record<string, string> = {
      ollama: '#39ff14',
      claude: '#bd93f9',
      openai: '#00ffff',
      anthropic: '#bd93f9',
    };

    if (usage.today_by_provider) {
      Object.entries(usage.today_by_provider).forEach(([provider, data]) => {
        stats.push({
          name: provider,
          cost: data.cost,
          requests: data.requests,
          inputTokens: data.input_tokens,
          outputTokens: data.output_tokens,
          color: colors[provider.toLowerCase()] || '#6b7280',
        });
      });
    }

    return stats.sort((a, b) => b.cost - a.cost);
  }, [usage.today_by_provider]);

  const totalCost = usage.today.total_cost;
  const monthlyBudget = 100; // Configurable budget
  const budgetUsed = (totalCost / monthlyBudget) * 100;

  const formatCost = (cost: number) => {
    return cost < 1 ? `$${cost.toFixed(4)}` : `$${cost.toFixed(2)}`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
    if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
    return tokens.toString();
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('costDashboard.title')}
        </span>
        <span className="text-xs text-[#6b7280]">
          {t('costDashboard.today')}
        </span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 rounded border border-[#39ff14]/30 bg-[#39ff14]/10">
          <div className="text-lg font-bold text-[#39ff14]">
            {formatCost(totalCost)}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('costDashboard.todayCost')}</div>
        </div>
        <div className="p-3 rounded border border-[#00ffff]/30 bg-[#00ffff]/10">
          <div className="text-lg font-bold text-[#00ffff]">
            {usage.today.total_requests}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('costDashboard.requests')}</div>
        </div>
        <div className="p-3 rounded border border-[#bd93f9]/30 bg-[#bd93f9]/10">
          <div className="text-lg font-bold text-[#bd93f9]">
            {formatTokens(usage.today.total_input_tokens + usage.today.total_output_tokens)}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('costDashboard.tokens')}</div>
        </div>
        <div className="p-3 rounded border border-[#ff6b35]/30 bg-[#ff6b35]/10">
          <div className="text-lg font-bold text-[#ff6b35]">
            {formatCost(usage.month_total)}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('costDashboard.monthTotal')}</div>
        </div>
      </div>

      {/* Budget Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[#6b7280]">{t('costDashboard.budgetUsage')}</span>
          <span className={`font-bold ${
            budgetUsed >= 90 ? 'text-[#ff5555]' :
            budgetUsed >= 70 ? 'text-[#ff6b35]' :
            'text-[#39ff14]'
          }`}>
            {budgetUsed.toFixed(1)}%
          </span>
        </div>
        <div className="h-3 bg-[#21262d] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, budgetUsed)}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className={`h-full ${
              budgetUsed >= 90 ? 'bg-[#ff5555]' :
              budgetUsed >= 70 ? 'bg-[#ff6b35]' :
              'bg-[#39ff14]'
            }`}
          />
        </div>
        <div className="flex items-center justify-between text-[10px] text-[#6b7280]">
          <span>{formatCost(usage.month_total)} {t('costDashboard.used')}</span>
          <span>{formatCost(monthlyBudget)} {t('costDashboard.budget')}</span>
        </div>
      </div>

      {/* Provider Breakdown */}
      {providerStats.length > 0 && (
        <div className="space-y-2 pt-3 border-t border-[#21262d]">
          <div className="text-xs text-[#6b7280] uppercase">
            {t('costDashboard.byProvider')}
          </div>
          <div className="space-y-2">
            {providerStats.map((provider, idx) => {
              const percentage = totalCost > 0 ? (provider.cost / totalCost) * 100 : 0;

              return (
                <motion.div
                  key={provider.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: provider.color }}
                      />
                      <span className="text-xs text-[#c0c0c0]">{provider.name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      {showDetails && (
                        <>
                          <span className="text-[#6b7280]">{provider.requests} req</span>
                          <span className="text-[#6b7280]">
                            {formatTokens(provider.inputTokens + provider.outputTokens)} tok
                          </span>
                        </>
                      )}
                      <span className="font-bold" style={{ color: provider.color }}>
                        {formatCost(provider.cost)}
                      </span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-[#21262d] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ delay: idx * 0.1, duration: 0.5 }}
                      className="h-full"
                      style={{ backgroundColor: provider.color }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* History Chart */}
      {usage.history && usage.history.length > 0 && showDetails && (
        <div className="space-y-2 pt-3 border-t border-[#21262d]">
          <div className="text-xs text-[#6b7280] uppercase">
            {t('costDashboard.history')} ({usage.days} {t('costDashboard.days')})
          </div>
          <div className="flex items-end gap-1 h-16">
            {usage.history.slice(-14).map((day, idx) => {
              const maxCost = Math.max(...usage.history.map((h) => h.cost), 1);
              const height = (day.cost / maxCost) * 100;

              return (
                <motion.div
                  key={day.date}
                  initial={{ height: 0 }}
                  animate={{ height: `${height}%` }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex-1 bg-[#00ffff]/50 hover:bg-[#00ffff] rounded-t cursor-pointer transition-colors"
                  title={`${day.date}: ${formatCost(day.cost)} (${day.requests} req)`}
                />
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] text-[#6b7280]">
            <span>{usage.history[usage.history.length - 14]?.date.slice(-5) || ''}</span>
            <span>{t('costDashboard.today')}</span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="pt-3 border-t border-[#21262d] flex flex-wrap gap-3 text-[10px]">
        {providerStats.map((provider) => (
          <div key={provider.name} className="flex items-center gap-1">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: provider.color }}
            />
            <span className="text-[#6b7280]">{provider.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Compact version for dashboard widgets
export function CostDashboardCompact({ usage }: { usage: UsageResponse }) {
  const formatCost = (cost: number) => {
    return cost < 1 ? `$${cost.toFixed(3)}` : `$${cost.toFixed(2)}`;
  };

  return (
    <div className="flex items-center gap-3 text-xs">
      <div className="flex items-center gap-1">
        <span className="text-[#39ff14] font-bold">{formatCost(usage.today.total_cost)}</span>
        <span className="text-[#6b7280]">today</span>
      </div>
      <span className="text-[#6b7280]">|</span>
      <div className="flex items-center gap-1">
        <span className="text-[#00ffff] font-bold">{usage.today.total_requests}</span>
        <span className="text-[#6b7280]">req</span>
      </div>
      <span className="text-[#6b7280]">|</span>
      <div className="flex items-center gap-1">
        <span className="text-[#bd93f9] font-bold">{formatCost(usage.month_total)}</span>
        <span className="text-[#6b7280]">month</span>
      </div>
    </div>
  );
}

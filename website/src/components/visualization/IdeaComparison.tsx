'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiIdea } from '@/lib/api';

interface IdeaComparisonProps {
  ideas: ApiIdea[];
  onSelect?: (ideaId: string) => void;
  maxCompare?: number;
}

interface ComparisonMetric {
  key: string;
  label: string;
  getValue: (idea: ApiIdea) => string | number;
  format?: 'score' | 'text' | 'status' | 'date';
}

export function IdeaComparison({
  ideas,
  onSelect,
  maxCompare = 3,
}: IdeaComparisonProps) {
  const { t } = useI18n();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  const metrics: ComparisonMetric[] = [
    { key: 'score', label: t('ideaComparison.score'), getValue: (i) => i.score, format: 'score' },
    { key: 'status', label: t('ideaComparison.status'), getValue: (i) => i.status, format: 'status' },
    { key: 'source', label: t('ideaComparison.source'), getValue: (i) => i.source_type, format: 'text' },
    { key: 'created', label: t('ideaComparison.created'), getValue: (i) => i.created_at?.split('T')[0] || '-', format: 'date' },
  ];

  const toggleSelect = (ideaId: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(ideaId)) {
        return prev.filter((id) => id !== ideaId);
      }
      if (prev.length >= maxCompare) {
        return [...prev.slice(1), ideaId];
      }
      return [...prev, ideaId];
    });
  };

  const selectedIdeas = ideas.filter((i) => selectedIds.includes(i.id));

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-[#39ff14]';
    if (score >= 6) return 'text-[#00ffff]';
    if (score >= 4) return 'text-[#ff6b35]';
    return 'text-[#6b7280]';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'promoted':
        return 'bg-[#39ff14]/20 text-[#39ff14]';
      case 'scored':
        return 'bg-[#00ffff]/20 text-[#00ffff]';
      case 'in-development':
        return 'bg-[#ff6b35]/20 text-[#ff6b35]';
      case 'archived':
        return 'bg-[#6b7280]/20 text-[#6b7280]';
      default:
        return 'bg-[#bd93f9]/20 text-[#bd93f9]';
    }
  };

  const getBestValue = (metric: ComparisonMetric): string | number | null => {
    if (selectedIdeas.length < 2) return null;
    if (metric.format === 'score') {
      const values = selectedIdeas.map((i) => Number(metric.getValue(i)));
      return Math.max(...values);
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('ideaComparison.title')}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280]">
            {selectedIds.length}/{maxCompare} {t('ideaComparison.selected')}
          </span>
          {selectedIds.length >= 2 && (
            <button
              onClick={() => setShowComparison(!showComparison)}
              className="btn-cli text-xs"
            >
              {showComparison ? t('ideaComparison.hideCompare') : t('ideaComparison.compare')}
            </button>
          )}
        </div>
      </div>

      {/* Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
        {ideas.map((idea) => {
          const isSelected = selectedIds.includes(idea.id);
          return (
            <motion.div
              key={idea.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleSelect(idea.id)}
              className={`
                p-2 rounded border cursor-pointer transition-colors
                ${isSelected
                  ? 'border-[#39ff14] bg-[#39ff14]/10'
                  : 'border-[#21262d] bg-black/20 hover:border-[#6b7280]'
                }
              `}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${getScoreColor(idea.score)}`}>
                  {idea.score.toFixed(1)}
                </span>
                <span className={`text-[10px] px-1 py-0.5 rounded ${getStatusColor(idea.status)}`}>
                  {idea.status}
                </span>
              </div>
              <div className="text-xs text-[#c0c0c0] line-clamp-2">{idea.title}</div>
            </motion.div>
          );
        })}
      </div>

      {/* Comparison Table */}
      <AnimatePresence>
        {showComparison && selectedIdeas.length >= 2 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="card-cli p-4 mt-4">
              <div className="text-xs text-[#00ffff] uppercase tracking-wider mb-4">
                {t('ideaComparison.comparisonTable')}
              </div>

              {/* Header Row */}
              <div className="grid gap-2" style={{ gridTemplateColumns: `120px repeat(${selectedIdeas.length}, 1fr)` }}>
                <div className="text-xs text-[#6b7280]">{t('ideaComparison.metric')}</div>
                {selectedIdeas.map((idea) => (
                  <div key={idea.id} className="text-xs text-[#c0c0c0] font-bold line-clamp-2">
                    {idea.title.slice(0, 30)}...
                  </div>
                ))}
              </div>

              {/* Divider */}
              <div className="h-px bg-[#21262d] my-3" />

              {/* Metric Rows */}
              {metrics.map((metric) => {
                const bestValue = getBestValue(metric);
                return (
                  <div
                    key={metric.key}
                    className="grid gap-2 py-2 border-b border-[#21262d]/50 last:border-0"
                    style={{ gridTemplateColumns: `120px repeat(${selectedIdeas.length}, 1fr)` }}
                  >
                    <div className="text-xs text-[#6b7280]">{metric.label}</div>
                    {selectedIdeas.map((idea) => {
                      const value = metric.getValue(idea);
                      const isBest = metric.format === 'score' && value === bestValue;

                      return (
                        <div key={idea.id} className="relative">
                          {metric.format === 'score' && (
                            <div className="flex items-center gap-1">
                              <span className={`text-sm font-bold ${getScoreColor(Number(value))}`}>
                                {Number(value).toFixed(1)}
                              </span>
                              {isBest && (
                                <span className="text-[10px] text-[#39ff14]">★</span>
                              )}
                            </div>
                          )}
                          {metric.format === 'status' && (
                            <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusColor(String(value))}`}>
                              {value}
                            </span>
                          )}
                          {metric.format === 'text' && (
                            <span className="text-xs text-[#c0c0c0]">{value}</span>
                          )}
                          {metric.format === 'date' && (
                            <span className="text-xs text-[#6b7280]">{value}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}

              {/* Summary Row */}
              <div className="mt-4 pt-3 border-t border-[#21262d]">
                <div className="grid gap-2" style={{ gridTemplateColumns: `120px repeat(${selectedIdeas.length}, 1fr)` }}>
                  <div className="text-xs text-[#6b7280]">{t('ideaComparison.summary')}</div>
                  {selectedIdeas.map((idea) => (
                    <div key={idea.id} className="text-xs text-[#c0c0c0] line-clamp-3">
                      {idea.summary}
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 mt-4">
                {selectedIdeas.map((idea) => (
                  <button
                    key={idea.id}
                    onClick={() => onSelect?.(idea.id)}
                    className="flex-1 btn-cli text-xs text-center"
                  >
                    {t('ideaComparison.viewDetails')} #{idea.id.slice(0, 6)}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Stats */}
      {selectedIds.length >= 2 && !showComparison && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center gap-4 text-xs"
        >
          <div className="flex items-center gap-2">
            <span className="text-[#6b7280]">{t('ideaComparison.avgScore')}:</span>
            <span className={`font-bold ${getScoreColor(
              selectedIdeas.reduce((sum, i) => sum + i.score, 0) / selectedIdeas.length
            )}`}>
              {(selectedIdeas.reduce((sum, i) => sum + i.score, 0) / selectedIdeas.length).toFixed(1)}
            </span>
          </div>
          <span className="text-[#6b7280]">|</span>
          <div className="flex items-center gap-2">
            <span className="text-[#6b7280]">{t('ideaComparison.bestScore')}:</span>
            <span className="font-bold text-[#39ff14]">
              {Math.max(...selectedIdeas.map((i) => i.score)).toFixed(1)}
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
}

// Mini version for quick selection
export function IdeaComparisonMini({
  ideas,
  onCompare,
}: {
  ideas: ApiIdea[];
  onCompare: (ids: string[]) => void;
}) {
  const { t } = useI18n();
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1">
        {ideas.slice(0, 5).map((idea) => (
          <button
            key={idea.id}
            onClick={() => toggle(idea.id)}
            className={`
              w-6 h-6 rounded text-[10px] font-bold transition-colors
              ${selected.includes(idea.id)
                ? 'bg-[#39ff14] text-black'
                : 'bg-[#21262d] text-[#6b7280] hover:bg-[#6b7280]/20'
              }
            `}
          >
            {idea.score.toFixed(0)}
          </button>
        ))}
      </div>
      {selected.length >= 2 && (
        <button
          onClick={() => onCompare(selected)}
          className="text-xs text-[#00ffff] hover:text-[#39ff14]"
        >
          {t('ideaComparison.compare')}
        </button>
      )}
    </div>
  );
}

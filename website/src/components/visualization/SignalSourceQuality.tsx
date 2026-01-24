'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiSignal } from '@/lib/api';

interface SignalSourceQualityProps {
  signals: ApiSignal[];
  showDetails?: boolean;
}

interface SourceStats {
  source: string;
  count: number;
  avgScore: number;
  maxScore: number;
  categories: string[];
  recentSignals: number;
  quality: 'excellent' | 'good' | 'average' | 'poor';
}

export function SignalSourceQuality({ signals, showDetails = false }: SignalSourceQualityProps) {
  const { t } = useI18n();

  const sourceStats = useMemo(() => {
    const stats: Record<string, SourceStats> = {};

    signals.forEach((signal) => {
      const source = signal.source || 'unknown';
      if (!stats[source]) {
        stats[source] = {
          source,
          count: 0,
          avgScore: 0,
          maxScore: 0,
          categories: [],
          recentSignals: 0,
          quality: 'average',
        };
      }

      stats[source].count++;
      stats[source].avgScore =
        (stats[source].avgScore * (stats[source].count - 1) + signal.score) / stats[source].count;
      stats[source].maxScore = Math.max(stats[source].maxScore, signal.score);

      if (signal.category && !stats[source].categories.includes(signal.category)) {
        stats[source].categories.push(signal.category);
      }

      // Count recent signals (within 24h)
      if (signal.collected_at) {
        const signalDate = new Date(signal.collected_at);
        const now = new Date();
        const hoursDiff = (now.getTime() - signalDate.getTime()) / (1000 * 60 * 60);
        if (hoursDiff < 24) {
          stats[source].recentSignals++;
        }
      }
    });

    // Calculate quality rating
    Object.values(stats).forEach((stat) => {
      const scoreRating = stat.avgScore >= 7 ? 2 : stat.avgScore >= 5 ? 1 : 0;
      const volumeRating = stat.count >= 50 ? 2 : stat.count >= 20 ? 1 : 0;
      const freshnessRating = stat.recentSignals >= 10 ? 2 : stat.recentSignals >= 3 ? 1 : 0;
      const totalRating = scoreRating + volumeRating + freshnessRating;

      stat.quality =
        totalRating >= 5 ? 'excellent' :
        totalRating >= 3 ? 'good' :
        totalRating >= 1 ? 'average' : 'poor';
    });

    return Object.values(stats).sort((a, b) => b.avgScore - a.avgScore);
  }, [signals]);

  const totalSignals = signals.length;
  const avgOverallScore =
    signals.length > 0
      ? signals.reduce((sum, s) => sum + s.score, 0) / signals.length
      : 0;

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent':
        return 'bg-[#39ff14]/20 text-[#39ff14] border-[#39ff14]';
      case 'good':
        return 'bg-[#00ffff]/20 text-[#00ffff] border-[#00ffff]';
      case 'average':
        return 'bg-[#ff6b35]/20 text-[#ff6b35] border-[#ff6b35]';
      case 'poor':
        return 'bg-[#ff5555]/20 text-[#ff5555] border-[#ff5555]';
      default:
        return 'bg-[#6b7280]/20 text-[#6b7280] border-[#6b7280]';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-[#39ff14]';
    if (score >= 6) return 'text-[#00ffff]';
    if (score >= 4) return 'text-[#ff6b35]';
    return 'text-[#6b7280]';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('signalSourceQuality.title')}
        </span>
        <span className="text-xs text-[#6b7280]">
          {sourceStats.length} {t('signalSourceQuality.sources')}
        </span>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="text-center p-2 rounded border border-[#21262d] bg-black/20">
          <div className="text-lg font-bold text-[#00ffff]">{totalSignals}</div>
          <div className="text-[10px] text-[#6b7280]">{t('signalSourceQuality.totalSignals')}</div>
        </div>
        <div className="text-center p-2 rounded border border-[#21262d] bg-black/20">
          <div className={`text-lg font-bold ${getScoreColor(avgOverallScore)}`}>
            {avgOverallScore.toFixed(1)}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('signalSourceQuality.avgScore')}</div>
        </div>
        <div className="text-center p-2 rounded border border-[#21262d] bg-black/20">
          <div className="text-lg font-bold text-[#39ff14]">
            {sourceStats.filter((s) => s.quality === 'excellent' || s.quality === 'good').length}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('signalSourceQuality.quality')}</div>
        </div>
        <div className="text-center p-2 rounded border border-[#21262d] bg-black/20">
          <div className="text-lg font-bold text-[#bd93f9]">{sourceStats.length}</div>
          <div className="text-[10px] text-[#6b7280]">{t('signalSourceQuality.sources')}</div>
        </div>
      </div>

      {/* Source Distribution Chart */}
      <div className="space-y-2">
        <div className="text-xs text-[#6b7280] uppercase">
          {t('signalSourceQuality.distribution')}
        </div>
        <div className="space-y-1.5">
          {sourceStats.slice(0, showDetails ? undefined : 5).map((stat, idx) => {
            const percentage = (stat.count / totalSignals) * 100;

            return (
              <motion.div
                key={stat.source}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-[#c0c0c0] w-24 truncate">{stat.source}</span>
                  <div className="flex-1 h-4 bg-[#21262d] rounded overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ delay: idx * 0.05, duration: 0.5 }}
                      className={`h-full ${getQualityColor(stat.quality).split(' ')[0]}`}
                    />
                  </div>
                  <span className="text-xs text-[#6b7280] w-12 text-right">
                    {stat.count}
                  </span>
                  <span className={`text-xs font-bold w-8 text-right ${getScoreColor(stat.avgScore)}`}>
                    {stat.avgScore.toFixed(1)}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${getQualityColor(stat.quality)}`}>
                    {stat.quality}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Detailed View */}
      {showDetails && sourceStats.length > 0 && (
        <div className="space-y-2 pt-3 border-t border-[#21262d]">
          <div className="text-xs text-[#6b7280] uppercase">
            {t('signalSourceQuality.qualityBreakdown')}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {['excellent', 'good', 'average', 'poor'].map((quality) => {
              const count = sourceStats.filter((s) => s.quality === quality).length;
              return (
                <motion.div
                  key={quality}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className={`p-2 rounded border ${getQualityColor(quality)}`}
                >
                  <div className="text-center">
                    <div className="text-lg font-bold">{count}</div>
                    <div className="text-[10px] uppercase">{quality}</div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="pt-3 border-t border-[#21262d] flex flex-wrap gap-3 text-[10px]">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#39ff14]" />
          <span className="text-[#6b7280]">{t('signalSourceQuality.excellent')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#00ffff]" />
          <span className="text-[#6b7280]">{t('signalSourceQuality.good')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#ff6b35]" />
          <span className="text-[#6b7280]">{t('signalSourceQuality.average')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#ff5555]" />
          <span className="text-[#6b7280]">{t('signalSourceQuality.poor')}</span>
        </div>
      </div>
    </div>
  );
}

// Compact version for summaries
export function SignalSourceQualityCompact({ signals }: { signals: ApiSignal[] }) {
  const { t } = useI18n();

  const qualityCounts = useMemo(() => {
    const sourceScores: Record<string, number[]> = {};
    signals.forEach((s) => {
      if (!sourceScores[s.source]) sourceScores[s.source] = [];
      sourceScores[s.source].push(s.score);
    });

    let excellent = 0,
      good = 0,
      average = 0,
      poor = 0;

    Object.values(sourceScores).forEach((scores) => {
      const avg = scores.reduce((sum, s) => sum + s, 0) / scores.length;
      if (avg >= 8) excellent++;
      else if (avg >= 6) good++;
      else if (avg >= 4) average++;
      else poor++;
    });

    return { excellent, good, average, poor };
  }, [signals]);

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-[#39ff14]">{qualityCounts.excellent}</span>
      <span className="text-[#00ffff]">{qualityCounts.good}</span>
      <span className="text-[#ff6b35]">{qualityCounts.average}</span>
      <span className="text-[#ff5555]">{qualityCounts.poor}</span>
      <span className="text-[#6b7280]">{t('signalSourceQuality.sources')}</span>
    </div>
  );
}

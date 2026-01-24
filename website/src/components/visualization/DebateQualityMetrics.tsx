'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiDebateMessage } from '@/lib/api';

interface DebateQualityMetricsProps {
  messages: ApiDebateMessage[];
  phase: string;
  roundNumber: number;
  maxRounds: number;
  showDetails?: boolean;
}

interface QualityMetric {
  key: string;
  label: string;
  value: number;
  maxValue: number;
  description: string;
  rating: 'excellent' | 'good' | 'average' | 'poor';
}

export function DebateQualityMetrics({
  messages,
  phase,
  roundNumber,
  maxRounds,
  showDetails = false,
}: DebateQualityMetricsProps) {
  const { t } = useI18n();

  const metrics = useMemo(() => {
    const result: QualityMetric[] = [];

    // 1. Participation Rate
    const uniqueAgents = new Set(messages.map((m) => m.agent_id)).size;
    const participationValue = Math.min(100, (uniqueAgents / 8) * 100);
    result.push({
      key: 'participation',
      label: t('debateQualityMetrics.participation'),
      value: participationValue,
      maxValue: 100,
      description: `${uniqueAgents} ${t('debateQualityMetrics.agentsActive')}`,
      rating: participationValue >= 80 ? 'excellent' : participationValue >= 60 ? 'good' : participationValue >= 40 ? 'average' : 'poor',
    });

    // 2. Message Depth
    const avgMessageLength = messages.length > 0
      ? messages.reduce((sum, m) => sum + m.content.length, 0) / messages.length
      : 0;
    const depthValue = Math.min(100, (avgMessageLength / 500) * 100);
    result.push({
      key: 'depth',
      label: t('debateQualityMetrics.depth'),
      value: depthValue,
      maxValue: 100,
      description: `${Math.round(avgMessageLength)} ${t('debateQualityMetrics.avgChars')}`,
      rating: depthValue >= 70 ? 'excellent' : depthValue >= 50 ? 'good' : depthValue >= 30 ? 'average' : 'poor',
    });

    // 3. Engagement Score
    const messageTypes = new Set(messages.map((m) => m.message_type));
    const diversityScore = (messageTypes.size / 5) * 100;
    result.push({
      key: 'engagement',
      label: t('debateQualityMetrics.engagement'),
      value: diversityScore,
      maxValue: 100,
      description: `${messageTypes.size} ${t('debateQualityMetrics.messageTypes')}`,
      rating: diversityScore >= 80 ? 'excellent' : diversityScore >= 60 ? 'good' : diversityScore >= 40 ? 'average' : 'poor',
    });

    // 4. Progress Score
    const progressValue = (roundNumber / maxRounds) * 100;
    result.push({
      key: 'progress',
      label: t('debateQualityMetrics.progress'),
      value: progressValue,
      maxValue: 100,
      description: `${t('debateQualityMetrics.round')} ${roundNumber}/${maxRounds}`,
      rating: progressValue === 100 ? 'excellent' : progressValue >= 66 ? 'good' : progressValue >= 33 ? 'average' : 'poor',
    });

    // 5. Consensus Indicator (based on message sentiment patterns)
    const positivePatterns = ['agree', 'support', 'build on', 'excellent', 'great'];
    const negativePatterns = ['disagree', 'concern', 'risk', 'however', 'but'];

    let positiveCount = 0;
    let negativeCount = 0;
    messages.forEach((m) => {
      const content = m.content.toLowerCase();
      positivePatterns.forEach((p) => { if (content.includes(p)) positiveCount++; });
      negativePatterns.forEach((p) => { if (content.includes(p)) negativeCount++; });
    });

    const total = positiveCount + negativeCount || 1;
    const consensusValue = (positiveCount / total) * 100;
    result.push({
      key: 'consensus',
      label: t('debateQualityMetrics.consensus'),
      value: consensusValue,
      maxValue: 100,
      description: `${Math.round(consensusValue)}% ${t('debateQualityMetrics.agreementRate')}`,
      rating: consensusValue >= 70 ? 'excellent' : consensusValue >= 50 ? 'good' : consensusValue >= 30 ? 'average' : 'poor',
    });

    return result;
  }, [messages, roundNumber, maxRounds, t]);

  const overallScore = useMemo(() => {
    if (metrics.length === 0) return 0;
    return metrics.reduce((sum, m) => sum + m.value, 0) / metrics.length;
  }, [metrics]);

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'excellent':
        return 'text-[#39ff14] bg-[#39ff14]/20';
      case 'good':
        return 'text-[#00ffff] bg-[#00ffff]/20';
      case 'average':
        return 'text-[#ff6b35] bg-[#ff6b35]/20';
      case 'poor':
        return 'text-[#ff5555] bg-[#ff5555]/20';
      default:
        return 'text-[#6b7280] bg-[#6b7280]/20';
    }
  };

  const getBarColor = (rating: string) => {
    switch (rating) {
      case 'excellent':
        return 'bg-[#39ff14]';
      case 'good':
        return 'bg-[#00ffff]';
      case 'average':
        return 'bg-[#ff6b35]';
      case 'poor':
        return 'bg-[#ff5555]';
      default:
        return 'bg-[#6b7280]';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('debateQualityMetrics.title')}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280]">{t('debateQualityMetrics.overall')}:</span>
          <span className={`text-sm font-bold ${
            overallScore >= 70 ? 'text-[#39ff14]' :
            overallScore >= 50 ? 'text-[#00ffff]' :
            overallScore >= 30 ? 'text-[#ff6b35]' : 'text-[#ff5555]'
          }`}>
            {overallScore.toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Overall Score Gauge */}
      <div className="relative h-3 bg-[#21262d] rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${overallScore}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="h-full bg-gradient-to-r from-[#ff5555] via-[#ff6b35] via-[#00ffff] to-[#39ff14]"
          style={{
            background: `linear-gradient(to right, #ff5555, #ff6b35 33%, #00ffff 66%, #39ff14)`,
          }}
        />
        <div
          className="absolute top-0 h-full w-0.5 bg-white/50"
          style={{ left: `${overallScore}%` }}
        />
      </div>

      {/* Metrics Grid */}
      <div className="space-y-3">
        {metrics.map((metric, idx) => (
          <motion.div
            key={metric.key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-[#c0c0c0]">{metric.label}</span>
              <div className="flex items-center gap-2">
                {showDetails && (
                  <span className="text-[10px] text-[#6b7280]">{metric.description}</span>
                )}
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${getRatingColor(metric.rating)}`}>
                  {metric.rating.toUpperCase()}
                </span>
              </div>
            </div>
            <div className="h-2 bg-[#21262d] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(metric.value / metric.maxValue) * 100}%` }}
                transition={{ delay: idx * 0.1, duration: 0.5 }}
                className={`h-full ${getBarColor(metric.rating)}`}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Phase Info */}
      <div className="pt-3 border-t border-[#21262d] flex items-center justify-between text-xs">
        <span className="text-[#6b7280]">{t('debateQualityMetrics.currentPhase')}:</span>
        <span className={`px-2 py-0.5 rounded ${
          phase === 'planning' ? 'bg-[#39ff14]/20 text-[#39ff14]' :
          phase === 'convergence' ? 'bg-[#00ffff]/20 text-[#00ffff]' :
          'bg-[#ff6b35]/20 text-[#ff6b35]'
        }`}>
          {phase.toUpperCase()}
        </span>
      </div>
    </div>
  );
}

// Compact badge version
export function DebateQualityBadge({
  messages,
  roundNumber,
  maxRounds,
}: {
  messages: ApiDebateMessage[];
  roundNumber: number;
  maxRounds: number;
}) {
  const uniqueAgents = new Set(messages.map((m) => m.agent_id)).size;
  const progress = (roundNumber / maxRounds) * 100;

  const qualityScore = (uniqueAgents / 8 + progress / 100) / 2 * 100;
  const rating = qualityScore >= 70 ? 'A' : qualityScore >= 50 ? 'B' : qualityScore >= 30 ? 'C' : 'D';

  const getRatingStyle = () => {
    switch (rating) {
      case 'A':
        return 'bg-[#39ff14]/20 text-[#39ff14] border-[#39ff14]';
      case 'B':
        return 'bg-[#00ffff]/20 text-[#00ffff] border-[#00ffff]';
      case 'C':
        return 'bg-[#ff6b35]/20 text-[#ff6b35] border-[#ff6b35]';
      default:
        return 'bg-[#ff5555]/20 text-[#ff5555] border-[#ff5555]';
    }
  };

  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded border ${getRatingStyle()}`}>
      {rating}
    </span>
  );
}

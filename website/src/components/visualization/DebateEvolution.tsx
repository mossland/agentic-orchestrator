'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiDebateMessage } from '@/lib/api';

interface RoundSummary {
  round: number;
  phase: string;
  messageCount: number;
  participants: string[];
  keyPoints: string[];
  avgSentiment: 'positive' | 'neutral' | 'negative' | 'mixed';
  ideasProposed: number;
  ideasFiltered: number;
  consensusLevel: number; // 0-100
}

interface DebateEvolutionProps {
  messages: ApiDebateMessage[];
  phase: string;
  maxRounds: number;
  currentRound: number;
  showDetails?: boolean;
}

export function DebateEvolution({
  messages,
  phase,
  maxRounds,
  currentRound,
  showDetails = false,
}: DebateEvolutionProps) {
  const { t } = useI18n();

  // Analyze messages to create round summaries
  const roundSummaries = analyzeRounds(messages, maxRounds);

  // Calculate overall evolution metrics
  const evolutionMetrics = calculateEvolutionMetrics(roundSummaries);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('debateEvolution.title')}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280]">{t('debateEvolution.phase')}:</span>
          <span className="text-xs text-[#ff6b35] font-bold">{phase}</span>
        </div>
      </div>

      {/* Evolution Timeline */}
      <div className="relative">
        {/* Progress Bar Background */}
        <div className="h-2 bg-[#21262d] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(currentRound / maxRounds) * 100}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="h-full bg-gradient-to-r from-[#ff6b35] via-[#bd93f9] to-[#39ff14]"
          />
        </div>

        {/* Round Markers */}
        <div className="flex justify-between mt-2">
          {Array.from({ length: maxRounds }, (_, i) => i + 1).map((round) => (
            <motion.div
              key={round}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: round * 0.1 }}
              className={`
                w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
                ${round <= currentRound
                  ? round === currentRound
                    ? 'bg-[#ff6b35] text-black'
                    : 'bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]'
                  : 'bg-[#21262d] text-[#6b7280] border border-[#21262d]'
                }
              `}
            >
              R{round}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Round Details */}
      {showDetails && (
        <div className="space-y-3 mt-4">
          {roundSummaries.map((summary, idx) => (
            <motion.div
              key={summary.round}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="card-cli p-3 border-l-2 border-[#ff6b35]/50 hover:border-[#ff6b35] transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[#ff6b35] font-bold text-sm">
                    R{summary.round}
                  </span>
                  <span className="text-xs text-[#6b7280]">
                    {summary.messageCount} {t('debateEvolution.messages')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {/* Sentiment Indicator */}
                  <span className={`text-xs px-1.5 py-0.5 rounded ${getSentimentColor(summary.avgSentiment)}`}>
                    {summary.avgSentiment}
                  </span>
                  {/* Consensus Level */}
                  <span className="text-xs text-[#6b7280]">
                    {t('debateEvolution.consensus')}: {summary.consensusLevel}%
                  </span>
                </div>
              </div>

              {/* Participants */}
              <div className="flex flex-wrap gap-1 mb-2">
                {summary.participants.slice(0, 5).map((p) => (
                  <span key={p} className="text-[10px] text-[#00ffff]">
                    @{p}
                  </span>
                ))}
                {summary.participants.length > 5 && (
                  <span className="text-[10px] text-[#6b7280]">
                    +{summary.participants.length - 5}
                  </span>
                )}
              </div>

              {/* Key Points */}
              {summary.keyPoints.length > 0 && (
                <div className="text-xs text-[#c0c0c0] space-y-1">
                  {summary.keyPoints.map((point, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="text-[#bd93f9]">•</span>
                      <span className="line-clamp-1">{point}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Ideas Stats */}
              <div className="flex items-center gap-4 mt-2 text-[10px]">
                <span className="text-[#39ff14]">
                  +{summary.ideasProposed} {t('debateEvolution.proposed')}
                </span>
                {summary.ideasFiltered > 0 && (
                  <span className="text-[#ff5555]">
                    -{summary.ideasFiltered} {t('debateEvolution.filtered')}
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Evolution Metrics Summary */}
      <div className="grid grid-cols-4 gap-2 pt-3 border-t border-[#21262d]">
        <div className="text-center">
          <div className="text-lg font-bold text-[#ff6b35]">
            {evolutionMetrics.totalMessages}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('debateEvolution.totalMessages')}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#00ffff]">
            {evolutionMetrics.uniqueParticipants}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('debateEvolution.participants')}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#39ff14]">
            {evolutionMetrics.ideasNet}
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('debateEvolution.netIdeas')}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#bd93f9]">
            {evolutionMetrics.avgConsensus}%
          </div>
          <div className="text-[10px] text-[#6b7280]">{t('debateEvolution.avgConsensus')}</div>
        </div>
      </div>
    </div>
  );
}

// Compact version for debate cards
export function DebateEvolutionCompact({
  currentRound,
  maxRounds,
  messageCount,
  participantCount,
}: {
  currentRound: number;
  maxRounds: number;
  messageCount: number;
  participantCount: number;
}) {
  const progress = (currentRound / maxRounds) * 100;

  return (
    <div className="flex items-center gap-2">
      {/* Mini progress bar */}
      <div className="flex-1 h-1.5 bg-[#21262d] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#ff6b35] to-[#39ff14]"
          style={{ width: `${progress}%` }}
        />
      </div>
      {/* Stats */}
      <div className="flex items-center gap-1.5 text-[10px]">
        <span className="text-[#ff6b35]">R{currentRound}/{maxRounds}</span>
        <span className="text-[#6b7280]">•</span>
        <span className="text-[#00ffff]">{messageCount}msg</span>
        <span className="text-[#6b7280]">•</span>
        <span className="text-[#bd93f9]">{participantCount}</span>
      </div>
    </div>
  );
}

// Helper functions
function analyzeRounds(messages: ApiDebateMessage[], maxRounds: number): RoundSummary[] {
  const summaries: RoundSummary[] = [];

  // Group messages by round (estimate based on message sequence)
  const messagesPerRound = Math.ceil(messages.length / maxRounds);

  for (let round = 1; round <= maxRounds; round++) {
    const startIdx = (round - 1) * messagesPerRound;
    const endIdx = Math.min(round * messagesPerRound, messages.length);
    const roundMessages = messages.slice(startIdx, endIdx);

    if (roundMessages.length === 0) break;

    // Extract unique participants
    const participants = [...new Set(roundMessages.map((m) => m.agent_handle || m.agent_name))];

    // Extract key points from message types
    const keyPoints: string[] = [];
    roundMessages.forEach((m) => {
      if (m.message_type === 'proposal' || m.message_type === 'synthesis') {
        const preview = m.content.slice(0, 100);
        if (!keyPoints.includes(preview)) {
          keyPoints.push(preview);
        }
      }
    });

    // Estimate sentiment
    const sentimentScore = roundMessages.reduce((acc, m) => {
      const lower = m.content.toLowerCase();
      if (lower.includes('agree') || lower.includes('support') || lower.includes('excellent')) {
        return acc + 1;
      }
      if (lower.includes('disagree') || lower.includes('concern') || lower.includes('risk')) {
        return acc - 1;
      }
      return acc;
    }, 0);

    const avgSentiment: 'positive' | 'neutral' | 'negative' | 'mixed' =
      sentimentScore > 2 ? 'positive' :
      sentimentScore < -2 ? 'negative' :
      Math.abs(sentimentScore) <= 1 ? 'neutral' : 'mixed';

    // Estimate ideas proposed/filtered
    const ideasProposed = roundMessages.filter(
      (m) => m.message_type === 'proposal' || m.message_type === 'idea'
    ).length;
    const ideasFiltered = round > 1 ? Math.floor(ideasProposed * 0.3) : 0;

    // Consensus level (higher in later rounds)
    const consensusLevel = Math.min(95, 50 + round * 15 + Math.random() * 10);

    summaries.push({
      round,
      phase: round === 1 ? 'divergence' : round === maxRounds ? 'planning' : 'convergence',
      messageCount: roundMessages.length,
      participants,
      keyPoints: keyPoints.slice(0, 3),
      avgSentiment,
      ideasProposed,
      ideasFiltered,
      consensusLevel: Math.round(consensusLevel),
    });
  }

  return summaries;
}

function calculateEvolutionMetrics(summaries: RoundSummary[]) {
  const totalMessages = summaries.reduce((sum, s) => sum + s.messageCount, 0);
  const allParticipants = new Set(summaries.flatMap((s) => s.participants));
  const totalProposed = summaries.reduce((sum, s) => sum + s.ideasProposed, 0);
  const totalFiltered = summaries.reduce((sum, s) => sum + s.ideasFiltered, 0);
  const avgConsensus = summaries.length > 0
    ? Math.round(summaries.reduce((sum, s) => sum + s.consensusLevel, 0) / summaries.length)
    : 0;

  return {
    totalMessages,
    uniqueParticipants: allParticipants.size,
    ideasNet: totalProposed - totalFiltered,
    avgConsensus,
  };
}

function getSentimentColor(sentiment: 'positive' | 'neutral' | 'negative' | 'mixed'): string {
  switch (sentiment) {
    case 'positive':
      return 'bg-[#39ff14]/20 text-[#39ff14]';
    case 'negative':
      return 'bg-[#ff5555]/20 text-[#ff5555]';
    case 'mixed':
      return 'bg-[#ff6b35]/20 text-[#ff6b35]';
    default:
      return 'bg-[#6b7280]/20 text-[#6b7280]';
  }
}

'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiDebate } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { DebateConversation } from '../visualization/DebateConversation';
import { DebateTimeline } from '../visualization/DebateTimeline';
import { AgentContribution } from '../visualization/AgentContribution';
import { DebateEvolution } from '../visualization/DebateEvolution';
import { DebateQualityMetrics } from '../visualization/DebateQualityMetrics';
import { LiveDebateViewer } from '../visualization/LiveDebateViewer';
import { TerminalBadge } from '../TerminalWindow';

interface DebateDetailProps {
  data: ModalData;
}

interface DebateMessage {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_handle: string | null;
  message_type: string;
  content: string;
  content_ko: string | null;
  created_at: string | null;
}

interface DebateWithMessages {
  debate: ApiDebate;
  messages: DebateMessage[];
  message_count: number;
}

export function DebateDetail({ data }: DebateDetailProps) {
  const { t, locale } = useI18n();
  const [debateData, setDebateData] = useState<DebateWithMessages | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'conversation' | 'timeline' | 'live'>('live');

  useEffect(() => {
    async function fetchDebate() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getDebateDetail(data.id);
        if (response.data) {
          setDebateData(response.data);
        } else {
          setError(response.error || t('detail.fetchError'));
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchDebate();
  }, [data.id, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#ff6b35] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !debateData) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const { debate, messages } = debateData;

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    completed: 'green',
    'in-progress': 'orange',
    pending: 'cyan',
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TerminalBadge variant={statusColors[debate.status] || 'cyan'}>
            {debate.status}
          </TerminalBadge>
          <TerminalBadge variant="orange">{debate.phase}</TerminalBadge>
          <TerminalBadge variant="purple">
            R{debate.round_number}/{debate.max_rounds}
          </TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">
          {t('detail.debateSession')} #{debate.id.slice(0, 8)}
        </h3>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card-cli p-3 text-center">
          <div className="text-2xl font-bold text-[#ff6b35]">{messages.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.messages')}</div>
        </div>
        <div className="card-cli p-3 text-center">
          <div className="text-2xl font-bold text-[#00ffff]">{debate.participants.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.participants')}</div>
        </div>
        <div className="card-cli p-3 text-center">
          <div className="text-2xl font-bold text-[#bd93f9]">{debate.round_number}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.currentRound')}</div>
        </div>
        <div className="card-cli p-3 text-center">
          <div className="text-2xl font-bold text-[#39ff14]">{debate.max_rounds}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.maxRounds')}</div>
        </div>
      </div>

      {/* Debate Evolution */}
      {messages.length > 0 && (
        <div className="card-cli p-4">
          <DebateEvolution
            messages={messages}
            phase={debate.phase}
            maxRounds={debate.max_rounds}
            currentRound={debate.round_number}
            showDetails={true}
          />
        </div>
      )}

      {/* Debate Quality Metrics */}
      {messages.length > 0 && (
        <div className="card-cli p-4">
          <DebateQualityMetrics
            messages={messages}
            phase={debate.phase}
            roundNumber={debate.round_number}
            maxRounds={debate.max_rounds}
            showDetails={true}
          />
        </div>
      )}

      {/* Participants */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.participants')}</div>
        <div className="flex flex-wrap gap-2">
          {debate.participants.map((participant, idx) => (
            <motion.span
              key={participant}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="tag tag-cyan"
            >
              @{participant}
            </motion.span>
          ))}
        </div>
      </div>

      {/* Agent Contributions */}
      {messages.length > 0 && (
        <div className="card-cli p-4">
          <AgentContribution
            messages={messages}
            phase={debate.phase}
            showDetails={true}
            maxAgents={10}
          />
        </div>
      )}

      {/* View Mode Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setViewMode('live')}
          className={`btn-cli text-xs ${viewMode === 'live' ? 'bg-[#39ff14] text-black' : ''}`}
        >
          {t('liveDebate.title')}
        </button>
        <button
          onClick={() => setViewMode('conversation')}
          className={`btn-cli text-xs ${viewMode === 'conversation' ? 'bg-[#39ff14] text-black' : ''}`}
        >
          {t('detail.conversationView')}
        </button>
        <button
          onClick={() => setViewMode('timeline')}
          className={`btn-cli text-xs ${viewMode === 'timeline' ? 'bg-[#39ff14] text-black' : ''}`}
        >
          {t('detail.timelineView')}
        </button>
      </div>

      {/* Messages */}
      <div className="card-cli p-4">
        {viewMode === 'live' ? (
          <LiveDebateViewer
            debate={debate}
            messages={messages}
            isLive={debate.status === 'in-progress'}
          />
        ) : viewMode === 'conversation' ? (
          <DebateConversation messages={messages} locale={locale} />
        ) : (
          <DebateTimeline messages={messages} locale={locale} />
        )}
      </div>

      {/* Outcome */}
      {debate.outcome && (
        <div className="card-cli p-4 border-l-2 border-[#39ff14]">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.outcome')}</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">{debate.outcome}</p>
        </div>
      )}

      {/* Timestamps */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.timestamps')}</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[#6b7280]">{t('detail.startedAt')}: </span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(debate.started_at)}
            </span>
          </div>
          <div>
            <span className="text-[#6b7280]">{t('detail.completedAt')}: </span>
            <span className="text-[#c0c0c0]">
              {debate.completed_at ? formatLocalDateTime(debate.completed_at) : t('detail.inProgress')}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

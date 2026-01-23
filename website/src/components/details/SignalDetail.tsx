'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiSignal } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { ScoreGauge } from '../visualization/ScoreGauge';
import { TerminalBadge } from '../TerminalWindow';

interface SignalDetailProps {
  data: ModalData;
}

export function SignalDetail({ data }: SignalDetailProps) {
  const { t } = useI18n();
  const [signal, setSignal] = useState<ApiSignal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSignal() {
      setLoading(true);
      setError(null);

      // If full signal data is passed in, use it
      if (data.source && data.title) {
        setSignal(data as unknown as ApiSignal);
        setLoading(false);
        return;
      }

      // Otherwise, fetch from API (when API supports single signal fetch)
      try {
        const response = await ApiClient.getSignals({ limit: 100 });
        if (response.data) {
          const found = response.data.signals.find(s => s.id === data.id);
          if (found) {
            setSignal(found);
          } else {
            setError(t('detail.notFound'));
          }
        } else {
          setError(response.error || t('detail.fetchError'));
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchSignal();
  }, [data, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#00ffff] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !signal) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const sentimentColor = signal.sentiment === 'positive'
    ? 'green'
    : signal.sentiment === 'negative'
      ? 'red'
      : 'cyan';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TerminalBadge variant="cyan">{signal.source}</TerminalBadge>
          <TerminalBadge variant="purple">{signal.category}</TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{signal.title}</h3>
      </div>

      {/* Score Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.score')}</div>
          <ScoreGauge value={signal.score} maxValue={10} label={t('detail.relevance')} />
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.sentiment')}</div>
          <div className="flex items-center gap-2">
            <TerminalBadge variant={sentimentColor as 'green' | 'red' | 'cyan'}>
              {signal.sentiment || 'neutral'}
            </TerminalBadge>
          </div>
        </div>
      </div>

      {/* Summary */}
      {signal.summary && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.summary')}</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">{signal.summary}</p>
        </div>
      )}

      {/* Topics */}
      {signal.topics && signal.topics.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.topics')}</div>
          <div className="flex flex-wrap gap-2">
            {signal.topics.map((topic, idx) => (
              <motion.span
                key={topic}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="tag tag-cyan"
              >
                {topic}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Entities */}
      {signal.entities && signal.entities.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.entities')}</div>
          <div className="flex flex-wrap gap-2">
            {signal.entities.map((entity, idx) => (
              <motion.span
                key={entity}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="tag tag-purple"
              >
                {entity}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.metadata')}</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[#6b7280]">{t('detail.collectedAt')}: </span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(signal.collected_at)}
            </span>
          </div>
          {signal.url && (
            <div>
              <span className="text-[#6b7280]">{t('detail.source')}: </span>
              <a
                href={signal.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#00ffff] hover:underline"
              >
                {t('detail.viewOriginal')}
              </a>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

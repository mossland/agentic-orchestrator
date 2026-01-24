'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiTrend, type ApiSignal } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { ScoreGauge } from '../visualization/ScoreGauge';
import { TerminalBadge } from '../TerminalWindow';

interface TrendDetailProps {
  data: ModalData;
}

interface TrendWithSignals extends ApiTrend {
  related_signals?: ApiSignal[];
}

export function TrendDetail({ data }: TrendDetailProps) {
  const { t, locale } = useI18n();
  const [trend, setTrend] = useState<TrendWithSignals | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper to get localized content
  const getLocalizedText = (en: string | null | undefined, ko: string | null | undefined): string => {
    if (locale === 'ko' && ko) return ko;
    return en || '';
  };

  useEffect(() => {
    async function fetchTrend() {
      setLoading(true);
      setError(null);

      // If full trend data is passed in, use it
      if (data.name && data.score !== undefined) {
        setTrend(data as unknown as TrendWithSignals);
        setLoading(false);
        return;
      }

      try {
        const response = await ApiClient.getTrends({ limit: 100 });
        if (response.data) {
          const found = response.data.trends.find(t => t.id === data.id);
          if (found) {
            setTrend(found);
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

    fetchTrend();
  }, [data, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#bd93f9] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !trend) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const categoryColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    ai: 'cyan',
    web3: 'purple',
    crypto: 'orange',
    tech: 'green',
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
          <TerminalBadge variant={categoryColors[trend.category || 'tech'] || 'green'}>
            {trend.category || 'tech'}
          </TerminalBadge>
          <TerminalBadge variant="cyan">{trend.period}</TerminalBadge>
          {locale === 'ko' && trend.name_ko && (
            <TerminalBadge variant="green">{t('detail.translatedContent')}</TerminalBadge>
          )}
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">
          {getLocalizedText(trend.name, trend.name_ko)}
        </h3>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.trendScore')}</div>
          <ScoreGauge value={trend.score} maxValue={10} label={t('detail.relevance')} color="purple" />
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.signalCount')}</div>
          <div className="text-3xl font-bold text-[#00ffff]">
            {trend.signal_count}
          </div>
          <div className="text-xs text-[#6b7280]">{t('detail.relatedSignals')}</div>
        </div>
      </div>

      {/* Description */}
      {(trend.description || trend.description_ko) && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.description')}</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">
            {getLocalizedText(trend.description, trend.description_ko)}
          </p>
        </div>
      )}

      {/* Web3 Relevance */}
      {(trend as any).web3_relevance && (
        <div className="card-cli p-4 border-l-2 border-[#bd93f9]">
          <div className="text-xs text-[#6b7280] uppercase mb-2">Web3 Relevance</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">{(trend as any).web3_relevance}</p>
        </div>
      )}

      {/* Idea Seeds */}
      {(trend as any).idea_seeds && (trend as any).idea_seeds.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">💡 Idea Seeds</div>
          <div className="space-y-2">
            {(trend as any).idea_seeds.map((seed: string, idx: number) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-start gap-2 p-2 bg-[#39ff14]/5 border border-[#39ff14]/20 rounded"
              >
                <span className="text-[#39ff14]">→</span>
                <span className="text-sm text-[#c0c0c0]">{seed}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Sample Headlines */}
      {(trend as any).sample_headlines && (trend as any).sample_headlines.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">📰 Sample Headlines</div>
          <div className="space-y-2">
            {(trend as any).sample_headlines.map((headline: string, idx: number) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="text-xs text-[#c0c0c0] p-2 bg-black/20 rounded border-l-2 border-[#00ffff]"
              >
                {headline}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Keywords */}
      {trend.keywords && trend.keywords.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.keywords')}</div>
          <div className="flex flex-wrap gap-2">
            {trend.keywords.map((keyword, idx) => (
              <motion.span
                key={keyword}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="tag tag-purple"
              >
                #{keyword}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {(trend as any).sources && (trend as any).sources.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">Sources</div>
          <div className="flex flex-wrap gap-2">
            {(trend as any).sources.map((source: string, idx: number) => (
              <span
                key={idx}
                className="tag tag-cyan"
              >
                {source}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Related Signals */}
      {trend.related_signals && trend.related_signals.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.relatedSignals')}</div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {trend.related_signals.map((signal, idx) => (
              <motion.div
                key={signal.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-2 p-2 bg-black/20 rounded"
              >
                <span className="text-[#00ffff]">→</span>
                <span className="text-sm text-[#c0c0c0] flex-1 truncate">
                  {getLocalizedText(signal.title, signal.title_ko)}
                </span>
                <span className="text-xs text-[#bd93f9]">{signal.score.toFixed(1)}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.metadata')}</div>
        <div className="text-xs">
          <span className="text-[#6b7280]">{t('detail.analyzedAt')}: </span>
          <span className="text-[#c0c0c0]">
            {formatLocalDateTime(trend.analyzed_at)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

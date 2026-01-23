'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiDebate } from '@/lib/api';
import { formatLocalDate } from '@/lib/date';
import { useModal } from '@/components/modals/useModal';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';

export default function DebatesPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [debates, setDebates] = useState<ApiDebate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string; phase?: string }>({});

  useEffect(() => {
    async function fetchDebates() {
      setLoading(true);
      const response = await ApiClient.getDebates({
        limit: 50,
        status: filter.status,
        phase: filter.phase,
      });

      if (response.data) {
        setDebates(response.data.debates);
      }
      setLoading(false);
    }

    fetchDebates();
  }, [filter]);

  const handleDebateClick = (debate: ApiDebate) => {
    openModal('debate', {
      id: debate.id,
      title: `Debate Session #${debate.id.slice(0, 8)}`,
    });
  };

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    completed: 'green',
    'in-progress': 'orange',
    pending: 'cyan',
  };

  const phaseColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    divergence: 'cyan',
    convergence: 'orange',
    planning: 'purple',
  };

  return (
    <div className="min-h-screen pt-14 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-[#ff6b35] mb-2">
            💬 {t('debates.title')}
          </h1>
          <p className="text-sm text-[#6b7280]">
            {t('debates.subtitle')}
          </p>
        </motion.div>

        {/* Debate Explanation */}
        <TerminalWindow title="MULTI_AGENT_DEBATE_SYSTEM" className="mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            {['Founder', 'VC', 'Accelerator', 'Founder Friend'].map((role, idx) => (
              <motion.div
                key={role}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-3 rounded bg-black/20"
              >
                <div className="text-2xl mb-1">
                  {['🚀', '💰', '🎯', '🤝'][idx]}
                </div>
                <div className={`text-xs font-bold ${['text-[#39ff14]', 'text-[#00ffff]', 'text-[#ff6b35]', 'text-[#bd93f9]'][idx]}`}>
                  {role}
                </div>
                <div className="text-[10px] text-[#6b7280] mt-1">
                  {t(`role.${role.toLowerCase().replace(' ', '')}.perspective`)}
                </div>
              </motion.div>
            ))}
          </div>
          <div className="text-center text-xs text-[#6b7280] mt-4">
            {t('debates.rotationInfo')}
          </div>
        </TerminalWindow>

        {/* Filters */}
        <TerminalWindow title="FILTERS" className="mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Status Filter */}
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('debates.status')}</label>
              <select
                value={filter.status || ''}
                onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('debates.allStatuses')}</option>
                <option value="completed">{t('debates.completed')}</option>
                <option value="in-progress">{t('debates.inProgress')}</option>
                <option value="pending">{t('debates.pending')}</option>
              </select>
            </div>

            {/* Phase Filter */}
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('debates.phase')}</label>
              <select
                value={filter.phase || ''}
                onChange={(e) => setFilter({ ...filter, phase: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('debates.allPhases')}</option>
                <option value="divergence">{t('debates.divergence')}</option>
                <option value="convergence">{t('debates.convergence')}</option>
                <option value="planning">{t('debates.planning')}</option>
              </select>
            </div>
          </div>
        </TerminalWindow>

        {/* Debates List */}
        <TerminalWindow title={`DEBATE_HISTORY (${debates.length})`}>
          {loading ? (
            <div className="text-center py-12">
              <div className="text-[#ff6b35] animate-pulse">
                $ {t('detail.loading')}
                <span className="cursor-blink">▋</span>
              </div>
            </div>
          ) : debates.length === 0 ? (
            <div className="text-center py-12 text-[#6b7280]">
              {t('debates.noDebates')}
            </div>
          ) : (
            <div className="space-y-3">
              {debates.map((debate, idx) => (
                <motion.div
                  key={debate.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  onClick={() => handleDebateClick(debate)}
                  className="card-cli p-4 cursor-pointer hover:border-[#ff6b35] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    {/* Round indicator */}
                    <div className="text-center">
                      <div className="text-xl font-bold text-[#ff6b35]">
                        R{debate.round_number}
                      </div>
                      <div className="text-[10px] text-[#6b7280]">
                        /{debate.max_rounds}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <TerminalBadge variant={statusColors[debate.status] || 'cyan'}>
                          {debate.status}
                        </TerminalBadge>
                        <TerminalBadge variant={phaseColors[debate.phase] || 'cyan'}>
                          {debate.phase}
                        </TerminalBadge>
                      </div>
                      <div className="text-sm text-[#c0c0c0]">
                        {t('debates.session')} #{debate.id.slice(0, 8)}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {debate.participants.slice(0, 4).map(participant => (
                          <span key={participant} className="text-[10px] text-[#00ffff]">
                            @{participant}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="text-right">
                      <div className="text-lg font-bold text-[#00ffff]">
                        {debate.message_count || 0}
                      </div>
                      <div className="text-[10px] text-[#6b7280]">{t('debates.messages')}</div>
                    </div>

                    {/* Arrow */}
                    <div className="text-[#21262d]">→</div>
                  </div>

                  {/* Outcome preview */}
                  {debate.outcome && (
                    <div className="mt-3 pt-3 border-t border-[#21262d]">
                      <div className="text-xs text-[#6b7280] line-clamp-1">
                        <span className="text-[#39ff14]">✓</span> {debate.outcome}
                      </div>
                    </div>
                  )}

                  {/* Timestamps */}
                  <div className="mt-2 flex gap-4 text-[10px] text-[#3b3b3b]">
                    {debate.started_at && (
                      <span>{t('debates.started')}: {formatLocalDate(debate.started_at)}</span>
                    )}
                    {debate.completed_at && (
                      <span>{t('debates.completed')}: {formatLocalDate(debate.completed_at)}</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </TerminalWindow>
      </div>
    </div>
  );
}

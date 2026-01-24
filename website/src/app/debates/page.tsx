'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiDebate } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import { useModal } from '@/components/modals/useModal';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';

// Polling interval: 5 seconds for active debates, 30 seconds otherwise
const ACTIVE_POLL_INTERVAL = 5000;
const IDLE_POLL_INTERVAL = 30000;

export default function DebatesPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [debates, setDebates] = useState<ApiDebate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<{ status?: string; phase?: string }>({});
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [hasActiveDebate, setHasActiveDebate] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const fetchDebates = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);

    const response = await ApiClient.getDebates({
      limit: 50,
      status: filter.status,
      phase: filter.phase,
    });

    if (response.data) {
      setDebates(response.data.debates);
      // Check if any debate is active
      const active = response.data.debates.some(d => d.status === 'active');
      setHasActiveDebate(active);
      setLastUpdate(new Date());
    }
    if (showLoading) setLoading(false);
  }, [filter]);

  // Initial fetch
  useEffect(() => {
    fetchDebates(true);
  }, [fetchDebates]);

  // Polling effect
  useEffect(() => {
    // Clear existing interval
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // Set polling interval based on active debates
    const interval = hasActiveDebate ? ACTIVE_POLL_INTERVAL : IDLE_POLL_INTERVAL;

    pollingRef.current = setInterval(() => {
      fetchDebates(false);
    }, interval);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [hasActiveDebate, fetchDebates]);

  const handleDebateClick = (debate: ApiDebate) => {
    openModal('debate', {
      id: debate.id,
      title: debate.topic || `Debate Session #${debate.id.slice(0, 8)}`,
    });
  };

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    completed: 'green',
    active: 'orange',
    'in-progress': 'orange',
    pending: 'cyan',
    cancelled: 'purple',
  };

  // Check if a debate is live (active status)
  const isLive = (debate: ApiDebate) => debate.status === 'active';

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
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-[#ff6b35]">
              {t('debates.pageTitle')}
            </h1>
            {hasActiveDebate && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#ff6b35]/20 border border-[#ff6b35]/50"
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff6b35] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#ff6b35]" />
                </span>
                <span className="text-[10px] font-bold text-[#ff6b35] uppercase tracking-wider">
                  {t('debates.liveDebate')}
                </span>
              </motion.div>
            )}
          </div>
          <p className="text-sm text-[#6b7280]">
            {t('debates.pageSubtitle')}
          </p>
        </motion.div>

        {/* How Debates Work */}
        <TerminalWindow title="HOW_DEBATES_WORK" className="mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center mb-4">
            {[
              { role: 'Founder', icon: '🚀', color: 'text-[#39ff14]', desc: 'Vision & execution' },
              { role: 'VC', icon: '💰', color: 'text-[#00ffff]', desc: 'Market & returns' },
              { role: 'Accelerator', icon: '🎯', color: 'text-[#ff6b35]', desc: 'Strategy & growth' },
              { role: 'Friend', icon: '🤝', color: 'text-[#bd93f9]', desc: 'Reality check' },
            ].map((agent, idx) => (
              <motion.div
                key={agent.role}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="p-4 rounded bg-black/20 border border-[#21262d]"
              >
                <div className="text-3xl mb-2">{agent.icon}</div>
                <div className={`text-sm font-bold ${agent.color}`}>{agent.role}</div>
                <div className="text-[10px] text-[#6b7280] mt-1">{agent.desc}</div>
              </motion.div>
            ))}
          </div>
          <div className="text-center text-xs text-[#6b7280] border-t border-[#21262d] pt-4">
            Agents rotate through roles: <span className="text-[#00ffff]">Proposer</span> →
            <span className="text-[#39ff14]"> Supporter</span> →
            <span className="text-[#ff6b35]"> Challenger</span> →
            <span className="text-[#bd93f9]"> Synthesizer</span>
          </div>
        </TerminalWindow>

        {/* Debate Phases */}
        <TerminalWindow title="DEBATE_PHASES" className="mb-6">
          <div className="flex flex-col md:flex-row justify-center gap-4 py-4">
            {[
              { phase: 'Divergence', desc: 'Explore all possibilities', color: 'cyan' },
              { phase: 'Convergence', desc: 'Find common ground', color: 'orange' },
              { phase: 'Planning', desc: 'Create actionable plan', color: 'purple' },
            ].map((item, idx) => (
              <div key={item.phase} className="flex items-center">
                <div className={`
                  p-4 rounded border text-center min-w-[140px]
                  ${item.color === 'cyan' ? 'border-[#00ffff]/30 bg-[#00ffff]/5' : ''}
                  ${item.color === 'orange' ? 'border-[#ff6b35]/30 bg-[#ff6b35]/5' : ''}
                  ${item.color === 'purple' ? 'border-[#bd93f9]/30 bg-[#bd93f9]/5' : ''}
                `}>
                  <div className={`text-sm font-bold
                    ${item.color === 'cyan' ? 'text-[#00ffff]' : ''}
                    ${item.color === 'orange' ? 'text-[#ff6b35]' : ''}
                    ${item.color === 'purple' ? 'text-[#bd93f9]' : ''}
                  `}>
                    {item.phase}
                  </div>
                  <div className="text-[10px] text-[#6b7280] mt-1">{item.desc}</div>
                </div>
                {idx < 2 && (
                  <span className="text-[#21262d] mx-2 hidden md:block">→</span>
                )}
              </div>
            ))}
          </div>
        </TerminalWindow>

        {/* Filters */}
        <TerminalWindow title="FILTERS" className="mb-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('debates.filter.status')}</label>
              <select
                value={filter.status || ''}
                onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('debates.filter.all')}</option>
                <option value="active">{t('debates.filter.active')}</option>
                <option value="completed">{t('debates.filter.completed')}</option>
                <option value="cancelled">{t('debates.filter.cancelled')}</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('debates.filter.phase')}</label>
              <select
                value={filter.phase || ''}
                onChange={(e) => setFilter({ ...filter, phase: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('debates.filter.allPhases')}</option>
                <option value="divergence">{t('debates.phase.divergence')}</option>
                <option value="convergence">{t('debates.phase.convergence')}</option>
                <option value="planning">{t('debates.phase.planning')}</option>
              </select>
            </div>

            {/* Polling Status */}
            <div className="ml-auto text-right">
              <div className="text-[10px] text-[#6b7280]">
                {hasActiveDebate ? (
                  <span className="text-[#ff6b35]">
                    <span className="inline-block w-2 h-2 rounded-full bg-[#ff6b35] animate-pulse mr-1" />
                    {t('debates.livePolling')}
                  </span>
                ) : (
                  <span>{t('debates.autoRefresh')}</span>
                )}
              </div>
              <div className="text-[10px] text-[#3b3b3b]">
                {t('debates.lastUpdate')}: {lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </TerminalWindow>

        {/* Debates List */}
        <TerminalWindow title={`DEBATE_SESSIONS (${debates.length})`}>
          {loading ? (
            <div className="text-center py-12">
              <div className="text-[#ff6b35] animate-pulse">
                {t('debates.loading')}
                <span className="cursor-blink">_</span>
              </div>
            </div>
          ) : debates.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">💬</div>
              <div className="text-[#6b7280] mb-2">{t('debates.noDebates')}</div>
              <div className="text-xs text-[#3b3b3b]">
                {t('debates.noDebatesDesc')}
              </div>
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
                  className={`card-cli p-4 cursor-pointer transition-colors relative ${
                    isLive(debate)
                      ? 'border-[#ff6b35] bg-[#ff6b35]/5'
                      : 'hover:border-[#ff6b35]'
                  }`}
                >
                  {/* LIVE indicator for active debates */}
                  {isLive(debate) && (
                    <div className="absolute top-2 right-2 flex items-center gap-1.5">
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff6b35] opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#ff6b35]" />
                      </span>
                      <span className="text-[10px] font-bold text-[#ff6b35] uppercase tracking-wider">
                        Live
                      </span>
                    </div>
                  )}

                  <div className="flex items-center gap-4">
                    {/* Round indicator */}
                    <div className="text-center w-16">
                      <div className={`text-xl font-bold ${isLive(debate) ? 'text-[#ff6b35] animate-pulse' : 'text-[#ff6b35]'}`}>
                        R{debate.round_number}
                      </div>
                      <div className="text-[10px] text-[#6b7280]">
                        of {debate.max_rounds}
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

                      {/* Topic - show if available */}
                      {debate.topic ? (
                        <div className="text-sm text-[#c0c0c0] line-clamp-1" title={debate.topic}>
                          {debate.topic}
                        </div>
                      ) : (
                        <div className="text-sm text-[#6b7280]">
                          Session #{debate.id.slice(0, 8)}
                        </div>
                      )}

                      <div className="flex flex-wrap gap-1 mt-2">
                        {debate.participants.slice(0, 4).map(participant => (
                          <span key={participant} className="text-[10px] text-[#00ffff]">
                            @{participant}
                          </span>
                        ))}
                        {debate.participants.length > 4 && (
                          <span className="text-[10px] text-[#6b7280]">
                            +{debate.participants.length - 4} more
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="text-right">
                      <div className={`text-lg font-bold ${isLive(debate) ? 'text-[#ff6b35]' : 'text-[#00ffff]'}`}>
                        {debate.message_count || 0}
                      </div>
                      <div className="text-[10px] text-[#6b7280]">messages</div>
                      {isLive(debate) && debate.total_cost > 0 && (
                        <div className="text-[10px] text-[#39ff14] mt-1">
                          ${debate.total_cost.toFixed(4)}
                        </div>
                      )}
                    </div>

                    {/* Arrow */}
                    <div className="text-[#21262d]">→</div>
                  </div>

                  {/* Summary for active debates */}
                  {isLive(debate) && debate.summary && (
                    <div className="mt-3 pt-3 border-t border-[#ff6b35]/30">
                      <div className="text-xs text-[#ff6b35] line-clamp-2">
                        <span className="font-bold">Progress:</span> {debate.summary}
                      </div>
                    </div>
                  )}

                  {/* Outcome preview for completed debates */}
                  {!isLive(debate) && debate.outcome && (
                    <div className="mt-3 pt-3 border-t border-[#21262d]">
                      <div className="text-xs text-[#6b7280] line-clamp-1">
                        <span className="text-[#39ff14]">Outcome:</span> {debate.outcome}
                      </div>
                    </div>
                  )}

                  {/* Timestamps */}
                  <div className="mt-2 flex gap-4 text-[10px] text-[#3b3b3b]">
                    {debate.started_at && (
                      <span>Started: {formatLocalDateTime(debate.started_at)}</span>
                    )}
                    {debate.completed_at && (
                      <span>Completed: {formatLocalDateTime(debate.completed_at)}</span>
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

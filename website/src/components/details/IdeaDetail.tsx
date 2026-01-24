'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiIdea, type ApiDebate, type ApiPlan, type ApiDebateMessage, type IdeaLineageResponse } from '@/lib/api';
import type { ModalData } from '../modals/ModalProvider';
import { IdeaJourney } from '../visualization/IdeaJourney';
import { ScoreGauge } from '../visualization/ScoreGauge';
import { ScoreBreakdown } from '../visualization/ScoreBreakdown';
import { AgentContribution } from '../visualization/AgentContribution';
import { SignalLineage } from '../visualization/SignalLineage';
import { TerminalBadge } from '../TerminalWindow';

interface IdeaDetailProps {
  data: ModalData;
}

interface IdeaWithDetails {
  idea: ApiIdea;
  debates: (ApiDebate & { messages?: ApiDebateMessage[] })[];
  plans: ApiPlan[];
}

export function IdeaDetail({ data }: IdeaDetailProps) {
  const { t, locale } = useI18n();
  const [ideaData, setIdeaData] = useState<IdeaWithDetails | null>(null);
  const [lineageData, setLineageData] = useState<IdeaLineageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMessages, setExpandedMessages] = useState<boolean>(false);

  useEffect(() => {
    async function fetchIdea() {
      setLoading(true);
      setError(null);

      try {
        // Fetch idea detail and lineage in parallel
        const [ideaResponse, lineageResponse] = await Promise.all([
          ApiClient.getIdeaDetail(data.id),
          ApiClient.getIdeaLineage(data.id),
        ]);

        if (ideaResponse.data) {
          setIdeaData(ideaResponse.data);
        } else {
          setError(ideaResponse.error || t('detail.fetchError'));
        }

        if (lineageResponse.data) {
          setLineageData(lineageResponse.data);
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchIdea();
  }, [data.id, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#39ff14] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !ideaData) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const { idea, debates, plans } = ideaData;

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    backlog: 'cyan',
    planned: 'purple',
    'in-development': 'orange',
    done: 'green',
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
          <TerminalBadge variant={statusColors[idea.status] || 'cyan'}>
            {idea.status}
          </TerminalBadge>
          <TerminalBadge variant="purple">{idea.source_type}</TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{idea.title}</h3>
      </div>

      {/* Score Breakdown */}
      <div className="card-cli p-4">
        <ScoreBreakdown
          score={idea.score}
          consensus={debates.length > 0 ? Math.min(95, 70 + debates.length * 5) : undefined}
          confidence={idea.score >= 7 ? 'high' : idea.score >= 5 ? 'medium' : 'low'}
          showDetails={true}
        />
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.ideaScore')}</div>
          <ScoreGauge value={idea.score} maxValue={10} label={t('detail.potential')} color="green" />
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.debatesCount')}</div>
          <div className="text-3xl font-bold text-[#ff6b35]">{debates.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.rounds')}</div>
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.plansCount')}</div>
          <div className="text-3xl font-bold text-[#00ffff]">{plans.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.versions')}</div>
        </div>
      </div>

      {/* Full Description or Summary */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">
          {idea.description ? t('detail.fullDescription') : t('detail.summary')}
        </div>
        <div className="text-sm text-[#c0c0c0] leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
          {idea.description || idea.summary}
        </div>
      </div>

      {/* Agent Contributions */}
      {debates.length > 0 && debates[0].messages && debates[0].messages.length > 0 && (
        <div className="card-cli p-4">
          <AgentContribution
            messages={debates[0].messages}
            phase={debates[0].phase}
            showDetails={true}
            maxAgents={8}
          />
        </div>
      )}

      {/* Idea Journey Timeline */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">{t('detail.ideaJourney')}</div>
        <IdeaJourney idea={idea} debates={debates} plans={plans} />
      </div>

      {/* Signal Lineage */}
      {lineageData && (
        <div className="card-cli p-4">
          <SignalLineage
            lineage={lineageData}
            onNodeClick={(type, id) => {
              // Could open modals for each node type
              console.log(`Clicked ${type}: ${id}`);
            }}
          />
        </div>
      )}

      {/* Debate Timeline with Agent Messages */}
      {debates.length > 0 && debates[0].messages && debates[0].messages.length > 0 && (
        <div className="card-cli p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs text-[#6b7280] uppercase">{t('detail.debateTimeline')}</div>
            <button
              onClick={() => setExpandedMessages(!expandedMessages)}
              className="text-xs text-[#00ffff] hover:text-[#39ff14] transition-colors"
            >
              {expandedMessages ? t('detail.collapse') : t('detail.expand')} ({debates[0].messages.length})
            </button>
          </div>

          <AnimatePresence initial={false}>
            {expandedMessages && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="space-y-3 max-h-96 overflow-y-auto"
              >
                {debates[0].messages.map((msg, idx) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="border-l-2 border-[#39ff14]/50 pl-4 py-2 hover:border-[#39ff14] transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-[#00ffff] font-bold text-sm">{msg.agent_name}</span>
                      {msg.agent_handle && (
                        <span className="text-xs text-[#6b7280]">@{msg.agent_handle}</span>
                      )}
                      <TerminalBadge variant="purple">{msg.message_type}</TerminalBadge>
                      {msg.created_at && (
                        <span className="text-xs text-[#6b7280]">
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[#c0c0c0] leading-relaxed whitespace-pre-wrap line-clamp-4">
                      {locale === 'ko' && msg.content_ko ? msg.content_ko : msg.content}
                    </p>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {!expandedMessages && (
            <div className="text-sm text-[#6b7280] italic">
              {t('detail.clickToShowMessages')}
            </div>
          )}
        </div>
      )}

      {/* Debates Summary */}
      {debates.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.debateHistory')}</div>
          <div className="space-y-2">
            {debates.map((debate, idx) => (
              <motion.div
                key={debate.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-3 p-2 bg-black/20 rounded hover:bg-black/30 transition-colors"
              >
                <span className="text-[#ff6b35] text-xs font-bold">
                  R{debate.round_number}
                </span>
                <span className="text-sm text-[#c0c0c0] flex-1">{debate.phase}</span>
                <TerminalBadge variant={debate.status === 'completed' ? 'green' : 'orange'}>
                  {debate.status}
                </TerminalBadge>
                <span className="text-xs text-[#6b7280]">
                  {debate.messages?.length || debate.message_count || 0} {t('detail.messages')}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Plans List */}
      {plans.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.planVersions')}</div>
          <div className="space-y-2">
            {plans.map((plan, idx) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-3 p-2 bg-black/20 rounded hover:bg-black/30 transition-colors"
              >
                <span className="text-[#00ffff] text-xs font-bold">
                  v{plan.version}
                </span>
                <span className="text-sm text-[#c0c0c0] flex-1 truncate">{plan.title}</span>
                <TerminalBadge variant={plan.status === 'approved' ? 'green' : 'cyan'}>
                  {plan.status}
                </TerminalBadge>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Links */}
      {idea.github_issue_url && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.links')}</div>
          <a
            href={idea.github_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[#00ffff] hover:underline text-sm"
          >
            <span>→</span>
            {t('detail.viewOnGitHub')}
          </a>
        </div>
      )}
    </motion.div>
  );
}

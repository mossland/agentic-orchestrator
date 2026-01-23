'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiTrend, type ApiIdea, type ApiPlan } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import { useModal } from '@/components/modals/useModal';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';

type ViewMode = 'pipeline' | 'trends' | 'ideas' | 'plans';

export default function IdeasPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [viewMode, setViewMode] = useState<ViewMode>('pipeline');
  const [trends, setTrends] = useState<ApiTrend[]>([]);
  const [ideas, setIdeas] = useState<ApiIdea[]>([]);
  const [plans, setPlans] = useState<ApiPlan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const [trendsRes, ideasRes, plansRes] = await Promise.all([
        ApiClient.getTrends({ limit: 20 }),
        ApiClient.getIdeas({ limit: 50 }),
        ApiClient.getPlans({ limit: 50 }),
      ]);

      if (trendsRes.data) setTrends(trendsRes.data.trends);
      if (ideasRes.data) setIdeas(ideasRes.data.ideas);
      if (plansRes.data) setPlans(plansRes.data.plans);
      setLoading(false);
    }

    fetchData();
  }, []);

  const tabs = [
    { id: 'pipeline' as const, label: 'Pipeline', count: null },
    { id: 'trends' as const, label: 'Trends', count: trends.length },
    { id: 'ideas' as const, label: 'Ideas', count: ideas.length },
    { id: 'plans' as const, label: 'Plans', count: plans.length },
  ];

  const statusColors: Record<string, string> = {
    pending: 'text-[#f1fa8c]',
    approved: 'text-[#39ff14]',
    rejected: 'text-[#ff5555]',
    'in-development': 'text-[#00ffff]',
    done: 'text-[#39ff14]',
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
          <h1 className="text-2xl font-bold text-[#39ff14] mb-2">
            Ideas & Pipeline
          </h1>
          <p className="text-sm text-[#6b7280]">
            From signals to trends to ideas to plans
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-[#21262d] pb-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setViewMode(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 text-sm transition-colors rounded
                ${viewMode === tab.id
                  ? 'bg-[#39ff14]/10 text-[#39ff14] border border-[#39ff14]/30'
                  : 'text-[#6b7280] hover:bg-[#21262d] hover:text-[#c0c0c0]'
                }
              `}
            >
              {tab.label}
              {tab.count !== null && (
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  viewMode === tab.id ? 'bg-[#39ff14]/20' : 'bg-[#21262d]'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-[#39ff14] animate-pulse">
              Loading...
              <span className="cursor-blink">_</span>
            </div>
          </div>
        ) : (
          <>
            {/* Pipeline View */}
            {viewMode === 'pipeline' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                {/* Pipeline Flow */}
                <TerminalWindow title="IDEA_GENERATION_PIPELINE" className="mb-6">
                  <div className="flex flex-col md:flex-row items-center justify-center gap-4 py-6">
                    {[
                      { stage: 'Signals', count: '1000+', color: 'cyan', desc: 'RSS/API feeds' },
                      { stage: 'Trends', count: trends.length, color: 'purple', desc: 'Pattern analysis' },
                      { stage: 'Ideas', count: ideas.length, color: 'green', desc: 'Generated concepts' },
                      { stage: 'Plans', count: plans.length, color: 'orange', desc: 'Refined proposals' },
                    ].map((item, idx) => (
                      <div key={item.stage} className="flex items-center">
                        <div className={`
                          text-center p-4 rounded border bg-black/20
                          ${item.color === 'cyan' ? 'border-[#00ffff]/30' : ''}
                          ${item.color === 'purple' ? 'border-[#bd93f9]/30' : ''}
                          ${item.color === 'green' ? 'border-[#39ff14]/30' : ''}
                          ${item.color === 'orange' ? 'border-[#ff6b35]/30' : ''}
                        `}>
                          <div className={`text-2xl font-bold mb-1
                            ${item.color === 'cyan' ? 'text-[#00ffff]' : ''}
                            ${item.color === 'purple' ? 'text-[#bd93f9]' : ''}
                            ${item.color === 'green' ? 'text-[#39ff14]' : ''}
                            ${item.color === 'orange' ? 'text-[#ff6b35]' : ''}
                          `}>
                            {item.count}
                          </div>
                          <div className="text-sm text-[#c0c0c0]">{item.stage}</div>
                          <div className="text-[10px] text-[#6b7280] mt-1">{item.desc}</div>
                        </div>
                        {idx < 3 && (
                          <span className="text-[#21262d] mx-2 hidden md:block text-xl">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </TerminalWindow>

                {/* Recent Activity */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Recent Trends */}
                  <TerminalWindow title="RECENT_TRENDS">
                    <div className="space-y-2">
                      {trends.slice(0, 5).map((trend) => (
                        <div
                          key={trend.id}
                          onClick={() => openModal('trend', { ...trend, title: trend.name })}
                          className="p-3 rounded bg-black/20 border border-[#21262d] hover:border-[#bd93f9] cursor-pointer transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-[#c0c0c0] truncate">{trend.name}</span>
                            <span className="text-xs text-[#bd93f9]">{trend.score.toFixed(1)}</span>
                          </div>
                          <div className="text-[10px] text-[#6b7280] mt-1">
                            {trend.signal_count} signals
                            {trend.analyzed_at && (
                              <span className="ml-2">
                                | {formatLocalDateTime(trend.analyzed_at)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {trends.length === 0 && (
                        <div className="text-center py-4 text-[#6b7280] text-sm">No trends yet</div>
                      )}
                    </div>
                  </TerminalWindow>

                  {/* Recent Ideas */}
                  <TerminalWindow title="RECENT_IDEAS">
                    <div className="space-y-2">
                      {ideas.slice(0, 5).map((idea) => (
                        <div
                          key={idea.id}
                          onClick={() => openModal('idea', { ...idea, title: idea.title })}
                          className="p-3 rounded bg-black/20 border border-[#21262d] hover:border-[#39ff14] cursor-pointer transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-[#c0c0c0] truncate flex-1">{idea.title}</span>
                            <span className={`text-xs ml-2 ${statusColors[idea.status] || 'text-[#6b7280]'}`}>
                              {idea.status}
                            </span>
                          </div>
                          <div className="text-[10px] text-[#6b7280] mt-1">
                            {idea.source_type} | Score: {idea.score.toFixed(1)}
                            {idea.created_at && (
                              <span className="ml-2">
                                | {formatLocalDateTime(idea.created_at)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {ideas.length === 0 && (
                        <div className="text-center py-4 text-[#6b7280] text-sm">No ideas yet</div>
                      )}
                    </div>
                  </TerminalWindow>
                </div>
              </motion.div>
            )}

            {/* Trends View */}
            {viewMode === 'trends' && (
              <TerminalWindow title={`TRENDS (${trends.length})`}>
                <div className="space-y-3">
                  {trends.map((trend, idx) => (
                    <motion.div
                      key={trend.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => openModal('trend', { ...trend, title: trend.name })}
                      className="p-4 rounded border border-[#21262d] hover:border-[#bd93f9] cursor-pointer transition-colors bg-black/20"
                    >
                      <div className="flex items-start gap-4">
                        <div className="text-xl font-bold text-[#bd93f9] w-12 text-center">
                          {trend.score.toFixed(1)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{trend.name}</h3>
                          {trend.description && (
                            <p className="text-xs text-[#6b7280] mt-1 line-clamp-2">{trend.description}</p>
                          )}
                          <div className="flex flex-wrap gap-1 mt-2">
                            {trend.keywords?.slice(0, 3).map(kw => (
                              <span key={kw} className="text-[10px] text-[#00ffff]">#{kw}</span>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-[#00ffff]">{trend.signal_count}</div>
                          <div className="text-[10px] text-[#6b7280]">signals</div>
                          {trend.analyzed_at && (
                            <div className="text-[10px] text-[#6b7280] mt-1">
                              {formatLocalDateTime(trend.analyzed_at)}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {trends.length === 0 && (
                    <div className="text-center py-12 text-[#6b7280]">No trends found</div>
                  )}
                </div>
              </TerminalWindow>
            )}

            {/* Ideas View */}
            {viewMode === 'ideas' && (
              <TerminalWindow title={`IDEAS (${ideas.length})`}>
                <div className="space-y-3">
                  {ideas.map((idea, idx) => (
                    <motion.div
                      key={idea.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => openModal('idea', { ...idea, title: idea.title })}
                      className="p-4 rounded border border-[#21262d] hover:border-[#39ff14] cursor-pointer transition-colors bg-black/20"
                    >
                      <div className="flex items-start gap-4">
                        <div className={`text-xl font-bold w-12 text-center ${statusColors[idea.status] || 'text-[#6b7280]'}`}>
                          {idea.score.toFixed(1)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <TerminalBadge variant="green">{idea.status}</TerminalBadge>
                            <TerminalBadge variant="cyan">{idea.source_type}</TerminalBadge>
                          </div>
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{idea.title}</h3>
                          <p className="text-xs text-[#6b7280] mt-1 line-clamp-2">{idea.summary}</p>
                          {idea.created_at && (
                            <div className="text-[10px] text-[#6b7280] mt-2">
                              {formatLocalDateTime(idea.created_at)}
                            </div>
                          )}
                        </div>
                        {idea.github_issue_url && (
                          <a
                            href={idea.github_issue_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[#00ffff] hover:underline text-xs"
                          >
                            GitHub
                          </a>
                        )}
                      </div>
                    </motion.div>
                  ))}
                  {ideas.length === 0 && (
                    <div className="text-center py-12 text-[#6b7280]">No ideas found</div>
                  )}
                </div>
              </TerminalWindow>
            )}

            {/* Plans View */}
            {viewMode === 'plans' && (
              <TerminalWindow title={`PLANS (${plans.length})`}>
                <div className="space-y-3">
                  {plans.map((plan, idx) => (
                    <motion.div
                      key={plan.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => openModal('plan', { ...plan, title: plan.title })}
                      className="p-4 rounded border border-[#21262d] hover:border-[#ff6b35] cursor-pointer transition-colors bg-black/20"
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <div className="text-xl font-bold text-[#ff6b35]">v{plan.version}</div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <TerminalBadge variant={plan.status === 'approved' ? 'green' : plan.status === 'rejected' ? 'red' : 'orange'}>
                              {plan.status}
                            </TerminalBadge>
                          </div>
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{plan.title}</h3>
                          {plan.created_at && (
                            <div className="text-[10px] text-[#6b7280] mt-1">
                              {formatLocalDateTime(plan.created_at)}
                            </div>
                          )}
                        </div>
                        {plan.github_issue_url && (
                          <a
                            href={plan.github_issue_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[#00ffff] hover:underline text-xs"
                          >
                            GitHub
                          </a>
                        )}
                      </div>
                    </motion.div>
                  ))}
                  {plans.length === 0 && (
                    <div className="text-center py-12 text-[#6b7280]">No plans found</div>
                  )}
                </div>
              </TerminalWindow>
            )}
          </>
        )}
      </div>
    </div>
  );
}

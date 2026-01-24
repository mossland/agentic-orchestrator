'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiTrend, type ApiIdea, type ApiPlan, type ApiProject } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import { useModal } from '@/components/modals/useModal';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';
import { IdeaComparison } from '@/components/visualization/IdeaComparison';
import { TrendHeatmap } from '@/components/visualization/TrendHeatmap';
import { IdeaNetwork } from '@/components/visualization/IdeaNetwork';

// Helper function to extract readable text from JSON idea content
function getIdeaSummaryText(content: string | null | undefined): string {
  if (!content) return '';

  try {
    // Remove markdown code block if present (handle various formats)
    let jsonStr = content.trim();

    // Handle ```json\n...\n``` format
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (codeBlockMatch) {
      jsonStr = codeBlockMatch[1].trim();
    } else {
      // Simple removal for edge cases
      if (jsonStr.startsWith('```json')) {
        jsonStr = jsonStr.slice(7);
      } else if (jsonStr.startsWith('```')) {
        jsonStr = jsonStr.slice(3);
      }
      if (jsonStr.endsWith('```')) {
        jsonStr = jsonStr.slice(0, -3);
      }
      jsonStr = jsonStr.trim();
    }

    // Try to parse as JSON
    const parsed = JSON.parse(jsonStr);

    // Try to extract readable text in order of preference
    if (parsed.core_analysis) return parsed.core_analysis;
    if (parsed.proposal?.description) return parsed.proposal.description;
    if (parsed.opportunity_risk?.opportunities) return parsed.opportunity_risk.opportunities;
    if (parsed.idea_title) return parsed.idea_title;

    // If nothing found, return first string value found
    for (const value of Object.values(parsed)) {
      if (typeof value === 'string' && value.length > 20) {
        return value;
      }
    }

    return content; // Fallback to original
  } catch {
    // Not valid JSON - check if it looks like JSON and extract readable parts
    if (content.includes('"core_analysis"')) {
      const match = content.match(/"core_analysis"\s*:\s*"([^"]+)"/);
      if (match) return match[1];
    }
    if (content.includes('"idea_title"')) {
      const match = content.match(/"idea_title"\s*:\s*"([^"]+)"/);
      if (match) return match[1];
    }
    // Return content without JSON artifacts
    return content.replace(/```json/g, '').replace(/```/g, '').replace(/[{}"]/g, '').trim().slice(0, 200);
  }
}

type ViewMode = 'pipeline' | 'trends' | 'ideas' | 'plans' | 'projects';

// Skeleton components for loading states
function PipelineSkeleton() {
  return (
    <div>
      {/* Pipeline Flow Skeleton */}
      <div className="rounded border border-[#21262d] bg-[#0d1117] mb-6 p-6">
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 py-6">
          {[1, 2, 3, 4].map((idx) => (
            <div key={idx} className="flex items-center">
              <div className="text-center p-4 rounded border border-[#21262d] bg-black/20 w-28">
                <div className="h-8 w-12 mx-auto bg-[#21262d] rounded animate-pulse mb-2" />
                <div className="h-4 w-16 mx-auto bg-[#21262d] rounded animate-pulse mb-1" />
                <div className="h-3 w-20 mx-auto bg-[#21262d] rounded animate-pulse" />
              </div>
              {idx < 4 && (
                <span className="text-[#21262d] mx-2 hidden md:block text-xl">→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Skeleton */}
      <div className="grid md:grid-cols-2 gap-6">
        {[1, 2].map((col) => (
          <div key={col} className="rounded border border-[#21262d] bg-[#0d1117] p-4">
            <div className="h-4 w-32 bg-[#21262d] rounded animate-pulse mb-4" />
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((item) => (
                <motion.div
                  key={item}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: item * 0.05 }}
                  className="p-3 rounded bg-black/20 border border-[#21262d]"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="h-4 bg-[#21262d] rounded animate-pulse w-2/3" />
                    <div className="h-4 w-8 bg-[#21262d] rounded animate-pulse" />
                  </div>
                  <div className="h-3 w-1/3 bg-[#21262d] rounded animate-pulse" />
                </motion.div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ListItemSkeleton({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.02 }}
      className="p-4 rounded border border-[#21262d] bg-black/20"
    >
      <div className="flex items-start gap-4">
        {/* Score skeleton */}
        <div className="w-12 h-12 bg-[#21262d] rounded animate-pulse" />

        {/* Content skeleton */}
        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex gap-2 mb-1">
            <div className="h-5 w-16 bg-[#21262d] rounded animate-pulse" />
            <div className="h-5 w-12 bg-[#21262d] rounded animate-pulse" />
          </div>
          <div className="h-4 bg-[#21262d] rounded animate-pulse w-4/5" />
          <div className="h-3 bg-[#21262d] rounded animate-pulse w-full" />
          <div className="h-3 bg-[#21262d] rounded animate-pulse w-1/4 mt-2" />
        </div>

        {/* Action skeleton */}
        <div className="h-4 w-12 bg-[#21262d] rounded animate-pulse" />
      </div>
    </motion.div>
  );
}

function ListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, idx) => (
        <ListItemSkeleton key={idx} index={idx} />
      ))}
    </div>
  );
}

export default function IdeasPage() {
  const { t, locale } = useI18n();
  const { openModal } = useModal();
  const [viewMode, setViewMode] = useState<ViewMode>('pipeline');
  const [trends, setTrends] = useState<ApiTrend[]>([]);
  const [ideas, setIdeas] = useState<ApiIdea[]>([]);
  const [plans, setPlans] = useState<ApiPlan[]>([]);
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [loading, setLoading] = useState(true);

  // Helper function for localized text display
  const getLocalizedText = (en: string | null | undefined, ko: string | null | undefined): string => {
    if (locale === 'ko' && ko) return ko;
    return en || '';
  };

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      const [trendsRes, ideasRes, plansRes, projectsRes] = await Promise.all([
        ApiClient.getTrends({ limit: 20 }),
        ApiClient.getIdeas({ limit: 50 }),
        ApiClient.getPlans({ limit: 50 }),
        ApiClient.getProjects({ limit: 50 }),
      ]);

      if (trendsRes.data) setTrends(trendsRes.data.trends);
      if (ideasRes.data) setIdeas(ideasRes.data.ideas);
      if (plansRes.data) setPlans(plansRes.data.plans);
      if (projectsRes.data) setProjects(projectsRes.data.projects);
      setLoading(false);
    }

    fetchData();
  }, []);

  const tabs = [
    { id: 'pipeline' as const, labelKey: 'ideas.tab.pipeline', count: null },
    { id: 'trends' as const, labelKey: 'ideas.tab.trends', count: trends.length },
    { id: 'ideas' as const, labelKey: 'ideas.tab.ideas', count: ideas.length },
    { id: 'plans' as const, labelKey: 'ideas.tab.plans', count: plans.length },
    { id: 'projects' as const, labelKey: 'ideas.tab.projects', count: projects.length },
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
            {t('ideas.pageTitle')}
          </h1>
          <p className="text-sm text-[#6b7280]">
            {t('ideas.pageSubtitle')}
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
              {t(tab.labelKey)}
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
          // Skeleton loading state based on current view mode
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {viewMode === 'pipeline' && <PipelineSkeleton />}
            {viewMode === 'trends' && (
              <TerminalWindow title="TRENDS">
                <ListSkeleton count={8} />
              </TerminalWindow>
            )}
            {viewMode === 'ideas' && (
              <TerminalWindow title="IDEAS">
                <ListSkeleton count={8} />
              </TerminalWindow>
            )}
            {viewMode === 'plans' && (
              <TerminalWindow title="PLANS">
                <ListSkeleton count={6} />
              </TerminalWindow>
            )}
            {viewMode === 'projects' && (
              <TerminalWindow title="PROJECTS">
                <ListSkeleton count={6} />
              </TerminalWindow>
            )}
          </motion.div>
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
                      { stageKey: 'ideas.stage.signals', count: '1000+', color: 'cyan', descKey: 'ideas.stage.signalsDesc' },
                      { stageKey: 'ideas.stage.trends', count: trends.length, color: 'purple', descKey: 'ideas.stage.trendsDesc' },
                      { stageKey: 'ideas.stage.ideas', count: ideas.length, color: 'green', descKey: 'ideas.stage.ideasDesc' },
                      { stageKey: 'ideas.stage.plans', count: plans.length, color: 'orange', descKey: 'ideas.stage.plansDesc' },
                    ].map((item, idx) => (
                      <div key={item.stageKey} className="flex items-center">
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
                          <div className="text-sm text-[#c0c0c0]">{t(item.stageKey)}</div>
                          <div className="text-[10px] text-[#6b7280] mt-1">{t(item.descKey)}</div>
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
                          onClick={() => openModal('trend', { ...trend, title: getLocalizedText(trend.name, trend.name_ko) })}
                          className="p-3 rounded bg-black/20 border border-[#21262d] hover:border-[#bd93f9] cursor-pointer transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-[#c0c0c0] truncate">{getLocalizedText(trend.name, trend.name_ko)}</span>
                            <span className="text-xs text-[#bd93f9]">{trend.score.toFixed(1)}</span>
                          </div>
                          <div className="text-[10px] text-[#6b7280] mt-1">
                            {trend.signal_count} signals
                            {trend.analyzed_at && (
                              <span className="ml-2">
                                | {formatLocalDateTime(trend.analyzed_at, locale)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {trends.length === 0 && (
                        <div className="text-center py-4 text-[#6b7280] text-sm">{t('ideas.noTrends')}</div>
                      )}
                    </div>
                  </TerminalWindow>

                  {/* Recent Ideas */}
                  <TerminalWindow title="RECENT_IDEAS">
                    <div className="space-y-2">
                      {ideas.slice(0, 5).map((idea) => (
                        <div
                          key={idea.id}
                          onClick={() => openModal('idea', { ...idea, title: getLocalizedText(idea.title, idea.title_ko) })}
                          className="p-3 rounded bg-black/20 border border-[#21262d] hover:border-[#39ff14] cursor-pointer transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-[#c0c0c0] truncate flex-1">{getLocalizedText(idea.title, idea.title_ko)}</span>
                            <span className={`text-xs ml-2 ${statusColors[idea.status] || 'text-[#6b7280]'}`}>
                              {idea.status}
                            </span>
                          </div>
                          <div className="text-[10px] text-[#6b7280] mt-1">
                            {idea.source_type} | Score: {idea.score.toFixed(1)}
                            {idea.created_at && (
                              <span className="ml-2">
                                | {formatLocalDateTime(idea.created_at, locale)}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {ideas.length === 0 && (
                        <div className="text-center py-4 text-[#6b7280] text-sm">{t('ideas.noIdeas')}</div>
                      )}
                    </div>
                  </TerminalWindow>
                </div>
              </motion.div>
            )}

            {/* Trends View */}
            {viewMode === 'trends' && (
              <div className="space-y-6">
                {/* Trend Heatmap */}
                {trends.length > 0 && (
                  <TerminalWindow title="TREND_HEATMAP">
                    <TrendHeatmap
                      trends={trends}
                      onCellClick={(category, day) => {
                        console.log(`Clicked ${category} on ${day}`);
                      }}
                    />
                  </TerminalWindow>
                )}

                <TerminalWindow title={`TRENDS (${trends.length})`}>
                  <div className="space-y-3">
                    {trends.map((trend, idx) => (
                    <motion.div
                      key={trend.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => openModal('trend', { ...trend, title: getLocalizedText(trend.name, trend.name_ko) })}
                      className="p-4 rounded border border-[#21262d] hover:border-[#bd93f9] cursor-pointer transition-colors bg-black/20"
                    >
                      <div className="flex items-start gap-4">
                        <div className="text-xl font-bold text-[#bd93f9] w-12 text-center">
                          {trend.score.toFixed(1)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{getLocalizedText(trend.name, trend.name_ko)}</h3>
                          {(trend.description || trend.description_ko) && (
                            <p className="text-xs text-[#6b7280] mt-1 line-clamp-2">{getLocalizedText(trend.description, trend.description_ko)}</p>
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
                              {formatLocalDateTime(trend.analyzed_at, locale)}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                    {trends.length === 0 && (
                      <div className="text-center py-12 text-[#6b7280]">{t('ideas.noTrends')}</div>
                    )}
                  </div>
                </TerminalWindow>
              </div>
            )}

            {/* Ideas View */}
            {viewMode === 'ideas' && (
              <div className="space-y-6">
                {/* Idea Comparison Tool */}
                {ideas.length >= 2 && (
                  <TerminalWindow title="COMPARE_IDEAS">
                    <IdeaComparison
                      ideas={ideas}
                      onSelect={(id) => {
                        const idea = ideas.find(i => i.id === id);
                        if (idea) openModal('idea', { ...idea, title: getLocalizedText(idea.title, idea.title_ko) });
                      }}
                      maxCompare={3}
                    />
                  </TerminalWindow>
                )}

                {/* Idea Network */}
                {ideas.length >= 3 && (
                  <TerminalWindow title="IDEA_NETWORK">
                    <IdeaNetwork
                      ideas={ideas.slice(0, 20)}
                      onIdeaClick={(id) => {
                        const idea = ideas.find(i => i.id === id);
                        if (idea) openModal('idea', { ...idea, title: getLocalizedText(idea.title, idea.title_ko) });
                      }}
                      showLabels={true}
                    />
                  </TerminalWindow>
                )}

                <TerminalWindow title={`IDEAS (${ideas.length})`}>
                  <div className="space-y-3">
                    {ideas.map((idea, idx) => (
                    <motion.div
                      key={idea.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => openModal('idea', { ...idea, title: getLocalizedText(idea.title, idea.title_ko) })}
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
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{getLocalizedText(idea.title, idea.title_ko)}</h3>
                          <p className="text-xs text-[#6b7280] mt-1 line-clamp-2">{getIdeaSummaryText(getLocalizedText(idea.summary, idea.summary_ko))}</p>
                          {idea.created_at && (
                            <div className="text-[10px] text-[#6b7280] mt-2">
                              {formatLocalDateTime(idea.created_at, locale)}
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
                      <div className="text-center py-12 text-[#6b7280]">{t('ideas.noIdeas')}</div>
                    )}
                  </div>
                </TerminalWindow>
              </div>
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
                      onClick={() => openModal('plan', { ...plan, title: getLocalizedText(plan.title, plan.title_ko) })}
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
                          <h3 className="text-sm font-medium text-[#c0c0c0]">{getLocalizedText(plan.title, plan.title_ko)}</h3>
                          {plan.created_at && (
                            <div className="text-[10px] text-[#6b7280] mt-1">
                              {formatLocalDateTime(plan.created_at, locale)}
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
                    <div className="text-center py-12 text-[#6b7280]">{t('ideas.noPlans')}</div>
                  )}
                </div>
              </TerminalWindow>
            )}

            {/* Projects View */}
            {viewMode === 'projects' && (
              <TerminalWindow title={`PROJECTS (${projects.length})`}>
                <div className="space-y-3">
                  {projects.map((project, idx) => {
                    const getStatusColor = (status: string): 'green' | 'cyan' | 'orange' | 'purple' => {
                      switch (status) {
                        case 'ready': return 'green';
                        case 'generating': return 'cyan';
                        case 'error': return 'orange';
                        default: return 'purple';
                      }
                    };
                    return (
                      <motion.div
                        key={project.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.02 }}
                        onClick={() => openModal('project', { id: project.id, title: project.name })}
                        className="p-4 rounded border border-[#21262d] hover:border-[#39ff14] cursor-pointer transition-colors bg-black/20"
                      >
                        <div className="flex items-start gap-4">
                          <div className="text-center w-16">
                            <div className={`text-xl font-bold ${project.status === 'ready' ? 'text-[#39ff14]' : project.status === 'generating' ? 'text-[#00ffff]' : 'text-[#ff5555]'}`}>
                              {project.files_generated > 0 ? project.files_generated : '-'}
                            </div>
                            <div className="text-[10px] text-[#6b7280]">
                              {project.files_generated > 0 ? (locale === 'ko' ? '파일' : 'files') : ''}
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <TerminalBadge variant={getStatusColor(project.status)}>
                                {project.status.toUpperCase()}
                              </TerminalBadge>
                              {project.tech_stack?.frontend && (
                                <TerminalBadge variant="cyan">{project.tech_stack.frontend}</TerminalBadge>
                              )}
                              {project.tech_stack?.backend && (
                                <TerminalBadge variant="purple">{project.tech_stack.backend}</TerminalBadge>
                              )}
                              {project.tech_stack?.blockchain && (
                                <TerminalBadge variant="orange">{project.tech_stack.blockchain}</TerminalBadge>
                              )}
                            </div>
                            <h3 className="text-sm font-medium text-[#c0c0c0]">{project.name}</h3>
                            {project.directory_path && (
                              <div className="text-[10px] text-[#6b7280] mt-1 font-mono truncate">
                                <span className="text-[#00ffff]">→</span> {project.directory_path}
                              </div>
                            )}
                            {project.created_at && (
                              <div className="text-[10px] text-[#6b7280] mt-1">
                                {formatLocalDateTime(project.created_at, locale)}
                              </div>
                            )}
                          </div>
                          <div className="text-[#21262d]">→</div>
                        </div>
                      </motion.div>
                    );
                  })}
                  {projects.length === 0 && (
                    <div className="text-center py-12 text-[#6b7280]">{t('ideas.noProjects')}</div>
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

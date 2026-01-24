'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { SystemStatus } from '@/components/SystemStatus';
import { StatsGrid } from '@/components/Stats';
import { Pipeline } from '@/components/Pipeline';
import { ActivityFeed } from '@/components/ActivityFeed';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';
import { AdapterDetailModal } from '@/components/AdapterDetailModal';
import { useModal } from '@/components/modals/useModal';
import { rssCategories, aiProviders, mockStats, mockPipeline } from '@/data/mock';
import { fetchSystemStats, fetchActivity, fetchPipeline, fetchAdapters, ApiClient, type ApiProject } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { SystemStats, ActivityItem, PipelineStage, AdapterInfo } from '@/lib/types';

const ASCII_LOGO = `
███╗   ███╗ ██████╗ ███████╗███████╗    █████╗  ██████╗
████╗ ████║██╔═══██╗██╔════╝██╔════╝   ██╔══██╗██╔═══██╗
██╔████╔██║██║   ██║███████╗███████╗   ███████║██║   ██║
██║╚██╔╝██║██║   ██║╚════██║╚════██║   ██╔══██║██║   ██║
██║ ╚═╝ ██║╚██████╔╝███████║███████║██╗██║  ██║╚██████╔╝
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═╝ ╚═════╝
`;

export default function Dashboard() {
  const { t, locale } = useI18n();
  const { openModal } = useModal();
  const [stats, setStats] = useState<SystemStats>(mockStats);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [pipeline, setPipeline] = useState<PipelineStage[]>(mockPipeline);
  const [adapters, setAdapters] = useState<AdapterInfo[]>([]);
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isActivityLoading, setIsActivityLoading] = useState(true);
  const [isAdapterModalOpen, setIsAdapterModalOpen] = useState(false);
  const [isAdaptersLoading, setIsAdaptersLoading] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, activityData, pipelineData, projectsRes] = await Promise.all([
          fetchSystemStats(),
          fetchActivity(),
          fetchPipeline(),
          ApiClient.getProjects({ limit: 5 }),
        ]);
        setStats(statsData);
        setActivity(activityData);
        setPipeline(pipelineData);
        if (projectsRes.data) {
          setProjects(projectsRes.data.projects);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
        setIsActivityLoading(false);
      }
    }

    loadData();

    // Refresh data every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load adapters when modal opens
  const handleOpenAdapterModal = async () => {
    setIsAdaptersLoading(true);
    setIsAdapterModalOpen(true);

    try {
      // Always fetch fresh data when opening modal
      const adapterData = await fetchAdapters();
      setAdapters(adapterData);
    } catch (error) {
      console.error('Failed to fetch adapters:', error);
    } finally {
      setIsAdaptersLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] pt-12">
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* ASCII Logo Header */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6 overflow-hidden"
        >
          <pre className="ascii-art text-center text-[8px] sm:text-[10px] leading-tight hidden sm:block">
            {ASCII_LOGO}
          </pre>
          <div className="text-center mt-2">
            <span className="text-[#6b7280] text-xs">
              Multi-Agent AI Orchestration System v0.5.1
            </span>
          </div>
        </motion.div>

        {/* System Status Bar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6"
        >
          <SystemStatus lastRun={stats.lastRun} nextRun={stats.nextRun} />
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <StatsGrid stats={stats} />
        </motion.div>

        {/* Pipeline Visualization */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6"
        >
          <Pipeline stages={pipeline} />
        </motion.div>

        {/* Recent Projects */}
        {projects.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="mb-6"
          >
            <TerminalWindow title="recent_projects">
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {projects.slice(0, 3).map((project) => {
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
                      onClick={() => openModal('project', { id: project.id, title: project.name })}
                      className="p-3 rounded border border-[#21262d] hover:border-[#39ff14] cursor-pointer transition-colors bg-black/20"
                      whileHover={{ scale: 1.02 }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <TerminalBadge variant={getStatusColor(project.status)}>
                          {project.status.toUpperCase()}
                        </TerminalBadge>
                        {project.files_generated > 0 && (
                          <span className="text-[10px] text-[#39ff14]">
                            {project.files_generated} files
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-[#c0c0c0] truncate mb-1">
                        {project.name}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {project.tech_stack?.frontend && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-[#00ffff]/10 text-[#00ffff] rounded">
                            {project.tech_stack.frontend}
                          </span>
                        )}
                        {project.tech_stack?.backend && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-[#bd93f9]/10 text-[#bd93f9] rounded">
                            {project.tech_stack.backend}
                          </span>
                        )}
                        {project.tech_stack?.blockchain && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-[#ff6b35]/10 text-[#ff6b35] rounded">
                            {project.tech_stack.blockchain}
                          </span>
                        )}
                      </div>
                      {project.created_at && (
                        <div className="text-[10px] text-[#6b7280] mt-2">
                          {formatLocalDateTime(project.created_at, locale)}
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
              {projects.length > 3 && (
                <div className="mt-3 pt-3 border-t border-[#21262d] text-center">
                  <a
                    href="/projects"
                    className="text-xs text-[#00ffff] hover:text-[#39ff14] transition-colors"
                  >
                    {locale === 'ko' ? '모든 프로젝트 보기' : 'View all projects'} →
                  </a>
                </div>
              )}
            </TerminalWindow>
          </motion.div>
        )}

        {/* Two Column Layout */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Activity Feed Terminal */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <TerminalWindow title="activity.log" showDots>
              <ActivityFeed activities={activity} isLoading={isActivityLoading} />
            </TerminalWindow>
          </motion.div>

          {/* Right Column - Stacked */}
          <div className="space-y-6">
            {/* Signal Sources */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <TerminalWindow title="signals.conf">
                <button
                  onClick={handleOpenAdapterModal}
                  className="w-full text-left hover:bg-[#21262d]/30 -m-3 p-3 rounded transition-colors"
                >
                  <div className="space-y-2">
                    <div className="text-[#6b7280] text-xs mb-3 flex justify-between items-center">
                      <span>
                        <span className="text-[#bd93f9]"># </span>
                        Signal adapters configuration
                      </span>
                      <span className="text-[#00ffff] text-[10px] opacity-60 hover:opacity-100">
                        [click for details]
                      </span>
                    </div>
                    {rssCategories.map((cat) => (
                      <div key={cat.name} className="flex items-center justify-between py-1">
                        <span className="text-[#c0c0c0] text-xs">
                          <span className="text-[#00ffff]">[</span>
                          {cat.name.toLowerCase().replace(/ /g, '_')}
                          <span className="text-[#00ffff]">]</span>
                        </span>
                        <span className="tag tag-cyan">{cat.count} sources</span>
                      </div>
                    ))}
                    <div className="border-t border-[#21262d] pt-3 mt-3">
                      <div className="flex justify-between items-center">
                        <span className="text-[#6b7280] text-xs">total_adapters:</span>
                        <span className="text-[#39ff14] font-bold">9</span>
                      </div>
                    </div>
                  </div>
                </button>
              </TerminalWindow>
            </motion.div>

            {/* LLM Providers */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
            >
              <TerminalWindow title="llm.status">
                <div className="space-y-2">
                  <div className="text-[#6b7280] text-xs mb-3">
                    <span className="text-[#bd93f9]"># </span>
                    LLM provider status (hybrid routing)
                  </div>

                  {/* Local Models */}
                  <div className="mb-4">
                    <div className="text-[#00ffff] text-xs mb-2">
                      <span className="text-[#bd93f9]">@</span> Local Models (Ollama)
                    </div>
                    {['llama3.3:70b', 'qwen2.5:32b', 'phi4:14b'].map((model, idx) => (
                      <div key={model} className="flex items-center justify-between py-1 ml-4">
                        <span className="text-[#c0c0c0] text-xs">{model}</span>
                        <div className="flex items-center gap-2">
                          <span className="tag tag-green">FREE</span>
                          <motion.div
                            className="status-dot online"
                            animate={{ opacity: [1, 0.5, 1] }}
                            transition={{ duration: 2, repeat: Infinity, delay: idx * 0.2 }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* API Models */}
                  <div>
                    <div className="text-[#ff6b35] text-xs mb-2">
                      <span className="text-[#bd93f9]">@</span> API Models (Budget Controlled)
                    </div>
                    {aiProviders.map((provider, idx) => (
                      <div key={provider} className="flex items-center justify-between py-1 ml-4">
                        <span className="text-[#c0c0c0] text-xs">{provider}</span>
                        <div className="flex items-center gap-2">
                          <span className="tag tag-orange">PAID</span>
                          <motion.div
                            className="status-dot online"
                            animate={{ opacity: [1, 0.5, 1] }}
                            transition={{ duration: 2, repeat: Infinity, delay: idx * 0.3 }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-[#21262d] pt-3 mt-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#6b7280]">daily_budget:</span>
                      <span className="text-[#f1fa8c]">$50.00</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[#6b7280]">used_today:</span>
                      <span className="text-[#39ff14]">$12.45</span>
                    </div>
                  </div>
                </div>
              </TerminalWindow>
            </motion.div>
          </div>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-8 text-center"
        >
          <a
            href="https://github.com/MosslandOpenDevs/agentic-orchestrator"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-xs text-[#6b7280] hover:text-[#39ff14] transition-colors"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>MosslandOpenDevs/agentic-orchestrator</span>
          </a>
        </motion.div>
      </div>

      {/* Adapter Detail Modal */}
      <AdapterDetailModal
        isOpen={isAdapterModalOpen}
        onClose={() => setIsAdapterModalOpen(false)}
        adapters={adapters}
        isLoading={isAdaptersLoading}
      />
    </div>
  );
}

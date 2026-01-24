'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiSignal, type StatusResponse, type SignalTimelineResponse } from '@/lib/api';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';
import { SignalTimeline } from '@/components/visualization/SignalTimeline';
import { useModal } from '@/components/modals/useModal';

type ViewMode = 'status' | 'signals' | 'tech';

export default function SystemPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [viewMode, setViewMode] = useState<ViewMode>('status');
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [signals, setSignals] = useState<ApiSignal[]>([]);
  const [signalFilter, setSignalFilter] = useState<{ source?: string; category?: string }>({});
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [timelineData, setTimelineData] = useState<SignalTimelineResponse | null>(null);
  const [timelinePeriod, setTimelinePeriod] = useState<'24h' | '7d'>('24h');

  useEffect(() => {
    async function fetchStatus() {
      const [statusRes, timelineRes] = await Promise.all([
        ApiClient.getStatus(),
        ApiClient.getSignalTimeline('24h'),
      ]);

      if (statusRes.data) {
        setStatus(statusRes.data);
      }
      if (timelineRes.data) {
        setTimelineData(timelineRes.data);
      }
      setLoading(false);
    }
    fetchStatus();
  }, []);

  useEffect(() => {
    async function fetchTimeline() {
      const response = await ApiClient.getSignalTimeline(timelinePeriod);
      if (response.data) {
        setTimelineData(response.data);
      }
    }
    fetchTimeline();
  }, [timelinePeriod]);

  useEffect(() => {
    async function fetchSignals() {
      const response = await ApiClient.getSignals({
        limit: 100,
        source: signalFilter.source,
        category: signalFilter.category,
      });
      if (response.data) {
        setSignals(response.data.signals);
        const uniqueSources = [...new Set(response.data.signals.map(s => s.source))];
        const uniqueCategories = [...new Set(response.data.signals.map(s => s.category))];
        setSources(uniqueSources);
        setCategories(uniqueCategories);
      }
    }
    if (viewMode === 'signals') {
      fetchSignals();
    }
  }, [viewMode, signalFilter]);

  const tabs = [
    { id: 'status' as const, label: 'System Status', icon: '🟢' },
    { id: 'signals' as const, label: 'Signal Explorer', icon: '📡' },
    { id: 'tech' as const, label: 'Tech Stack', icon: '🔧' },
  ];

  const techStack = [
    { category: 'LLM Providers', items: ['Claude (Anthropic)', 'GPT-4 (OpenAI)', 'Ollama (Local)'] },
    { category: 'Data Sources', items: ['45+ RSS Feeds', 'GitHub API', 'Custom APIs'] },
    { category: 'Storage', items: ['SQLite Database', 'GitHub Issues', 'Markdown Files'] },
    { category: 'Automation', items: ['PM2 Scheduler', 'Daily Signal Collection', 'Auto Debate Trigger'] },
  ];

  const scoreColors = (score: number) => {
    if (score >= 8) return 'text-[#39ff14]';
    if (score >= 6) return 'text-[#00ffff]';
    if (score >= 4) return 'text-[#f1fa8c]';
    return 'text-[#ff6b35]';
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
          <h1 className="text-2xl font-bold text-[#00ffff] mb-2">
            System Overview
          </h1>
          <p className="text-sm text-[#6b7280]">
            Monitor system health, explore raw signals, and view technical details
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
                  ? 'bg-[#00ffff]/10 text-[#00ffff] border border-[#00ffff]/30'
                  : 'text-[#6b7280] hover:bg-[#21262d] hover:text-[#c0c0c0]'
                }
              `}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Status View */}
        {viewMode === 'status' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Component Health */}
            <TerminalWindow title="COMPONENT_HEALTH" className="mb-6">
              {loading ? (
                <div className="text-center py-8 text-[#00ffff] animate-pulse">
                  Checking system status...
                </div>
              ) : status ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(status.components).map(([name, comp]) => (
                    <div key={name} className="p-4 rounded bg-black/20 border border-[#21262d]">
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${
                          comp.status === 'healthy' ? 'bg-[#39ff14]' : 'bg-[#ff5555]'
                        }`} />
                        <span className="text-sm text-[#c0c0c0] uppercase">{name}</span>
                      </div>
                      <div className={`text-xs ${
                        comp.status === 'healthy' ? 'text-[#39ff14]' : 'text-[#ff5555]'
                      }`}>
                        {comp.status}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-[#ff5555]">
                  Failed to fetch system status
                </div>
              )}
            </TerminalWindow>

            {/* Stats */}
            {status && (
              <TerminalWindow title="TODAY_STATS" className="mb-6">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {[
                    { label: 'Signals', value: status.stats.signals_today, color: 'cyan' },
                    { label: 'Debates', value: status.stats.debates_today, color: 'orange' },
                    { label: 'Ideas', value: status.stats.ideas_generated, color: 'green' },
                    { label: 'Plans', value: status.stats.plans_created, color: 'purple' },
                    { label: 'Agents', value: status.stats.agents_active, color: 'cyan' },
                  ].map((stat) => (
                    <div key={stat.label} className="text-center p-4 rounded bg-black/20 border border-[#21262d]">
                      <div className={`text-2xl font-bold
                        ${stat.color === 'cyan' ? 'text-[#00ffff]' : ''}
                        ${stat.color === 'orange' ? 'text-[#ff6b35]' : ''}
                        ${stat.color === 'green' ? 'text-[#39ff14]' : ''}
                        ${stat.color === 'purple' ? 'text-[#bd93f9]' : ''}
                      `}>
                        {stat.value}
                      </div>
                      <div className="text-xs text-[#6b7280] mt-1">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </TerminalWindow>
            )}

            {/* Signal Timeline */}
            <TerminalWindow title="SIGNAL_TIMELINE" className="mb-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex gap-2">
                  <button
                    onClick={() => setTimelinePeriod('24h')}
                    className={`text-xs px-3 py-1 rounded transition-colors ${
                      timelinePeriod === '24h'
                        ? 'bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]/30'
                        : 'text-[#6b7280] hover:bg-[#21262d]'
                    }`}
                  >
                    Last 24h
                  </button>
                  <button
                    onClick={() => setTimelinePeriod('7d')}
                    className={`text-xs px-3 py-1 rounded transition-colors ${
                      timelinePeriod === '7d'
                        ? 'bg-[#39ff14]/20 text-[#39ff14] border border-[#39ff14]/30'
                        : 'text-[#6b7280] hover:bg-[#21262d]'
                    }`}
                  >
                    Last 7 days
                  </button>
                </div>
              </div>
              {timelineData ? (
                <SignalTimeline
                  data={timelineData.slots}
                  totalSignals={timelineData.total}
                  period={timelinePeriod}
                  showDetails={true}
                />
              ) : (
                <div className="text-center py-8 text-[#6b7280]">
                  Loading timeline data...
                </div>
              )}
            </TerminalWindow>

            {/* Pipeline */}
            <TerminalWindow title="PIPELINE_STAGES">
              <div className="flex flex-wrap gap-2 py-4">
                {[
                  { name: 'IDEATION', desc: 'Generate ideas', color: 'yellow' },
                  { name: 'PLANNING', desc: 'Create plans', color: 'orange' },
                  { name: 'REVIEW', desc: 'Agent debate', color: 'purple' },
                  { name: 'DEVELOPMENT', desc: 'Build feature', color: 'blue' },
                  { name: 'QA', desc: 'Quality check', color: 'cyan' },
                  { name: 'DONE', desc: 'Completed', color: 'green' },
                ].map((stage, idx) => (
                  <div key={stage.name} className="flex items-center gap-2">
                    <div className="p-3 rounded border border-[#21262d] bg-black/20">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full
                          ${stage.color === 'yellow' ? 'bg-[#f1fa8c]' : ''}
                          ${stage.color === 'orange' ? 'bg-[#ff6b35]' : ''}
                          ${stage.color === 'purple' ? 'bg-[#bd93f9]' : ''}
                          ${stage.color === 'blue' ? 'bg-[#6272a4]' : ''}
                          ${stage.color === 'cyan' ? 'bg-[#00ffff]' : ''}
                          ${stage.color === 'green' ? 'bg-[#39ff14]' : ''}
                        `} />
                        <span className="text-xs text-[#c0c0c0]">{stage.name}</span>
                      </div>
                      <div className="text-[10px] text-[#6b7280] mt-1">{stage.desc}</div>
                    </div>
                    {idx < 5 && <span className="text-[#21262d]">→</span>}
                  </div>
                ))}
              </div>
            </TerminalWindow>
          </motion.div>
        )}

        {/* Signals View */}
        {viewMode === 'signals' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Filters */}
            <TerminalWindow title="FILTERS" className="mb-6">
              <div className="flex flex-wrap gap-4">
                <div>
                  <label className="text-xs text-[#6b7280] block mb-1">Source</label>
                  <select
                    value={signalFilter.source || ''}
                    onChange={(e) => setSignalFilter({ ...signalFilter, source: e.target.value || undefined })}
                    className="input-cli text-sm"
                  >
                    <option value="">All Sources</option>
                    {sources.map(source => (
                      <option key={source} value={source}>{source}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[#6b7280] block mb-1">Category</label>
                  <select
                    value={signalFilter.category || ''}
                    onChange={(e) => setSignalFilter({ ...signalFilter, category: e.target.value || undefined })}
                    className="input-cli text-sm"
                  >
                    <option value="">All Categories</option>
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>
              </div>
            </TerminalWindow>

            {/* Signals List */}
            <TerminalWindow title={`RAW_SIGNALS (${signals.length})`}>
              {signals.length === 0 ? (
                <div className="text-center py-12 text-[#6b7280]">
                  No signals found
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {signals.map((signal, idx) => (
                    <motion.div
                      key={signal.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.01 }}
                      onClick={() => openModal('signal', { ...signal, title: signal.title })}
                      className="p-3 rounded border border-[#21262d] hover:border-[#00ffff] cursor-pointer transition-colors bg-black/20"
                    >
                      <div className="flex items-start gap-3">
                        <div className={`text-lg font-bold w-10 text-center ${scoreColors(signal.score)}`}>
                          {signal.score.toFixed(1)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <TerminalBadge variant="cyan">{signal.source}</TerminalBadge>
                            <TerminalBadge variant="purple">{signal.category}</TerminalBadge>
                          </div>
                          <div className="text-sm text-[#c0c0c0] truncate">{signal.title}</div>
                          {signal.topics && signal.topics.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {signal.topics.slice(0, 3).map(topic => (
                                <span key={topic} className="text-[10px] text-[#bd93f9]">#{topic}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </TerminalWindow>
          </motion.div>
        )}

        {/* Tech Stack View */}
        {viewMode === 'tech' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="grid md:grid-cols-2 gap-6">
              {techStack.map((stack, idx) => (
                <TerminalWindow key={stack.category} title={stack.category.toUpperCase().replace(/ /g, '_')}>
                  <div className="space-y-2">
                    {stack.items.map((item) => (
                      <div key={item} className="flex items-center gap-2 text-sm">
                        <span className="text-[#39ff14]">•</span>
                        <span className="text-[#c0c0c0]">{item}</span>
                      </div>
                    ))}
                  </div>
                </TerminalWindow>
              ))}
            </div>

            {/* GitHub Link */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-8 text-center"
            >
              <a
                href="https://github.com/MosslandOpenDevs/agentic-orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded border border-[#21262d] text-sm text-[#6b7280] hover:text-[#39ff14] hover:border-[#39ff14] transition-colors"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                View Source Code
              </a>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

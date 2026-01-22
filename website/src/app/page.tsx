'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { SystemStatus } from '@/components/SystemStatus';
import { StatsGrid } from '@/components/Stats';
import { Pipeline } from '@/components/Pipeline';
import { ActivityFeed } from '@/components/ActivityFeed';
import { TerminalWindow } from '@/components/TerminalWindow';
import { mockStats, mockActivity, mockPipeline, rssCategories, aiProviders } from '@/data/mock';

const ASCII_LOGO = `
███╗   ███╗ ██████╗ ███████╗███████╗    █████╗  ██████╗
████╗ ████║██╔═══██╗██╔════╝██╔════╝   ██╔══██╗██╔═══██╗
██╔████╔██║██║   ██║███████╗███████╗   ███████║██║   ██║
██║╚██╔╝██║██║   ██║╚════██║╚════██║   ██╔══██║██║   ██║
██║ ╚═╝ ██║╚██████╔╝███████║███████║██╗██║  ██║╚██████╔╝
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═╝ ╚═════╝
`;

export default function Dashboard() {
  const { t } = useI18n();

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
              Multi-Agent AI Orchestration System v0.4.0
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
          <SystemStatus lastRun={mockStats.lastRun} nextRun={mockStats.nextRun} />
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <StatsGrid stats={mockStats} />
        </motion.div>

        {/* Pipeline Visualization */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6"
        >
          <Pipeline stages={mockPipeline} />
        </motion.div>

        {/* Two Column Layout */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Activity Feed Terminal */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <TerminalWindow title="activity.log" showDots>
              <ActivityFeed activities={mockActivity} />
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
                <div className="space-y-2">
                  <div className="text-[#6b7280] text-xs mb-3">
                    <span className="text-[#bd93f9]"># </span>
                    Signal adapters configuration
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
                      <span className="text-[#39ff14] font-bold">45</span>
                    </div>
                  </div>
                </div>
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
            href="https://github.com/mossland/agentic-orchestrator"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-xs text-[#6b7280] hover:text-[#39ff14] transition-colors"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>mossland/agentic-orchestrator</span>
          </a>
        </motion.div>
      </div>
    </div>
  );
}

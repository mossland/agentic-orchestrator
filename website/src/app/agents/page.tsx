'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { TerminalWindow } from '@/components/TerminalWindow';
import { useModal } from '@/components/modals/useModal';
import { ApiClient } from '@/lib/api';

interface AgentFromApi {
  id: string;
  name: string;
  role: string;
  phase: string;
  handle?: string;
  expertise?: string[];
  personality: Record<string, string | number>;
}

// Fallback agent data (used when API is unavailable)
const fallbackAgents = {
  divergence: [
    { id: 'alex_kim', name: 'Alex Kim', role: 'Tech Entrepreneur', traits: '낙관적, 직관적, 지지적, 혁신적', expertise: 'AI/ML Startups' },
    { id: 'sarah_park', name: 'Sarah Park', role: 'Venture Capitalist', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Investment Analysis' },
    { id: 'james_lee', name: 'James Lee', role: 'Product Manager', traits: '낙관적, 분석적, 지지적, 실용적', expertise: 'Product Strategy' },
    { id: 'mina_choi', name: 'Mina Choi', role: 'UX Designer', traits: '낙관적, 직관적, 지지적, 혁신적', expertise: 'User Experience' },
    { id: 'david_hong', name: 'David Hong', role: 'Blockchain Developer', traits: '신중한, 분석적, 도전적, 혁신적', expertise: 'Smart Contracts' },
    { id: 'emily_yoon', name: 'Emily Yoon', role: 'Marketing Strategist', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Growth Marketing' },
    { id: 'chris_oh', name: 'Chris Oh', role: 'Security Expert', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Cybersecurity' },
    { id: 'ryan_jung', name: 'Ryan Jung', role: 'Game Designer', traits: '낙관적, 직관적, 도전적, 혁신적', expertise: 'Game Mechanics' },
    { id: 'luna_shin', name: 'Luna Shin', role: 'Community Manager', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Community Building' },
    { id: 'hana_kang', name: 'Hana Kang', role: 'Content Creator', traits: '낙관적, 직관적, 지지적, 혁신적', expertise: 'Content Strategy' },
    { id: 'tony_baek', name: 'Tony Baek', role: 'DevOps Engineer', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Infrastructure' },
    { id: 'jina_nam', name: 'Jina Nam', role: 'Data Scientist', traits: '신중한, 분석적, 도전적, 혁신적', expertise: 'Data Analysis' },
    { id: 'kevin_lim', name: 'Kevin Lim', role: 'Mobile Developer', traits: '낙관적, 분석적, 지지적, 실용적', expertise: 'Mobile Apps' },
    { id: 'yuri_han', name: 'Yuri Han', role: 'AR/VR Specialist', traits: '낙관적, 직관적, 도전적, 혁신적', expertise: 'Immersive Tech' },
    { id: 'steve_kwon', name: 'Steve Kwon', role: 'Finance Expert', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Financial Modeling' },
    { id: 'joy_song', name: 'Joy Song', role: 'Partnership Lead', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Business Development' },
  ],
  convergence: [
    { id: 'michael_chen', name: 'Michael Chen', role: 'Strategy Consultant', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Business Strategy' },
    { id: 'jennifer_kim', name: 'Jennifer Kim', role: 'Innovation Director', traits: '낙관적, 분석적, 지지적, 혁신적', expertise: 'Innovation Management' },
    { id: 'paul_ryu', name: 'Paul Ryu', role: 'Portfolio Manager', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Portfolio Optimization' },
    { id: 'grace_seo', name: 'Grace Seo', role: 'Research Lead', traits: '신중한, 분석적, 지지적, 혁신적', expertise: 'Market Research' },
    { id: 'daniel_park', name: 'Daniel Park', role: 'Tech Architect', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'System Architecture' },
    { id: 'soyeon_lee', name: 'Soyeon Lee', role: 'Risk Analyst', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'Risk Assessment' },
    { id: 'hyun_cho', name: 'Hyun Cho', role: 'Quality Lead', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Quality Assurance' },
    { id: 'amy_hwang', name: 'Amy Hwang', role: 'Integration Specialist', traits: '낙관적, 분석적, 지지적, 실용적', expertise: 'System Integration' },
  ],
  planning: [
    { id: 'marcus_ko', name: 'Marcus Ko', role: 'Project Director', traits: '낙관적, 분석적, 지지적, 실용적', expertise: 'Project Management' },
    { id: 'lisa_jung', name: 'Lisa Jung', role: 'Agile Coach', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Agile Methodology' },
    { id: 'andrew_yoo', name: 'Andrew Yoo', role: 'Operations Manager', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Operations' },
    { id: 'nina_song', name: 'Nina Song', role: 'Resource Planner', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Resource Management' },
    { id: 'jason_chung', name: 'Jason Chung', role: 'Roadmap Owner', traits: '낙관적, 분석적, 도전적, 혁신적', expertise: 'Product Roadmap' },
    { id: 'eric_moon', name: 'Eric Moon', role: 'Release Manager', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Release Management' },
    { id: 'mia_jang', name: 'Mia Jang', role: 'Metrics Lead', traits: '신중한, 분석적, 도전적, 실용적', expertise: 'KPI & Metrics' },
    { id: 'tom_ahn', name: 'Tom Ahn', role: 'Change Manager', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Change Management' },
    { id: 'anna_cho', name: 'Anna Cho', role: 'Stakeholder Lead', traits: '낙관적, 직관적, 지지적, 실용적', expertise: 'Stakeholder Relations' },
    { id: 'ben_park', name: 'Ben Park', role: 'Delivery Lead', traits: '신중한, 분석적, 지지적, 실용적', expertise: 'Delivery Management' },
  ],
};

interface AgentCardProps {
  agent: AgentFromApi | typeof fallbackAgents.divergence[0];
  index: number;
  phase: string;
  onClick: () => void;
}

function AgentCard({ agent, index, phase, onClick }: AgentCardProps) {
  const phaseColors = {
    divergence: { border: 'border-[#00ffff]/30', accent: 'text-[#00ffff]' },
    convergence: { border: 'border-[#bd93f9]/30', accent: 'text-[#bd93f9]' },
    planning: { border: 'border-[#39ff14]/30', accent: 'text-[#39ff14]' },
  };
  const colors = phaseColors[phase as keyof typeof phaseColors];

  // Get traits string - either from personality object or traits field
  const traits = 'personality' in agent && typeof agent.personality === 'object'
    ? Object.values(agent.personality).join(', ')
    : ('traits' in agent ? agent.traits : '');

  // Get expertise - array or string
  const expertise = 'expertise' in agent
    ? (Array.isArray(agent.expertise) ? agent.expertise.join(', ') : agent.expertise)
    : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02 }}
      onClick={onClick}
      className={`card-cli p-3 border ${colors.border} hover:border-opacity-100 transition-all cursor-pointer hover:bg-[#21262d]/50`}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <span className={`${colors.accent} text-xs font-bold`}>{agent.name}</span>
          <div className="text-[10px] text-[#6b7280]">{agent.role}</div>
        </div>
        <div className="status-dot online" style={{ width: 6, height: 6 }} />
      </div>
      {expertise && (
        <div className="text-[10px] text-[#6b7280] mb-2">
          <span className="text-[#bd93f9]">expertise:</span> {expertise}
        </div>
      )}
      <div className="text-[10px] text-[#f1fa8c] line-clamp-2">
        {traits}
      </div>
    </motion.div>
  );
}

export default function AgentsPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [apiAgents, setApiAgents] = useState<{
    divergence: AgentFromApi[];
    convergence: AgentFromApi[];
    planning: AgentFromApi[];
  }>({
    divergence: [],
    convergence: [],
    planning: [],
  });
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);

  useEffect(() => {
    async function fetchAgents() {
      try {
        const response = await ApiClient.getAgents();
        if (response.data && response.data.agents.length > 0) {
          // Group agents by phase
          const agentList = response.data.agents as AgentFromApi[];
          const grouped = {
            divergence: agentList.filter(a => a.phase === 'divergence'),
            convergence: agentList.filter(a => a.phase === 'convergence'),
            planning: agentList.filter(a => a.phase === 'planning'),
          };
          setApiAgents(grouped);
        } else {
          setUsingFallback(true);
        }
      } catch (error) {
        console.error('Failed to fetch agents:', error);
        setUsingFallback(true);
      } finally {
        setLoading(false);
      }
    }

    fetchAgents();
  }, []);

  const handleAgentClick = (agent: AgentFromApi | typeof fallbackAgents.divergence[0], phase: string) => {
    // Convert to the format expected by AgentDetail
    const agentData = {
      id: agent.id,
      title: agent.name,
      name: agent.name,
      role: agent.role,
      phase: phase,
      handle: 'handle' in agent ? agent.handle : undefined,
      personality: 'personality' in agent && typeof agent.personality === 'object'
        ? {
            creativity: 7,
            analytical: 7,
            risk_tolerance: 5,
            collaboration: 7,
          }
        : {
            creativity: 7,
            analytical: 7,
            risk_tolerance: 5,
            collaboration: 7,
          },
      description: `${agent.role} agent specialized in ${'expertise' in agent ? (Array.isArray(agent.expertise) ? agent.expertise.join(', ') : agent.expertise) : 'various domains'}`,
    };
    openModal('agent', agentData);
  };

  // Use fallback data if API failed
  const divergenceAgents = usingFallback ? fallbackAgents.divergence : apiAgents.divergence;
  const convergenceAgents = usingFallback ? fallbackAgents.convergence : apiAgents.convergence;
  const planningAgents = usingFallback ? fallbackAgents.planning : apiAgents.planning;

  return (
    <div className="min-h-screen bg-[#0a0a0a] pt-12">
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6"
        >
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[#00ffff] text-sm">$</span>
            <span className="text-[#c0c0c0] text-sm">moss-ao agents --list</span>
          </div>
          <h1 className="text-[#39ff14] text-xl font-bold glow-green">
            {t('agents.pageTitle').toUpperCase()}
          </h1>
          <p className="text-[#6b7280] text-xs mt-1">
            {t('agents.pageSubtitle')}
            {usingFallback && <span className="text-[#f1fa8c] ml-2">{t('agents.cachedData')}</span>}
          </p>
        </motion.div>

        {loading ? (
          <div className="text-center py-12">
            <div className="text-[#39ff14] animate-pulse">
              {t('agents.loading')}
              <span className="cursor-blink">_</span>
            </div>
          </div>
        ) : (
          <>
            {/* Divergence Agents */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mb-6"
            >
              <TerminalWindow title="divergence_agents.json">
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="tag tag-cyan">{t('agents.phaseNum.1')}</span>
                    <span className="text-[#00ffff] text-xs font-bold">{t('agents.phase.divergence')}</span>
                    <span className="text-[#6b7280] text-xs">- {t('agents.phaseDesc.divergence')} ({divergenceAgents.length} {t('agents.agents')})</span>
                  </div>
                  <p className="text-[10px] text-[#6b7280]">
                    {t('agents.phaseInfo.divergence')}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                  {divergenceAgents.map((agent, idx) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      index={idx}
                      phase="divergence"
                      onClick={() => handleAgentClick(agent, 'divergence')}
                    />
                  ))}
                </div>
              </TerminalWindow>
            </motion.div>

            {/* Convergence Agents */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-6"
            >
              <TerminalWindow title="convergence_agents.json">
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="tag tag-purple">{t('agents.phaseNum.2')}</span>
                    <span className="text-[#bd93f9] text-xs font-bold">{t('agents.phase.convergence')}</span>
                    <span className="text-[#6b7280] text-xs">- {t('agents.phaseDesc.convergence')} ({convergenceAgents.length} {t('agents.agents')})</span>
                  </div>
                  <p className="text-[10px] text-[#6b7280]">
                    {t('agents.phaseInfo.convergence')}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                  {convergenceAgents.map((agent, idx) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      index={idx}
                      phase="convergence"
                      onClick={() => handleAgentClick(agent, 'convergence')}
                    />
                  ))}
                </div>
              </TerminalWindow>
            </motion.div>

            {/* Planning Agents */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mb-6"
            >
              <TerminalWindow title="planning_agents.json">
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="tag tag-green">{t('agents.phaseNum.3')}</span>
                    <span className="text-[#39ff14] text-xs font-bold">{t('agents.phase.planning')}</span>
                    <span className="text-[#6b7280] text-xs">- {t('agents.phaseDesc.planning')} ({planningAgents.length} {t('agents.agents')})</span>
                  </div>
                  <p className="text-[10px] text-[#6b7280]">
                    {t('agents.phaseInfo.planning')}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                  {planningAgents.map((agent, idx) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      index={idx}
                      phase="planning"
                      onClick={() => handleAgentClick(agent, 'planning')}
                    />
                  ))}
                </div>
              </TerminalWindow>
            </motion.div>
          </>
        )}

        {/* Personality Axes */}
        {!loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <TerminalWindow title="personality_system.md">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <span className="text-[#00ffff] text-xs font-bold">{t('agents.thinkingStyle')}</span>
                    <div className="text-[10px] text-[#6b7280] mt-1">
                      <span className="text-[#39ff14]">{t('agents.optimistic')}</span> vs <span className="text-[#ff5555]">{t('agents.cautious')}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[#bd93f9] text-xs font-bold">{t('agents.decisionStyle')}</span>
                    <div className="text-[10px] text-[#6b7280] mt-1">
                      <span className="text-[#f1fa8c]">{t('agents.intuitive')}</span> vs <span className="text-[#00ffff]">{t('agents.analytical')}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="text-[#ff6b35] text-xs font-bold">{t('agents.communicationStyle')}</span>
                    <div className="text-[10px] text-[#6b7280] mt-1">
                      <span className="text-[#ff6b35]">{t('agents.challenger')}</span> vs <span className="text-[#39ff14]">{t('agents.supporter')}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[#f1fa8c] text-xs font-bold">{t('agents.actionStyle')}</span>
                    <div className="text-[10px] text-[#6b7280] mt-1">
                      <span className="text-[#bd93f9]">{t('agents.innovative')}</span> vs <span className="text-[#c0c0c0]">{t('agents.pragmatic')}</span>
                    </div>
                  </div>
                </div>
              </div>
            </TerminalWindow>
          </motion.div>
        )}
      </div>
    </div>
  );
}

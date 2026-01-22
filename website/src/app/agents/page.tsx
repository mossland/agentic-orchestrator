'use client';

import { motion } from 'framer-motion';
import { TerminalWindow } from '@/components/TerminalWindow';

// Agent data matching the Python persona catalog
const agents = {
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

function AgentCard({ agent, index, phase }: { agent: typeof agents.divergence[0]; index: number; phase: string }) {
  const phaseColors = {
    divergence: { border: 'border-[#00ffff]/30', accent: 'text-[#00ffff]' },
    convergence: { border: 'border-[#bd93f9]/30', accent: 'text-[#bd93f9]' },
    planning: { border: 'border-[#39ff14]/30', accent: 'text-[#39ff14]' },
  };
  const colors = phaseColors[phase as keyof typeof phaseColors];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02 }}
      className={`card-cli p-3 border ${colors.border} hover:border-opacity-100 transition-all`}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <span className={`${colors.accent} text-xs font-bold`}>{agent.name}</span>
          <div className="text-[10px] text-[#6b7280]">{agent.role}</div>
        </div>
        <div className="status-dot online" style={{ width: 6, height: 6 }} />
      </div>
      <div className="text-[10px] text-[#6b7280] mb-2">
        <span className="text-[#bd93f9]">expertise:</span> {agent.expertise}
      </div>
      <div className="text-[10px] text-[#f1fa8c]">
        {agent.traits}
      </div>
    </motion.div>
  );
}

export default function AgentsPage() {
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
            AGENT PERSONAS
          </h1>
          <p className="text-[#6b7280] text-xs mt-1">
            34 unique AI agents with distinct personalities for multi-stage debates
          </p>
        </motion.div>

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
                <span className="tag tag-cyan">PHASE 1</span>
                <span className="text-[#00ffff] text-xs font-bold">Divergence</span>
                <span className="text-[#6b7280] text-xs">- Idea generation (16 agents)</span>
              </div>
              <p className="text-[10px] text-[#6b7280]">
                Creative agents that generate diverse ideas and perspectives
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {agents.divergence.map((agent, idx) => (
                <AgentCard key={agent.id} agent={agent} index={idx} phase="divergence" />
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
                <span className="tag tag-purple">PHASE 2</span>
                <span className="text-[#bd93f9] text-xs font-bold">Convergence</span>
                <span className="text-[#6b7280] text-xs">- Evaluation & filtering (8 agents)</span>
              </div>
              <p className="text-[10px] text-[#6b7280]">
                Analytical agents that evaluate, score, and merge ideas
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {agents.convergence.map((agent, idx) => (
                <AgentCard key={agent.id} agent={agent} index={idx} phase="convergence" />
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
                <span className="tag tag-green">PHASE 3</span>
                <span className="text-[#39ff14] text-xs font-bold">Planning</span>
                <span className="text-[#6b7280] text-xs">- Plan creation (10 agents)</span>
              </div>
              <p className="text-[10px] text-[#6b7280]">
                Execution-focused agents that create actionable plans
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {agents.planning.map((agent, idx) => (
                <AgentCard key={agent.id} agent={agent} index={idx} phase="planning" />
              ))}
            </div>
          </TerminalWindow>
        </motion.div>

        {/* Personality Axes */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <TerminalWindow title="personality_system.md">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <span className="text-[#00ffff] text-xs font-bold">Thinking Style</span>
                  <div className="text-[10px] text-[#6b7280] mt-1">
                    <span className="text-[#39ff14]">Optimistic</span> vs <span className="text-[#ff5555]">Cautious</span>
                  </div>
                </div>
                <div>
                  <span className="text-[#bd93f9] text-xs font-bold">Decision Style</span>
                  <div className="text-[10px] text-[#6b7280] mt-1">
                    <span className="text-[#f1fa8c]">Intuitive</span> vs <span className="text-[#00ffff]">Analytical</span>
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <span className="text-[#ff6b35] text-xs font-bold">Communication Style</span>
                  <div className="text-[10px] text-[#6b7280] mt-1">
                    <span className="text-[#ff6b35]">Challenger</span> vs <span className="text-[#39ff14]">Supporter</span>
                  </div>
                </div>
                <div>
                  <span className="text-[#f1fa8c] text-xs font-bold">Action Style</span>
                  <div className="text-[10px] text-[#6b7280] mt-1">
                    <span className="text-[#bd93f9]">Innovative</span> vs <span className="text-[#c0c0c0]">Pragmatic</span>
                  </div>
                </div>
              </div>
            </div>
          </TerminalWindow>
        </motion.div>
      </div>
    </div>
  );
}

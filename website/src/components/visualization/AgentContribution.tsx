'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';

// Helper function to extract readable text from JSON content
function extractReadableText(content: string): string {
  if (!content) return '';

  try {
    // Remove markdown code block if present
    const codeBlockMatch = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    const jsonStr = codeBlockMatch ? codeBlockMatch[1].trim() : content.trim();

    const parsed = JSON.parse(jsonStr);

    // Try to extract readable text in order of preference
    if (parsed.core_analysis) return parsed.core_analysis;
    if (parsed.idea_title) return parsed.idea_title;
    if (parsed.proposal?.description) return parsed.proposal.description;
    if (parsed.summary) return parsed.summary;

    // Get first string value
    for (const value of Object.values(parsed)) {
      if (typeof value === 'string' && value.length > 10) {
        return value;
      }
    }
    return content;
  } catch {
    // Not JSON - try regex extraction
    const coreMatch = content.match(/"core_analysis"\s*:\s*"([^"]+)"/);
    if (coreMatch) return coreMatch[1];
    const titleMatch = content.match(/"idea_title"\s*:\s*"([^"]+)"/);
    if (titleMatch) return titleMatch[1];
    // Return without JSON artifacts
    return content.replace(/```json/g, '').replace(/```/g, '').replace(/^\s*\{/g, '').slice(0, 150);
  }
}

interface DebateMessage {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_handle: string | null;
  message_type: string;
  content: string;
  content_ko: string | null;
  created_at: string | null;
}

interface AgentContributionProps {
  messages: DebateMessage[];
  phase?: string;
  showDetails?: boolean;
  maxAgents?: number;
}

interface AgentStats {
  id: string;
  name: string;
  handle: string | null;
  messageCount: number;
  influence: 'high' | 'medium' | 'low';
  stance: 'advocate' | 'challenger' | 'refiner' | 'neutral';
  keyQuote: string;
  phase: string;
}

// Analyze agent contributions from messages
function analyzeContributions(messages: DebateMessage[]): AgentStats[] {
  const agentMap = new Map<string, {
    id: string;
    name: string;
    handle: string | null;
    messages: DebateMessage[];
    types: Set<string>;
  }>();

  // Group messages by agent
  for (const msg of messages) {
    if (!agentMap.has(msg.agent_id)) {
      agentMap.set(msg.agent_id, {
        id: msg.agent_id,
        name: msg.agent_name,
        handle: msg.agent_handle,
        messages: [],
        types: new Set(),
      });
    }
    const agent = agentMap.get(msg.agent_id)!;
    agent.messages.push(msg);
    agent.types.add(msg.message_type);
  }

  // Analyze each agent
  const stats: AgentStats[] = [];
  const maxMessages = Math.max(...Array.from(agentMap.values()).map(a => a.messages.length), 1);

  for (const [, agent] of agentMap) {
    // Determine influence based on message count relative to max
    const ratio = agent.messages.length / maxMessages;
    const influence: 'high' | 'medium' | 'low' =
      ratio >= 0.7 ? 'high' : ratio >= 0.4 ? 'medium' : 'low';

    // Determine stance based on message types and content
    let stance: 'advocate' | 'challenger' | 'refiner' | 'neutral' = 'neutral';
    const types = Array.from(agent.types);

    if (types.some(t => t.includes('critique') || t.includes('challenge') || t.includes('risk'))) {
      stance = 'challenger';
    } else if (types.some(t => t.includes('refine') || t.includes('synthesis') || t.includes('merge'))) {
      stance = 'refiner';
    } else if (types.some(t => t.includes('proposal') || t.includes('idea') || t.includes('support'))) {
      stance = 'advocate';
    }

    // Get a key quote (first message, parsed and truncated)
    const firstMsg = agent.messages[0];
    const readableContent = extractReadableText(firstMsg.content);
    const keyQuote = readableContent.slice(0, 100) + (readableContent.length > 100 ? '...' : '');

    // Determine phase from message type
    let phase = 'general';
    if (types.some(t => t.includes('divergence') || t.includes('brainstorm'))) {
      phase = 'divergence';
    } else if (types.some(t => t.includes('convergence') || t.includes('evaluate'))) {
      phase = 'convergence';
    } else if (types.some(t => t.includes('planning') || t.includes('plan'))) {
      phase = 'planning';
    }

    stats.push({
      id: agent.id,
      name: agent.name,
      handle: agent.handle,
      messageCount: agent.messages.length,
      influence,
      stance,
      keyQuote,
      phase,
    });
  }

  // Sort by message count (most active first)
  stats.sort((a, b) => b.messageCount - a.messageCount);

  return stats;
}

export function AgentContribution({
  messages,
  phase,
  showDetails = true,
  maxAgents = 10,
}: AgentContributionProps) {
  const { t, locale } = useI18n();

  const agentStats = useMemo(() => {
    const stats = analyzeContributions(messages);
    return stats.slice(0, maxAgents);
  }, [messages, maxAgents]);

  // Calculate summary stats
  const summary = useMemo(() => {
    const advocates = agentStats.filter(a => a.stance === 'advocate').length;
    const challengers = agentStats.filter(a => a.stance === 'challenger').length;
    const refiners = agentStats.filter(a => a.stance === 'refiner').length;
    const total = agentStats.length;

    return {
      advocates,
      challengers,
      refiners,
      advocatePercent: total > 0 ? Math.round((advocates / total) * 100) : 0,
      challengerPercent: total > 0 ? Math.round((challengers / total) * 100) : 0,
      refinerPercent: total > 0 ? Math.round((refiners / total) * 100) : 0,
    };
  }, [agentStats]);

  const getInfluenceColor = (influence: string) => {
    switch (influence) {
      case 'high': return 'text-[#39ff14]';
      case 'medium': return 'text-[#ff6b35]';
      case 'low': return 'text-[#6b7280]';
      default: return 'text-[#6b7280]';
    }
  };

  const getStanceColor = (stance: string) => {
    switch (stance) {
      case 'advocate': return 'bg-[#39ff14]/20 text-[#39ff14] border-[#39ff14]/30';
      case 'challenger': return 'bg-[#ff6b35]/20 text-[#ff6b35] border-[#ff6b35]/30';
      case 'refiner': return 'bg-[#00ffff]/20 text-[#00ffff] border-[#00ffff]/30';
      default: return 'bg-[#6b7280]/20 text-[#6b7280] border-[#6b7280]/30';
    }
  };

  const getStanceLabel = (stance: string) => {
    return t(`agentContribution.stance.${stance}`);
  };

  if (agentStats.length === 0) {
    return (
      <div className="text-center py-4 text-[#6b7280] text-sm">
        {t('agentContribution.noContributions')}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('agentContribution.title')}
        </span>
        <span className="text-xs text-[#c0c0c0]">
          {agentStats.length} {t('agentContribution.agents')}
        </span>
      </div>

      {/* Agent list */}
      {showDetails && (
        <div className="space-y-3">
          {agentStats.map((agent, idx) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="border-l-2 border-[#21262d] pl-3 py-2 hover:border-[#39ff14]/50 transition-colors"
            >
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-[#00ffff] font-bold text-sm">
                  @{agent.handle || agent.name.toLowerCase().replace(/\s+/g, '_')}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded border ${getStanceColor(agent.stance)}`}>
                  {getStanceLabel(agent.stance)}
                </span>
                {phase && (
                  <span className="text-xs text-[#bd93f9]">({phase})</span>
                )}
              </div>

              <div className="flex items-center gap-4 text-xs mb-2">
                <span className="text-[#6b7280]">
                  {t('agentContribution.influence')}:
                  <span className={`ml-1 font-bold ${getInfluenceColor(agent.influence)}`}>
                    {t(`agentContribution.${agent.influence}`)}
                  </span>
                </span>
                <span className="text-[#6b7280]">
                  {t('agentContribution.messages')}:
                  <span className="ml-1 text-[#c0c0c0]">{agent.messageCount}</span>
                </span>
              </div>

              <p className="text-xs text-[#6b7280] italic leading-relaxed line-clamp-2">
                "{agent.keyQuote}"
              </p>
            </motion.div>
          ))}
        </div>
      )}

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="pt-3 border-t border-[#21262d]"
      >
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <div className="text-[#39ff14] font-bold">{summary.advocates}</div>
            <div className="text-[#6b7280]">
              {t('agentContribution.stance.advocate')} ({summary.advocatePercent}%)
            </div>
          </div>
          <div>
            <div className="text-[#ff6b35] font-bold">{summary.challengers}</div>
            <div className="text-[#6b7280]">
              {t('agentContribution.stance.challenger')} ({summary.challengerPercent}%)
            </div>
          </div>
          <div>
            <div className="text-[#00ffff] font-bold">{summary.refiners}</div>
            <div className="text-[#6b7280]">
              {t('agentContribution.stance.refiner')} ({summary.refinerPercent}%)
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// Compact version for cards
export function AgentContributionCompact({ messages }: { messages: DebateMessage[] }) {
  const { t } = useI18n();

  const agentStats = useMemo(() => analyzeContributions(messages), [messages]);

  const summary = useMemo(() => {
    const advocates = agentStats.filter(a => a.stance === 'advocate').length;
    const challengers = agentStats.filter(a => a.stance === 'challenger').length;
    const refiners = agentStats.filter(a => a.stance === 'refiner').length;

    return { advocates, challengers, refiners, total: agentStats.length };
  }, [agentStats]);

  return (
    <div className="flex items-center gap-3 text-xs">
      <span className="text-[#6b7280]">{summary.total} {t('agentContribution.agents')}</span>
      <div className="flex items-center gap-2">
        <span className="text-[#39ff14]" title={t('agentContribution.stance.advocate')}>
          +{summary.advocates}
        </span>
        <span className="text-[#ff6b35]" title={t('agentContribution.stance.challenger')}>
          -{summary.challengers}
        </span>
        <span className="text-[#00ffff]" title={t('agentContribution.stance.refiner')}>
          ~{summary.refiners}
        </span>
      </div>
    </div>
  );
}

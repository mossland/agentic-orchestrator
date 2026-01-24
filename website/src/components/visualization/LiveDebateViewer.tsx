'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { MarkdownContent } from '@/lib/markdown';
import type { ApiDebate, ApiDebateMessage } from '@/lib/api';

// Helper function to extract readable text from JSON content
function extractReadableContent(content: string): string {
  if (!content) return '';

  try {
    // Remove markdown code block if present
    const codeBlockMatch = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    const jsonStr = codeBlockMatch ? codeBlockMatch[1].trim() : content.trim();

    // Try to parse as JSON
    if (jsonStr.startsWith('{')) {
      const parsed = JSON.parse(jsonStr);

      // Build readable output from JSON fields
      const parts: string[] = [];

      if (parsed.idea_title) {
        parts.push(`**${parsed.idea_title}**`);
      }

      if (parsed.core_analysis) {
        parts.push(`\n${parsed.core_analysis}`);
      }

      if (parsed.proposal?.description) {
        parts.push(`\n\n**Proposal:** ${parsed.proposal.description}`);
      }

      if (parsed.proposal?.core_features && Array.isArray(parsed.proposal.core_features)) {
        parts.push(`\n\n**Core Features:**`);
        parsed.proposal.core_features.forEach((feature: string) => {
          parts.push(`\n• ${feature}`);
        });
      }

      if (parts.length > 0) {
        return parts.join('');
      }

      // Fallback: get first meaningful string value
      for (const value of Object.values(parsed)) {
        if (typeof value === 'string' && value.length > 20) {
          return value;
        }
      }
    }

    return content;
  } catch {
    // Not valid JSON, return as is (but clean up code block markers)
    return content.replace(/```json/g, '').replace(/```/g, '').trim();
  }
}

interface LiveDebateViewerProps {
  debate: ApiDebate;
  messages: ApiDebateMessage[];
  isLive?: boolean;
  onRefresh?: () => void;
  refreshInterval?: number;
}

interface AgentStyle {
  color: string;
  bgColor: string;
  borderColor: string;
}

const AGENT_STYLES: Record<string, AgentStyle> = {
  tech_founder: { color: '#39ff14', bgColor: 'rgba(57, 255, 20, 0.1)', borderColor: '#39ff14' },
  vc_skeptic: { color: '#ff5555', bgColor: 'rgba(255, 85, 85, 0.1)', borderColor: '#ff5555' },
  market_analyst: { color: '#00ffff', bgColor: 'rgba(0, 255, 255, 0.1)', borderColor: '#00ffff' },
  product_manager: { color: '#bd93f9', bgColor: 'rgba(189, 147, 249, 0.1)', borderColor: '#bd93f9' },
  community_builder: { color: '#ff6b35', bgColor: 'rgba(255, 107, 53, 0.1)', borderColor: '#ff6b35' },
  tech_lead: { color: '#39ff14', bgColor: 'rgba(57, 255, 20, 0.1)', borderColor: '#39ff14' },
  default: { color: '#c0c0c0', bgColor: 'rgba(192, 192, 192, 0.1)', borderColor: '#6b7280' },
};

export function LiveDebateViewer({
  debate,
  messages,
  isLive = false,
  onRefresh,
  refreshInterval = 10000,
}: LiveDebateViewerProps) {
  const { t, locale } = useI18n();
  const [autoScroll, setAutoScroll] = useState(true);
  const [showTypingIndicator, setShowTypingIndicator] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-refresh for live debates
  useEffect(() => {
    if (isLive && onRefresh) {
      const interval = setInterval(() => {
        onRefresh();
        // Show typing indicator briefly
        setShowTypingIndicator(true);
        setTimeout(() => setShowTypingIndicator(false), 2000);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [isLive, onRefresh, refreshInterval]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Detect manual scroll
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  const getAgentStyle = (agentHandle: string | null): AgentStyle => {
    if (!agentHandle) return AGENT_STYLES.default;
    const key = agentHandle.toLowerCase().replace(/@/g, '');
    return AGENT_STYLES[key] || AGENT_STYLES.default;
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'proposal':
        return '💡';
      case 'critique':
        return '🔍';
      case 'synthesis':
        return '🔗';
      case 'vote':
        return '✋';
      case 'agreement':
        return '✅';
      case 'disagreement':
        return '❌';
      default:
        return '💬';
    }
  };

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280] uppercase tracking-wider">
            {t('liveDebate.title')}
          </span>
          {isLive && (
            <motion.span
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="flex items-center gap-1 text-xs text-[#ff5555]"
            >
              <span className="w-2 h-2 bg-[#ff5555] rounded-full" />
              LIVE
            </motion.span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#6b7280]">
            {messages.length} {t('liveDebate.messages')}
          </span>
          {!autoScroll && (
            <button
              onClick={() => {
                setAutoScroll(true);
                messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xs text-[#00ffff] hover:text-[#39ff14]"
            >
              {t('liveDebate.scrollToBottom')}
            </button>
          )}
        </div>
      </div>

      {/* Debate Info */}
      <div className="flex items-center gap-3 text-xs">
        <span className={`px-2 py-0.5 rounded ${
          debate.status === 'in-progress' ? 'bg-[#ff6b35]/20 text-[#ff6b35]' :
          debate.status === 'completed' ? 'bg-[#39ff14]/20 text-[#39ff14]' :
          'bg-[#6b7280]/20 text-[#6b7280]'
        }`}>
          {debate.status}
        </span>
        <span className="text-[#bd93f9]">{debate.phase}</span>
        <span className="text-[#6b7280]">
          R{debate.round_number}/{debate.max_rounds}
        </span>
        <span className="text-[#00ffff]">
          {debate.participants.length} {t('liveDebate.participants')}
        </span>
      </div>

      {/* Messages Container */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="space-y-3 max-h-[500px] overflow-y-auto pr-2 scroll-smooth"
      >
        <AnimatePresence mode="popLayout">
          {messages.map((msg, idx) => {
            const style = getAgentStyle(msg.agent_handle);
            const rawContent = locale === 'ko' && msg.content_ko ? msg.content_ko : msg.content;
            const content = extractReadableContent(rawContent);

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ delay: idx * 0.02 }}
                className="relative"
              >
                <div
                  className="p-3 rounded-lg border-l-2"
                  style={{
                    backgroundColor: style.bgColor,
                    borderLeftColor: style.borderColor,
                  }}
                >
                  {/* Agent Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs" style={{ color: style.color }}>
                        @{msg.agent_handle || msg.agent_name}
                      </span>
                      <span className="text-[10px] text-[#6b7280]">
                        {getMessageTypeIcon(msg.message_type)} {msg.message_type}
                      </span>
                    </div>
                    <span className="text-[10px] text-[#6b7280]">
                      {formatTime(msg.created_at)}
                    </span>
                  </div>

                  {/* Message Content */}
                  <div className="text-sm text-[#c0c0c0] leading-relaxed">
                    {content.length > 500 ? (
                      <details>
                        <summary className="cursor-pointer text-[#00ffff]">
                          <MarkdownContent content={content.slice(0, 200) + '...'} />
                        </summary>
                        <div className="mt-2">
                          <MarkdownContent content={content} />
                        </div>
                      </details>
                    ) : (
                      <MarkdownContent content={content} />
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {showTypingIndicator && isLive && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-2 p-3"
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                    className="w-2 h-2 bg-[#6b7280] rounded-full"
                  />
                ))}
              </div>
              <span className="text-xs text-[#6b7280]">
                {t('liveDebate.agentsThinking')}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      {/* Participant Legend */}
      <div className="pt-3 border-t border-[#21262d]">
        <div className="text-xs text-[#6b7280] uppercase mb-2">
          {t('liveDebate.participants')}
        </div>
        <div className="flex flex-wrap gap-2">
          {debate.participants.map((participant) => {
            const style = getAgentStyle(participant);
            const msgCount = messages.filter(
              (m) => m.agent_handle === participant || m.agent_name === participant
            ).length;

            return (
              <div
                key={participant}
                className="flex items-center gap-1 px-2 py-0.5 rounded text-xs"
                style={{ backgroundColor: style.bgColor, color: style.color }}
              >
                <span>@{participant}</span>
                <span className="text-[#6b7280]">({msgCount})</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Compact live indicator
export function LiveDebateIndicator({
  isActive,
  messageCount,
}: {
  isActive: boolean;
  messageCount: number;
}) {
  const { t } = useI18n();

  return (
    <div className="flex items-center gap-2">
      {isActive ? (
        <motion.span
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
          className="flex items-center gap-1 text-xs text-[#ff5555]"
        >
          <span className="w-1.5 h-1.5 bg-[#ff5555] rounded-full" />
          LIVE
        </motion.span>
      ) : (
        <span className="text-xs text-[#6b7280]">{t('liveDebate.ended')}</span>
      )}
      <span className="text-xs text-[#6b7280]">{messageCount} msgs</span>
    </div>
  );
}

'use client';

import { motion } from 'framer-motion';
import { formatLocalDateTime } from '@/lib/date';
import { MarkdownContent } from '@/lib/markdown';

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

interface DebateConversationProps {
  messages: DebateMessage[];
  locale: string;
}

// Message type colors
const messageTypeColors: Record<string, string> = {
  propose: 'border-[#00ffff]',
  support: 'border-[#39ff14]',
  challenge: 'border-[#ff6b35]',
  synthesize: 'border-[#bd93f9]',
  question: 'border-[#f1fa8c]',
  answer: 'border-[#00ffff]',
  default: 'border-[#6b7280]',
};

const messageTypeIcons: Record<string, string> = {
  propose: '💡',
  support: '✓',
  challenge: '⚡',
  synthesize: '∑',
  question: '?',
  answer: '→',
  default: '•',
};

export function DebateConversation({ messages, locale }: DebateConversationProps) {
  if (messages.length === 0) {
    return (
      <div className="text-center py-8 text-[#6b7280]">
        No messages in this debate yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message, idx) => {
        const colorClass = messageTypeColors[message.message_type] || messageTypeColors.default;
        const icon = messageTypeIcons[message.message_type] || messageTypeIcons.default;
        const rawContent = locale === 'ko' && message.content_ko ? message.content_ko : message.content;
        const content = extractReadableContent(rawContent);

        return (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className={`debate-message ${colorClass} border-l-3 pl-4 py-2`}
          >
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{icon}</span>
              <span className="font-bold text-[#c0c0c0]">{message.agent_name}</span>
              {message.agent_handle && (
                <span className="text-xs text-[#00ffff]">@{message.agent_handle}</span>
              )}
              <span className="text-[10px] text-[#6b7280] uppercase ml-auto">
                {message.message_type}
              </span>
            </div>

            {/* Content */}
            <div className="text-sm text-[#c0c0c0] leading-relaxed">
              <MarkdownContent content={content} />
            </div>

            {/* Timestamp */}
            {message.created_at && (
              <div className="mt-2 text-[10px] text-[#3b3b3b]">
                {formatLocalDateTime(message.created_at, locale)}
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

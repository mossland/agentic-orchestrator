'use client';

import { motion } from 'framer-motion';
import { formatLocalTime } from '@/lib/date';

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

interface DebateTimelineProps {
  messages: DebateMessage[];
  locale: string;
}

// Message type colors
const messageTypeDotColors: Record<string, string> = {
  propose: 'bg-[#00ffff]',
  support: 'bg-[#39ff14]',
  challenge: 'bg-[#ff6b35]',
  synthesize: 'bg-[#bd93f9]',
  question: 'bg-[#f1fa8c]',
  answer: 'bg-[#00ffff]',
  default: 'bg-[#6b7280]',
};

export function DebateTimeline({ messages, locale }: DebateTimelineProps) {
  if (messages.length === 0) {
    return (
      <div className="text-center py-8 text-[#6b7280]">
        No messages in this debate yet.
      </div>
    );
  }

  return (
    <div className="timeline relative pl-8">
      {/* Vertical line */}
      <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-[#21262d]" />

      {messages.map((message, idx) => {
        const dotColor = messageTypeDotColors[message.message_type] || messageTypeDotColors.default;
        const content = locale === 'ko' && message.content_ko ? message.content_ko : message.content;

        return (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="timeline-item relative mb-6 last:mb-0"
          >
            {/* Dot */}
            <div
              className={`absolute -left-5 top-1 w-3 h-3 rounded-full ${dotColor} ring-2 ring-[#0d1117]`}
            />

            {/* Content */}
            <div className="bg-black/20 rounded p-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-bold text-sm text-[#c0c0c0]">
                  {message.agent_name}
                </span>
                <span className="tag text-[10px]" style={{
                  background: dotColor.replace('bg-[', 'rgba(').replace(']', ', 0.1)'),
                  color: dotColor.replace('bg-[', '').replace(']', ''),
                  border: `1px solid ${dotColor.replace('bg-[', '').replace(']', '')}`,
                }}>
                  {message.message_type}
                </span>
              </div>

              <div className="text-xs text-[#c0c0c0] leading-relaxed line-clamp-3">
                {content}
              </div>

              {message.created_at && (
                <div className="mt-1 text-[9px] text-[#3b3b3b]">
                  {formatLocalTime(message.created_at)}
                </div>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

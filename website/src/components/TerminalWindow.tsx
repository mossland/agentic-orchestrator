'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface TerminalWindowProps {
  title: string;
  children: ReactNode;
  showDots?: boolean;
  className?: string;
}

export function TerminalWindow({
  title,
  children,
  showDots = true,
  className = '',
}: TerminalWindowProps) {
  return (
    <div className={`terminal-window ${className}`}>
      <div className="terminal-header">
        {showDots && (
          <div className="flex gap-1.5">
            <div className="terminal-dot red" />
            <div className="terminal-dot yellow" />
            <div className="terminal-dot green" />
          </div>
        )}
        <div className="flex-1 text-center">
          <span className="text-[10px] text-[#6b7280] tracking-wider">
            {title}
          </span>
        </div>
        {showDots && <div className="w-[52px]" />} {/* Spacer for centering */}
      </div>
      <div className="terminal-body">
        {children}
      </div>
    </div>
  );
}

interface TerminalLineProps {
  prompt?: string;
  command?: string;
  output?: string | ReactNode;
  isTyping?: boolean;
  delay?: number;
}

export function TerminalLine({
  prompt = '$',
  command,
  output,
  isTyping = false,
  delay = 0,
}: TerminalLineProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="mb-1"
    >
      {command && (
        <div className="flex items-center gap-2">
          <span className="text-[#00ffff]">{prompt}</span>
          <span className="text-[#c0c0c0]">{command}</span>
          {isTyping && <span className="cursor-blink text-[#39ff14]">▋</span>}
        </div>
      )}
      {output && (
        <div className="text-[#6b7280] ml-4">
          {output}
        </div>
      )}
    </motion.div>
  );
}

interface TerminalTableProps {
  headers: string[];
  rows: (string | ReactNode)[][];
  className?: string;
}

export function TerminalTable({ headers, rows, className = '' }: TerminalTableProps) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="table-cli w-full">
        <thead>
          <tr>
            {headers.map((header, idx) => (
              <th key={idx}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <motion.tr
              key={rowIdx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: rowIdx * 0.05 }}
            >
              {row.map((cell, cellIdx) => (
                <td key={cellIdx}>{cell}</td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface TerminalProgressProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'green' | 'cyan' | 'orange' | 'purple';
}

export function TerminalProgress({
  value,
  max = 100,
  label,
  showPercentage = true,
  color = 'green',
}: TerminalProgressProps) {
  const percentage = Math.round((value / max) * 100);
  const colorClasses = {
    green: 'bg-[#39ff14]',
    cyan: 'bg-[#00ffff]',
    orange: 'bg-[#ff6b35]',
    purple: 'bg-[#bd93f9]',
  };

  return (
    <div className="space-y-1">
      {label && (
        <div className="flex justify-between text-xs">
          <span className="text-[#6b7280]">{label}</span>
          {showPercentage && (
            <span className="text-[#c0c0c0]">{percentage}%</span>
          )}
        </div>
      )}
      <div className="progress-cli">
        <motion.div
          className={`progress-cli-bar ${colorClasses[color]}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

interface TerminalBadgeProps {
  children: ReactNode;
  variant?: 'green' | 'cyan' | 'orange' | 'purple' | 'red';
  pulse?: boolean;
}

export function TerminalBadge({
  children,
  variant = 'green',
  pulse = false,
}: TerminalBadgeProps) {
  const variantClasses = {
    green: 'tag-green',
    cyan: 'tag-cyan',
    orange: 'tag-orange',
    purple: 'tag-purple',
    red: 'bg-[#ff5555]/10 text-[#ff5555] border border-[#ff5555]',
  };

  return (
    <span className={`tag ${variantClasses[variant]} ${pulse ? 'cursor-blink' : ''}`}>
      {children}
    </span>
  );
}

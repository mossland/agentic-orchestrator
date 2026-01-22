'use client';

import { motion } from 'framer-motion';
import { formatDistanceToNow, parseISO, format } from 'date-fns';
import { ko, enUS } from 'date-fns/locale';
import { useI18n } from '@/lib/i18n';

interface SystemStatusProps {
  lastRun: string;
  nextRun: string;
}

export function SystemStatus({ lastRun, nextRun }: SystemStatusProps) {
  const { t, locale } = useI18n();
  const dateLocale = locale === 'ko' ? ko : enUS;
  const lastRunDate = parseISO(lastRun);
  const nextRunDate = parseISO(nextRun);

  return (
    <div className="card-cli p-4">
      <div className="flex flex-wrap items-center gap-4 md:gap-8">
        {/* System Status */}
        <div className="flex items-center gap-3">
          <motion.div
            className="status-dot online"
            animate={{
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <div>
            <span className="text-[#39ff14] text-xs font-bold tracking-wider">
              SYSTEM ONLINE
            </span>
          </div>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Last Run */}
        <div className="flex items-center gap-2">
          <span className="text-[#6b7280] text-xs">last_run:</span>
          <span className="text-[#c0c0c0] text-xs">
            {formatDistanceToNow(lastRunDate, { addSuffix: true, locale: dateLocale })}
          </span>
          <span className="text-[#6b7280] text-[10px]">
            ({format(lastRunDate, 'HH:mm:ss')})
          </span>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Next Run */}
        <div className="flex items-center gap-2">
          <span className="text-[#6b7280] text-xs">next_run:</span>
          <span className="text-[#00ffff] text-xs">
            {formatDistanceToNow(nextRunDate, { addSuffix: true, locale: dateLocale })}
          </span>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Uptime */}
        <div className="flex items-center gap-2">
          <span className="text-[#6b7280] text-xs">uptime:</span>
          <span className="text-[#f1fa8c] text-xs">99.9%</span>
        </div>
      </div>

      {/* Command line style */}
      <div className="mt-3 pt-3 border-t border-[#21262d]">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#00ffff]">$</span>
          <span className="text-[#c0c0c0]">moss-ao status --watch</span>
          <motion.span
            className="text-[#39ff14] cursor-blink"
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
          >
            ▋
          </motion.span>
        </div>
      </div>
    </div>
  );
}

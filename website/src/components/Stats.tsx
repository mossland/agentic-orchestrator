'use client';

import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect } from 'react';
import { useI18n } from '@/lib/i18n';

interface StatCardProps {
  label: string;
  value: number;
  subValue?: { label: string; value: number };
  color?: 'green' | 'cyan' | 'orange' | 'purple';
  delay?: number;
}

function AnimatedNumber({ value, delay = 0 }: { value: number; delay?: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));

  useEffect(() => {
    const timeout = setTimeout(() => {
      const controls = animate(count, value, {
        duration: 1.5,
        ease: 'easeOut',
      });
      return controls.stop;
    }, delay * 1000);

    return () => clearTimeout(timeout);
  }, [count, value, delay]);

  return <motion.span>{rounded}</motion.span>;
}

function StatCard({ label, value, subValue, color = 'green', delay = 0 }: StatCardProps) {
  const colorClasses = {
    green: 'text-[#39ff14] border-[#39ff14]/30',
    cyan: 'text-[#00ffff] border-[#00ffff]/30',
    orange: 'text-[#ff6b35] border-[#ff6b35]/30',
    purple: 'text-[#bd93f9] border-[#bd93f9]/30',
  };

  const glowClasses = {
    green: 'hover:shadow-[0_0_15px_rgba(57,255,20,0.2)]',
    cyan: 'hover:shadow-[0_0_15px_rgba(0,255,255,0.2)]',
    orange: 'hover:shadow-[0_0_15px_rgba(255,107,53,0.2)]',
    purple: 'hover:shadow-[0_0_15px_rgba(189,147,249,0.2)]',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1 }}
      whileHover={{ y: -2 }}
      className={`
        card-cli p-4 border
        ${colorClasses[color]}
        ${glowClasses[color]}
        transition-all duration-200
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-[#6b7280] uppercase tracking-wider">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${colorClasses[color].split(' ')[0]}`}>
          <AnimatedNumber value={value} delay={delay * 0.1} />
        </span>
        {subValue && (
          <span className="text-xs text-[#6b7280]">
            (<span className="text-[#ff5555]">{subValue.value}</span> {subValue.label})
          </span>
        )}
      </div>
      {/* Mini progress bar */}
      <div className="mt-3 h-1 bg-[#21262d] overflow-hidden">
        <motion.div
          className={`h-full ${colorClasses[color].split(' ')[0].replace('text', 'bg')}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ delay: delay * 0.1 + 0.5, duration: 0.8 }}
        />
      </div>
    </motion.div>
  );
}

interface StatsGridProps {
  stats: {
    totalIdeas: number;
    totalPlans: number;
    plansRejected?: number;
    inDevelopment: number;
    trendsAnalyzed: number;
  };
}

export function StatsGrid({ stats }: StatsGridProps) {
  const { t } = useI18n();

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-[#00ffff] text-xs">$</span>
        <span className="text-[#c0c0c0] text-xs">moss-ao stats --summary</span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard
          label={t('stats.totalIdeas')}
          value={stats.totalIdeas}
          color="cyan"
          delay={0}
        />
        <StatCard
          label={t('stats.plansGenerated')}
          value={stats.totalPlans}
          subValue={stats.plansRejected ? { label: 'rejected', value: stats.plansRejected } : undefined}
          color="green"
          delay={1}
        />
        <StatCard
          label={t('stats.inDevelopment')}
          value={stats.inDevelopment}
          color="orange"
          delay={2}
        />
        <StatCard
          label={t('stats.trendsAnalyzed')}
          value={stats.trendsAnalyzed}
          color="purple"
          delay={3}
        />
      </div>
    </div>
  );
}

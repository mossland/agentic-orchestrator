'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { TrendCard } from '@/components/TrendCard';
import { rssCategories, mockTrends } from '@/data/mock';
import { fetchTrends } from '@/lib/api';
import type { Trend } from '@/lib/types';

const categories = ['all', 'crypto', 'defi', 'ai', 'security', 'dev', 'finance'] as const;

export default function TrendsPage() {
  const { t } = useI18n();
  const [trends, setTrends] = useState<Trend[]>(mockTrends);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadTrends() {
      try {
        const data = await fetchTrends();
        setTrends(data);
      } catch (error) {
        console.error('Failed to load trends:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadTrends();
  }, []);

  const filteredTrends = selectedCategory === 'all'
    ? trends
    : trends.filter((t) => t.category === selectedCategory);

  return (
    <div className="min-h-screen bg-zinc-950 pt-14">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-mono text-3xl font-bold text-white">{t('trends.title')}</h1>
          <p className="mt-2 text-zinc-400">{t('trends.subtitle')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
        >
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            {rssCategories.map((cat, index) => (
              <motion.div
                key={cat.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-3 text-center"
              >
                <div className="font-mono text-xl font-bold text-white">{cat.count}</div>
                <div className="text-xs text-zinc-500">{cat.name}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                  cat === selectedCategory
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                }`}
              >
                {cat.toUpperCase()}
              </button>
            ))}
          </div>
        </motion.div>

        <div className="grid gap-4">
          {isLoading ? (
            <div className="text-center text-zinc-500 py-8">Loading trends...</div>
          ) : filteredTrends.length === 0 ? (
            <div className="text-center text-zinc-500 py-8">No trends found</div>
          ) : (
            filteredTrends.map((trend, index) => (
              <TrendCard key={trend.title} trend={trend} index={index} />
            ))
          )}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 rounded-lg border border-zinc-800 bg-zinc-900/50 p-6 text-center"
        >
          <div className="font-mono text-sm text-zinc-500">{t('trends.schedule')}</div>
          <div className="mt-2 text-white">{t('trends.scheduleTime')}</div>
          <div className="mt-1 text-sm text-zinc-500">{t('trends.scheduleDesc')}</div>
        </motion.div>
      </div>
    </div>
  );
}

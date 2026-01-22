'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { IdeaCard } from '@/components/IdeaCard';
import { mockIdeas, mockPlans } from '@/data/mock';
import { fetchIdeas, fetchPlans } from '@/lib/api';
import type { Idea, Plan } from '@/lib/types';

export default function BacklogPage() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<'ideas' | 'plans' | 'in-dev'>('ideas');
  const [ideas, setIdeas] = useState<Idea[]>(mockIdeas);
  const [plans, setPlans] = useState<Plan[]>(mockPlans);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ideasData, plansData] = await Promise.all([
          fetchIdeas(),
          fetchPlans(),
        ]);
        setIdeas(ideasData);
        setPlans(plansData);
      } catch (error) {
        console.error('Failed to load backlog data:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const tabs = [
    { id: 'ideas' as const, label: t('backlog.ideas'), count: ideas.length },
    { id: 'plans' as const, label: t('backlog.plans'), count: plans.length },
    { id: 'in-dev' as const, label: t('backlog.inDevelopment'), count: ideas.filter(i => i.status === 'in-dev').length },
  ];

  const filteredIdeas = activeTab === 'in-dev'
    ? ideas.filter(i => i.status === 'in-dev')
    : activeTab === 'plans'
    ? ideas.filter(i => i.status === 'planned')
    : ideas;

  return (
    <div className="min-h-screen bg-zinc-950 pt-14">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-mono text-3xl font-bold text-white">{t('backlog.title')}</h1>
          <p className="mt-2 text-zinc-400">{t('backlog.subtitle')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 flex gap-2 border-b border-zinc-800 pb-4"
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition-colors ${
                activeTab === tab.id
                  ? 'bg-zinc-800 text-white'
                  : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'
              }`}
            >
              {tab.label}
              <span className={`rounded px-1.5 py-0.5 font-mono text-xs ${
                activeTab === tab.id ? 'bg-zinc-700' : 'bg-zinc-800'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </motion.div>

        <div className="grid gap-4">
          {isLoading ? (
            <div className="text-center text-zinc-500 py-8">Loading...</div>
          ) : filteredIdeas.length === 0 ? (
            <div className="text-center text-zinc-500 py-8">No items found</div>
          ) : (
            filteredIdeas.map((idea, index) => (
              <IdeaCard key={idea.id} idea={idea} index={index} />
            ))
          )}
        </div>

        {activeTab === 'plans' && plans.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <h2 className="mb-4 font-mono text-sm text-zinc-500">{t('backlog.debateHistory')}</h2>
            <div className="space-y-2">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 p-3"
                >
                  <div>
                    <span className="font-mono text-xs text-zinc-600">#{plan.id}</span>
                    <span className="ml-2 text-white">{plan.title}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-zinc-500">
                      {plan.debateRounds} {t('backlog.rounds')}
                    </span>
                    <span className={`rounded px-2 py-0.5 text-xs ${
                      plan.status === 'approved'
                        ? 'bg-green-500/20 text-green-400'
                        : plan.status === 'review'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : plan.status === 'rejected'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-zinc-500/20 text-zinc-400'
                    }`}>
                      {plan.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 text-center"
        >
          <a
            href="https://github.com/mossland/agentic-orchestrator/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
          >
            {t('backlog.viewAllIssues')}
            <span className="text-zinc-500">→</span>
          </a>
        </motion.div>
      </div>
    </div>
  );
}

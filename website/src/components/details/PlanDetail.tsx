'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiPlan } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { TerminalBadge } from '../TerminalWindow';

interface PlanDetailProps {
  data: ModalData;
}

interface PlanWithContent extends ApiPlan {
  prd_content: string | null;
  architecture_content: string | null;
  user_research_content: string | null;
  business_model_content: string | null;
  project_plan_content: string | null;
  final_plan: string | null;
  updated_at: string | null;
}

type TabKey = 'prd' | 'architecture' | 'userResearch' | 'businessModel' | 'projectPlan' | 'final';

const TABS: { key: TabKey; label: string; contentKey: keyof PlanWithContent }[] = [
  { key: 'prd', label: 'PRD', contentKey: 'prd_content' },
  { key: 'architecture', label: 'Architecture', contentKey: 'architecture_content' },
  { key: 'userResearch', label: 'User Research', contentKey: 'user_research_content' },
  { key: 'businessModel', label: 'Business Model', contentKey: 'business_model_content' },
  { key: 'projectPlan', label: 'Project Plan', contentKey: 'project_plan_content' },
  { key: 'final', label: 'Final Plan', contentKey: 'final_plan' },
];

export function PlanDetail({ data }: PlanDetailProps) {
  const { t } = useI18n();
  const [plan, setPlan] = useState<PlanWithContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('prd');

  useEffect(() => {
    async function fetchPlan() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getPlanDetail(data.id);
        if (response.data) {
          setPlan(response.data);
          // Set first tab with content as active
          const firstTabWithContent = TABS.find(tab => response.data?.[tab.contentKey]);
          if (firstTabWithContent) {
            setActiveTab(firstTabWithContent.key);
          }
        } else {
          setError(response.error || t('detail.fetchError'));
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchPlan();
  }, [data.id, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#00ffff] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    approved: 'green',
    draft: 'cyan',
    rejected: 'orange',
    'in-review': 'purple',
  };

  const activeContent = plan[TABS.find(tab => tab.key === activeTab)?.contentKey || 'prd_content'] as string | null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TerminalBadge variant={statusColors[plan.status] || 'cyan'}>
            {plan.status}
          </TerminalBadge>
          <TerminalBadge variant="purple">v{plan.version}</TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{plan.title}</h3>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 border-b border-[#21262d]">
        {TABS.map((tab) => {
          const hasContent = !!plan[tab.contentKey];
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              disabled={!hasContent}
              className={`
                tab-button px-3 py-2 text-xs uppercase tracking-wider
                border-b-2 transition-all
                ${activeTab === tab.key
                  ? 'text-[#39ff14] border-[#39ff14]'
                  : hasContent
                    ? 'text-[#6b7280] border-transparent hover:text-[#c0c0c0]'
                    : 'text-[#3b3b3b] border-transparent cursor-not-allowed'
                }
              `}
            >
              {tab.label}
              {!hasContent && <span className="ml-1 opacity-50">∅</span>}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="card-cli p-4 max-h-[500px] overflow-y-auto">
        {activeContent ? (
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="prose prose-invert prose-sm max-w-none"
          >
            <pre className="whitespace-pre-wrap text-sm text-[#c0c0c0] font-mono leading-relaxed">
              {activeContent}
            </pre>
          </motion.div>
        ) : (
          <div className="text-center py-12 text-[#6b7280]">
            {t('detail.noContent')}
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.metadata')}</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[#6b7280]">{t('detail.createdAt')}: </span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(plan.created_at)}
            </span>
          </div>
          <div>
            <span className="text-[#6b7280]">{t('detail.updatedAt')}: </span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(plan.updated_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Links */}
      {plan.github_issue_url && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.links')}</div>
          <a
            href={plan.github_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[#00ffff] hover:underline text-sm"
          >
            <span>→</span>
            {t('detail.viewOnGitHub')}
          </a>
        </div>
      )}
    </motion.div>
  );
}

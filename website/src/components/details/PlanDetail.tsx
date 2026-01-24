'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiPlan, type ApiProject } from '@/lib/api';
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
  updated_at: string | null;
}

interface ProjectState {
  project: ApiProject | null;
  jobId: string | null;
  generating: boolean;
  error: string | null;
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
  const { t, locale } = useI18n();
  const [plan, setPlan] = useState<PlanWithContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('prd');
  const [projectState, setProjectState] = useState<ProjectState>({
    project: null,
    jobId: null,
    generating: false,
    error: null,
  });

  // Helper function for localized text display
  const getLocalizedText = (en: string | null | undefined, ko: string | null | undefined): string => {
    if (locale === 'ko' && ko) return ko;
    return en || '';
  };

  // Fetch project status
  const fetchProjectStatus = useCallback(async (planId: string) => {
    try {
      const response = await ApiClient.getPlanProject(planId);
      if (response.data?.project) {
        setProjectState(prev => ({
          ...prev,
          project: response.data!.project,
          generating: response.data!.project?.status === 'generating',
        }));
      }
    } catch (err) {
      console.warn('Failed to fetch project status:', err);
    }
  }, []);

  // Poll job status
  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const response = await ApiClient.getJobStatus(jobId);
      if (response.data) {
        const status = response.data.status;
        if (status === 'completed' || status === 'failed') {
          // Refresh project data
          if (plan?.id) {
            await fetchProjectStatus(plan.id);
          }
          setProjectState(prev => ({
            ...prev,
            jobId: null,
            generating: false,
            error: status === 'failed' ? response.data!.error || 'Generation failed' : null,
          }));
        } else if (status === 'in_progress' || status === 'pending') {
          // Continue polling
          setTimeout(() => pollJobStatus(jobId), 3000);
        }
      }
    } catch (err) {
      console.warn('Failed to poll job status:', err);
    }
  }, [fetchProjectStatus, plan?.id]);

  // Handle generate project button click
  const handleGenerateProject = async () => {
    if (!plan?.id) return;

    setProjectState(prev => ({
      ...prev,
      generating: true,
      error: null,
    }));

    try {
      const response = await ApiClient.generateProject(plan.id, false);
      if (response.data) {
        if (response.data.status === 'accepted') {
          setProjectState(prev => ({
            ...prev,
            jobId: response.data!.job_id,
          }));
          // Start polling
          pollJobStatus(response.data.job_id);
        } else if (response.data.status === 'exists') {
          // Refresh project data
          await fetchProjectStatus(plan.id);
          setProjectState(prev => ({ ...prev, generating: false }));
        } else if (response.data.status === 'in_progress') {
          setProjectState(prev => ({ ...prev, generating: true }));
        }
      } else {
        setProjectState(prev => ({
          ...prev,
          generating: false,
          error: response.error || 'Failed to start project generation',
        }));
      }
    } catch (err) {
      setProjectState(prev => ({
        ...prev,
        generating: false,
        error: 'Failed to generate project',
      }));
    }
  };

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
          // Also fetch project status
          await fetchProjectStatus(data.id);
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
  }, [data.id, t, fetchProjectStatus]);

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

  // Get active content with Korean fallback for final_plan
  const getActiveContent = (): string | null => {
    const tab = TABS.find(tab => tab.key === activeTab);
    if (!tab) return null;

    const content = plan[tab.contentKey] as string | null;

    // For final_plan, use Korean version if available and locale is 'ko'
    if (tab.key === 'final' && locale === 'ko' && plan.final_plan_ko) {
      return plan.final_plan_ko;
    }

    return content;
  };

  const activeContent = getActiveContent();

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
        <h3 className="text-lg font-bold text-[#c0c0c0]">{getLocalizedText(plan.title, plan.title_ko)}</h3>
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
              {formatLocalDateTime(plan.created_at, locale)}
            </span>
          </div>
          <div>
            <span className="text-[#6b7280]">{t('detail.updatedAt')}: </span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(plan.updated_at, locale)}
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

      {/* Project Generation Section */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-3">
          {locale === 'ko' ? '프로젝트 생성' : 'Project Generation'}
        </div>

        {/* Error message */}
        {projectState.error && (
          <div className="text-[#ff5555] text-sm mb-3 p-2 border border-[#ff5555]/30 rounded">
            [ERROR] {projectState.error}
          </div>
        )}

        {/* Project exists and ready */}
        {projectState.project?.status === 'ready' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <TerminalBadge variant="green">READY</TerminalBadge>
              <span className="text-[#c0c0c0] text-sm">
                {projectState.project.name}
              </span>
            </div>
            <div className="text-xs text-[#6b7280]">
              <span>{locale === 'ko' ? '경로: ' : 'Path: '}</span>
              <code className="text-[#00ffff]">{projectState.project.directory_path}</code>
            </div>
            {projectState.project.tech_stack && (
              <div className="flex flex-wrap gap-2">
                {projectState.project.tech_stack.frontend && (
                  <TerminalBadge variant="cyan">{projectState.project.tech_stack.frontend}</TerminalBadge>
                )}
                {projectState.project.tech_stack.backend && (
                  <TerminalBadge variant="purple">{projectState.project.tech_stack.backend}</TerminalBadge>
                )}
                {projectState.project.tech_stack.database && (
                  <TerminalBadge variant="orange">{projectState.project.tech_stack.database}</TerminalBadge>
                )}
              </div>
            )}
            <div className="text-xs text-[#6b7280]">
              {locale === 'ko' ? '생성된 파일: ' : 'Files generated: '}
              <span className="text-[#39ff14]">{projectState.project.files_generated}</span>
            </div>
            <button
              onClick={() => handleGenerateProject()}
              className="w-full mt-2 px-4 py-2 text-sm border border-[#6b7280] text-[#6b7280] hover:border-[#00ffff] hover:text-[#00ffff] rounded transition-colors"
            >
              $ regenerate --force
            </button>
          </div>
        )}

        {/* Project generating */}
        {(projectState.generating || projectState.project?.status === 'generating') && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin">
                <svg className="w-5 h-5 text-[#00ffff]" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
              <span className="text-[#00ffff] animate-pulse">
                $ generating_project
                <span className="cursor-blink">▋</span>
              </span>
            </div>

            {/* Progress Steps */}
            <div className="border border-[#21262d] rounded p-3 space-y-2">
              <div className="text-xs text-[#6b7280] uppercase mb-2">
                {locale === 'ko' ? '생성 단계' : 'Generation Steps'}
              </div>
              {[
                { step: 1, en: 'Loading plan data', ko: 'Plan 데이터 로드', icon: '📄' },
                { step: 2, en: 'Parsing markdown', ko: '마크다운 파싱', icon: '🔍' },
                { step: 3, en: 'Detecting tech stack', ko: '기술 스택 감지', icon: '⚙️' },
                { step: 4, en: 'Generating templates', ko: '템플릿 생성', icon: '📝' },
                { step: 5, en: 'LLM code generation', ko: 'LLM 코드 생성', icon: '🤖' },
                { step: 6, en: 'Writing files', ko: '파일 저장', icon: '💾' },
              ].map((item, idx) => (
                <div key={item.step} className="flex items-center gap-2 text-xs">
                  <span className="w-4 text-center">{item.icon}</span>
                  <span className={idx < 2 ? 'text-[#39ff14]' : 'text-[#6b7280]'}>
                    {idx < 2 ? '✓' : idx === 2 ? '●' : '○'}
                  </span>
                  <span className={idx <= 2 ? 'text-[#c0c0c0]' : 'text-[#6b7280]'}>
                    {locale === 'ko' ? item.ko : item.en}
                  </span>
                </div>
              ))}
            </div>

            {/* LLM Models Info */}
            <div className="text-xs text-[#6b7280]">
              <span>{locale === 'ko' ? '사용 모델: ' : 'Models: '}</span>
              <span className="text-[#00ffff]">glm-4.7-flash</span>
              <span className="mx-1">→</span>
              <span className="text-[#bd93f9]">qwen2.5:32b</span>
            </div>
          </div>
        )}

        {/* Project error */}
        {projectState.project?.status === 'error' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <TerminalBadge variant="orange">ERROR</TerminalBadge>
              <span className="text-[#c0c0c0] text-sm">
                {locale === 'ko' ? '프로젝트 생성 실패' : 'Project generation failed'}
              </span>
            </div>
            <button
              onClick={() => handleGenerateProject()}
              disabled={projectState.generating}
              className="w-full px-4 py-2 text-sm border border-[#ff6b35] text-[#ff6b35] hover:bg-[#ff6b35]/10 rounded transition-colors disabled:opacity-50"
            >
              $ retry_generate
            </button>
          </div>
        )}

        {/* No project yet - show generate button for approved plans */}
        {!projectState.project && !projectState.generating && plan.status === 'approved' && (
          <button
            onClick={handleGenerateProject}
            disabled={projectState.generating}
            className="w-full px-4 py-3 text-sm border border-[#39ff14] text-[#39ff14] hover:bg-[#39ff14]/10 rounded transition-colors font-mono disabled:opacity-50"
          >
            $ generate_project --from-plan {data.id}
          </button>
        )}

        {/* Plan not approved */}
        {!projectState.project && !projectState.generating && plan.status !== 'approved' && (
          <div className="text-[#6b7280] text-sm">
            {locale === 'ko'
              ? '프로젝트 생성은 승인된 플랜에서만 가능합니다.'
              : 'Project generation is only available for approved plans.'}
          </div>
        )}
      </div>
    </motion.div>
  );
}

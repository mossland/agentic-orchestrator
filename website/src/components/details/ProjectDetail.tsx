'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiProject, type ApiPlan, type ApiIdea, type ApiDebate } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { TerminalBadge } from '../TerminalWindow';
import { useModal } from '../modals/useModal';

interface ProjectDetailProps {
  data: ModalData;
}

interface ProjectFullData {
  project: ApiProject;
  plan: ApiPlan | null;
  idea: ApiIdea | null;
  debate: ApiDebate | null;
}

export function ProjectDetail({ data }: ProjectDetailProps) {
  const { locale } = useI18n();
  const { openModal } = useModal();
  const [projectData, setProjectData] = useState<ProjectFullData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProject() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getProjectDetail(data.id);
        if (response.data) {
          // Fetch related idea and debate if plan exists
          let idea: ApiIdea | null = null;
          let debate: ApiDebate | null = null;

          if (response.data.plan?.idea_id) {
            const ideaRes = await ApiClient.getIdeaDetail(response.data.plan.idea_id);
            if (ideaRes.data) {
              idea = ideaRes.data.idea;
              if (idea?.debate_session_id) {
                const debateRes = await ApiClient.getDebateDetail(idea.debate_session_id);
                if (debateRes.data) {
                  debate = debateRes.data.debate;
                }
              }
            }
          }

          setProjectData({
            project: response.data.project,
            plan: response.data.plan,
            idea,
            debate,
          });
        } else {
          setError(response.error || 'Failed to fetch project');
        }
      } catch {
        setError('Failed to fetch project');
      } finally {
        setLoading(false);
      }
    }

    fetchProject();
  }, [data.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#00ffff] animate-pulse">
          $ {locale === 'ko' ? '로딩 중...' : 'Loading...'}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !projectData) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || 'Project not found'}</div>
      </div>
    );
  }

  const { project, plan, idea, debate } = projectData;

  const getStatusColor = (status: string): 'green' | 'cyan' | 'orange' | 'purple' => {
    switch (status) {
      case 'ready': return 'green';
      case 'generating': return 'cyan';
      case 'error': return 'orange';
      default: return 'purple';
    }
  };

  const getStatusLabel = (status: string): string => {
    if (locale === 'ko') {
      switch (status) {
        case 'ready': return '완료';
        case 'generating': return '생성 중';
        case 'error': return '오류';
        case 'pending': return '대기 중';
        default: return status;
      }
    }
    return status.toUpperCase();
  };

  // Tech stack icons
  const techIcons: Record<string, string> = {
    nextjs: '▲',
    react: '⚛',
    vue: '🟢',
    fastapi: '⚡',
    express: '🟩',
    postgresql: '🐘',
    mongodb: '🍃',
    sqlite: '📦',
    ethereum: '⟠',
    solana: '◎',
    hardhat: '🎩',
  };

  const getTechIcon = (tech: string): string => {
    const lowerTech = tech.toLowerCase();
    for (const [key, icon] of Object.entries(techIcons)) {
      if (lowerTech.includes(key)) return icon;
    }
    return '📦';
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header with Status and GitHub Link */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <TerminalBadge variant={getStatusColor(project.status)}>
              {getStatusLabel(project.status)}
            </TerminalBadge>
            {project.files_generated > 0 && (
              <span className="text-xs text-[#39ff14]">
                {project.files_generated} files
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-[#c0c0c0]">{project.name}</h3>
        </div>

        {/* GitHub Link */}
        {plan?.github_issue_url && (
          <a
            href={plan.github_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 border border-[#21262d] hover:border-[#39ff14] transition-colors text-xs"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12"/>
            </svg>
            <span className="text-[#c0c0c0]">View on GitHub</span>
          </a>
        )}
      </div>

      {/* Project Journey Visualization */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">
          {locale === 'ko' ? '프로젝트 여정' : 'Project Journey'}
        </div>
        <div className="flex items-center justify-between gap-1 overflow-x-auto pb-2">
          {/* Debate */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0 }}
            className={`flex flex-col items-center min-w-[60px] cursor-pointer ${debate ? 'hover:opacity-80' : 'opacity-40'}`}
            onClick={() => debate && openModal('debate', { id: debate.id, title: debate.topic || 'Debate' })}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${debate ? 'bg-[#ff6b35]/20 border border-[#ff6b35]' : 'bg-[#21262d] border border-[#21262d]'}`}>
              💬
            </div>
            <span className="text-[10px] text-[#6b7280] mt-1">Debate</span>
            {debate && (
              <span className="text-[8px] text-[#ff6b35]">
                {debate.participants?.length || 0} agents
              </span>
            )}
          </motion.div>

          {/* Arrow */}
          <div className="flex-shrink-0 w-6 h-0.5 bg-gradient-to-r from-[#ff6b35] to-[#39ff14]" />

          {/* Idea */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className={`flex flex-col items-center min-w-[60px] cursor-pointer ${idea ? 'hover:opacity-80' : 'opacity-40'}`}
            onClick={() => idea && openModal('idea', { id: idea.id, title: idea.title })}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${idea ? 'bg-[#39ff14]/20 border border-[#39ff14]' : 'bg-[#21262d] border border-[#21262d]'}`}>
              💡
            </div>
            <span className="text-[10px] text-[#6b7280] mt-1">Idea</span>
            {idea && (
              <span className="text-[8px] text-[#39ff14]">
                Score: {idea.score?.toFixed(1) || '-'}
              </span>
            )}
          </motion.div>

          {/* Arrow */}
          <div className="flex-shrink-0 w-6 h-0.5 bg-gradient-to-r from-[#39ff14] to-[#00ffff]" />

          {/* Plan */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className={`flex flex-col items-center min-w-[60px] cursor-pointer ${plan ? 'hover:opacity-80' : 'opacity-40'}`}
            onClick={() => plan && openModal('plan', { id: plan.id, title: plan.title })}
          >
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${plan ? 'bg-[#00ffff]/20 border border-[#00ffff]' : 'bg-[#21262d] border border-[#21262d]'}`}>
              📋
            </div>
            <span className="text-[10px] text-[#6b7280] mt-1">Plan</span>
            {plan && (
              <span className="text-[8px] text-[#00ffff]">
                v{plan.version}
              </span>
            )}
          </motion.div>

          {/* Arrow */}
          <div className="flex-shrink-0 w-6 h-0.5 bg-gradient-to-r from-[#00ffff] to-[#bd93f9]" />

          {/* Project */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col items-center min-w-[60px]"
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg bg-[#bd93f9]/20 border-2 border-[#bd93f9] shadow-[0_0_10px_rgba(189,147,249,0.3)]">
              📁
            </div>
            <span className="text-[10px] text-[#bd93f9] mt-1 font-bold">Project</span>
            <span className="text-[8px] text-[#bd93f9]">
              {getStatusLabel(project.status)}
            </span>
          </motion.div>
        </div>
      </div>

      {/* Project Description from Plan */}
      {plan && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-3">
            {locale === 'ko' ? '프로젝트 설명' : 'Project Description'}
          </div>
          <h4 className="text-[#c0c0c0] font-medium mb-2">
            {locale === 'ko' && plan.title_ko ? plan.title_ko : plan.title}
          </h4>
          {idea?.summary && (
            <p className="text-sm text-[#6b7280] leading-relaxed">
              {locale === 'ko' && idea.summary_ko ? idea.summary_ko : idea.summary}
            </p>
          )}
        </div>
      )}

      {/* Tech Stack with Icons */}
      {project.tech_stack && Object.keys(project.tech_stack).length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-3">
            {locale === 'ko' ? '기술 스택' : 'Tech Stack'}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {project.tech_stack.frontend && (
              <div className="flex items-center gap-3 p-3 bg-[#00ffff]/5 border border-[#00ffff]/30 rounded">
                <span className="text-2xl">{getTechIcon(project.tech_stack.frontend)}</span>
                <div>
                  <div className="text-xs text-[#6b7280]">Frontend</div>
                  <div className="text-sm text-[#00ffff] font-medium">{project.tech_stack.frontend}</div>
                </div>
              </div>
            )}
            {project.tech_stack.backend && (
              <div className="flex items-center gap-3 p-3 bg-[#bd93f9]/5 border border-[#bd93f9]/30 rounded">
                <span className="text-2xl">{getTechIcon(project.tech_stack.backend)}</span>
                <div>
                  <div className="text-xs text-[#6b7280]">Backend</div>
                  <div className="text-sm text-[#bd93f9] font-medium">{project.tech_stack.backend}</div>
                </div>
              </div>
            )}
            {project.tech_stack.database && (
              <div className="flex items-center gap-3 p-3 bg-[#ff6b35]/5 border border-[#ff6b35]/30 rounded">
                <span className="text-2xl">{getTechIcon(project.tech_stack.database)}</span>
                <div>
                  <div className="text-xs text-[#6b7280]">Database</div>
                  <div className="text-sm text-[#ff6b35] font-medium">{project.tech_stack.database}</div>
                </div>
              </div>
            )}
            {project.tech_stack.blockchain && (
              <div className="flex items-center gap-3 p-3 bg-[#39ff14]/5 border border-[#39ff14]/30 rounded">
                <span className="text-2xl">{getTechIcon(project.tech_stack.blockchain)}</span>
                <div>
                  <div className="text-xs text-[#6b7280]">Blockchain</div>
                  <div className="text-sm text-[#39ff14] font-medium">{project.tech_stack.blockchain}</div>
                </div>
              </div>
            )}
          </div>
          {project.tech_stack.additional && project.tech_stack.additional.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[#21262d]">
              <div className="text-xs text-[#6b7280] mb-2">
                {locale === 'ko' ? '추가 도구' : 'Additional Tools'}
              </div>
              <div className="flex flex-wrap gap-2">
                {project.tech_stack.additional.map((tool, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-[#21262d] text-[#c0c0c0] rounded">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Project Structure Visualization */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-3">
          {locale === 'ko' ? '프로젝트 구조' : 'Project Structure'}
        </div>
        <div className="relative">
          {/* Tree Structure */}
          <pre className="text-xs text-[#c0c0c0] font-mono leading-relaxed overflow-x-auto">
{`${project.name}/
├── 📄 README.md              ${locale === 'ko' ? '# 프로젝트 문서' : '# Project docs'}
├── 📋 PLAN.md                ${locale === 'ko' ? '# 기획서' : '# Plan document'}
├── ⚙️ .moss-project.json     ${locale === 'ko' ? '# 메타데이터' : '# Metadata'}
├── 📁 src/
│   ${project.tech_stack?.frontend ? `├── 🖥️ frontend/           # ${project.tech_stack.frontend}` : ''}
│   ${project.tech_stack?.backend ? `└── 🔧 backend/            # ${project.tech_stack.backend}` : ''}
${project.tech_stack?.blockchain ? `├── 📜 contracts/             # ${project.tech_stack.blockchain}` : ''}
├── 📚 docs/
│   └── api.md
└── 🧪 tests/`}
          </pre>
          {/* Files count badge */}
          {project.files_generated > 0 && (
            <div className="absolute top-2 right-2 px-2 py-1 bg-[#39ff14]/20 text-[#39ff14] text-xs rounded">
              {project.files_generated} {locale === 'ko' ? '파일 생성됨' : 'files generated'}
            </div>
          )}
        </div>
      </div>

      {/* Project Path */}
      {project.directory_path && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">
            {locale === 'ko' ? '프로젝트 경로' : 'Project Path'}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#00ffff]">→</span>
            <code className="text-sm text-[#00ffff] font-mono break-all">
              {project.directory_path}
            </code>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">
          {locale === 'ko' ? '타임라인' : 'Timeline'}
        </div>
        <div className="space-y-3">
          {debate?.started_at && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#ff6b35]" />
              <span className="text-xs text-[#6b7280] w-24">Debate</span>
              <span className="text-xs text-[#c0c0c0]">{formatLocalDateTime(debate.started_at, locale)}</span>
            </div>
          )}
          {idea?.created_at && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#39ff14]" />
              <span className="text-xs text-[#6b7280] w-24">Idea</span>
              <span className="text-xs text-[#c0c0c0]">{formatLocalDateTime(idea.created_at, locale)}</span>
            </div>
          )}
          {plan?.created_at && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#00ffff]" />
              <span className="text-xs text-[#6b7280] w-24">Plan</span>
              <span className="text-xs text-[#c0c0c0]">{formatLocalDateTime(plan.created_at, locale)}</span>
            </div>
          )}
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#bd93f9]" />
            <span className="text-xs text-[#6b7280] w-24">Project</span>
            <span className="text-xs text-[#c0c0c0]">{formatLocalDateTime(project.created_at, locale)}</span>
          </div>
          {project.completed_at && (
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-[#39ff14] shadow-[0_0_5px_#39ff14]" />
              <span className="text-xs text-[#6b7280] w-24">Completed</span>
              <span className="text-xs text-[#39ff14]">{formatLocalDateTime(project.completed_at, locale)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 gap-3">
        {plan && (
          <button
            onClick={() => openModal('plan', { id: plan.id, title: plan.title })}
            className="btn-cli py-3 text-xs text-center"
          >
            📋 {locale === 'ko' ? 'Plan 상세보기' : 'View Plan'}
          </button>
        )}
        {plan?.github_issue_url && (
          <a
            href={plan.github_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-cli py-3 text-xs text-center flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12"/>
            </svg>
            GitHub
          </a>
        )}
      </div>

      {/* Generating Status */}
      {project.status === 'generating' && (
        <div className="card-cli p-4 border-[#00ffff]">
          <div className="flex items-center gap-3">
            <div className="animate-spin">
              <svg className="w-6 h-6 text-[#00ffff]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <div>
              <div className="text-[#00ffff] font-medium">
                {locale === 'ko' ? '프로젝트 생성 중...' : 'Generating project...'}
              </div>
              <div className="text-xs text-[#6b7280] mt-1">
                {locale === 'ko'
                  ? 'LLM이 코드를 생성하고 있습니다. 잠시만 기다려주세요.'
                  : 'LLM is generating code. Please wait.'}
              </div>
            </div>
          </div>

          {/* Progress Steps */}
          <div className="mt-4 space-y-2">
            {[
              { step: 1, label: locale === 'ko' ? 'Plan 파싱' : 'Parsing Plan', done: true },
              { step: 2, label: locale === 'ko' ? '기술 스택 감지' : 'Detecting tech stack', done: true },
              { step: 3, label: locale === 'ko' ? '템플릿 생성' : 'Generating templates', done: false },
              { step: 4, label: locale === 'ko' ? 'LLM 코드 생성' : 'LLM code generation', done: false },
              { step: 5, label: locale === 'ko' ? '파일 저장' : 'Saving files', done: false },
            ].map((item) => (
              <div key={item.step} className="flex items-center gap-2 text-xs">
                <span className={item.done ? 'text-[#39ff14]' : 'text-[#6b7280]'}>
                  {item.done ? '✓' : '○'}
                </span>
                <span className={item.done ? 'text-[#c0c0c0]' : 'text-[#6b7280]'}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Status */}
      {project.status === 'error' && (
        <div className="card-cli p-4 border-[#ff5555]">
          <div className="text-[#ff5555] font-medium mb-2">
            {locale === 'ko' ? '프로젝트 생성 실패' : 'Project generation failed'}
          </div>
          <div className="text-xs text-[#6b7280]">
            {locale === 'ko'
              ? 'Plan 상세 페이지에서 재시도할 수 있습니다.'
              : 'You can retry from the Plan detail page.'}
          </div>
        </div>
      )}
    </motion.div>
  );
}

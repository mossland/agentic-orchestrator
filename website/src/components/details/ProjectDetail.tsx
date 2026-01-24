'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiProject, type ApiPlan } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';
import { TerminalBadge } from '../TerminalWindow';
import { useModal } from '../modals/useModal';

interface ProjectDetailProps {
  data: ModalData;
}

interface ProjectWithPlan {
  project: ApiProject;
  plan: ApiPlan | null;
}

export function ProjectDetail({ data }: ProjectDetailProps) {
  const { locale } = useI18n();
  const { openModal } = useModal();
  const [projectData, setProjectData] = useState<ProjectWithPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProject() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getProjectDetail(data.id);
        if (response.data) {
          setProjectData(response.data);
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

  const { project, plan } = projectData;

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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TerminalBadge variant={getStatusColor(project.status)}>
            {getStatusLabel(project.status)}
          </TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{project.name}</h3>
      </div>

      {/* Tech Stack */}
      {project.tech_stack && Object.keys(project.tech_stack).length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-3">
            {locale === 'ko' ? '기술 스택' : 'Tech Stack'}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {project.tech_stack.frontend && (
              <div>
                <div className="text-xs text-[#6b7280] mb-1">Frontend</div>
                <TerminalBadge variant="cyan">{project.tech_stack.frontend}</TerminalBadge>
              </div>
            )}
            {project.tech_stack.backend && (
              <div>
                <div className="text-xs text-[#6b7280] mb-1">Backend</div>
                <TerminalBadge variant="purple">{project.tech_stack.backend}</TerminalBadge>
              </div>
            )}
            {project.tech_stack.database && (
              <div>
                <div className="text-xs text-[#6b7280] mb-1">Database</div>
                <TerminalBadge variant="orange">{project.tech_stack.database}</TerminalBadge>
              </div>
            )}
            {project.tech_stack.blockchain && (
              <div>
                <div className="text-xs text-[#6b7280] mb-1">Blockchain</div>
                <TerminalBadge variant="green">{project.tech_stack.blockchain}</TerminalBadge>
              </div>
            )}
          </div>
          {project.tech_stack.additional && project.tech_stack.additional.length > 0 && (
            <div className="mt-3">
              <div className="text-xs text-[#6b7280] mb-1">
                {locale === 'ko' ? '추가 도구' : 'Additional'}
              </div>
              <div className="flex flex-wrap gap-1">
                {project.tech_stack.additional.map((tool, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 bg-[#21262d] text-[#c0c0c0] rounded">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Project Path */}
      {project.directory_path && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">
            {locale === 'ko' ? '프로젝트 경로' : 'Project Path'}
          </div>
          <code className="text-sm text-[#00ffff] font-mono break-all">
            {project.directory_path}
          </code>
        </div>
      )}

      {/* Files Generated */}
      {project.files_generated > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">
            {locale === 'ko' ? '생성된 파일' : 'Files Generated'}
          </div>
          <div className="text-2xl font-bold text-[#39ff14]">
            {project.files_generated}
          </div>
        </div>
      )}

      {/* Generated Structure Preview */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-3">
          {locale === 'ko' ? '프로젝트 구조' : 'Project Structure'}
        </div>
        <pre className="text-xs text-[#c0c0c0] font-mono leading-relaxed overflow-x-auto">
{`${project.name}/
├── README.md
├── PLAN.md
├── .moss-project.json
├── src/
│   ${project.tech_stack?.frontend ? `├── frontend/          # ${project.tech_stack.frontend}` : ''}
│   ${project.tech_stack?.backend ? `└── backend/           # ${project.tech_stack.backend}` : ''}
${project.tech_stack?.blockchain ? `├── contracts/             # ${project.tech_stack.blockchain}` : ''}
├── docs/
│   └── api.md
└── tests/`}
        </pre>
      </div>

      {/* Timestamps */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">
          {locale === 'ko' ? '타임스탬프' : 'Timestamps'}
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-[#6b7280]">{locale === 'ko' ? '생성 시작: ' : 'Created: '}</span>
            <span className="text-[#c0c0c0]">
              {formatLocalDateTime(project.created_at, locale)}
            </span>
          </div>
          {project.completed_at && (
            <div>
              <span className="text-[#6b7280]">{locale === 'ko' ? '완료: ' : 'Completed: '}</span>
              <span className="text-[#c0c0c0]">
                {formatLocalDateTime(project.completed_at, locale)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Source Plan */}
      {plan && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">
            {locale === 'ko' ? '소스 Plan' : 'Source Plan'}
          </div>
          <button
            onClick={() => openModal('plan', { id: plan.id, title: plan.title })}
            className="w-full text-left p-3 border border-[#21262d] rounded hover:border-[#00ffff] transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <TerminalBadge variant={plan.status === 'approved' ? 'green' : 'cyan'}>
                {plan.status}
              </TerminalBadge>
              <span className="text-xs text-[#6b7280]">v{plan.version}</span>
            </div>
            <div className="text-sm text-[#c0c0c0]">
              {locale === 'ko' && plan.title_ko ? plan.title_ko : plan.title}
            </div>
          </button>
        </div>
      )}

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

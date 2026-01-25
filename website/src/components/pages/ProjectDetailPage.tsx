'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiProject } from '@/lib/api';
import { DetailPageLayout } from '../DetailPageLayout';
import { ProjectDetail } from '../details/ProjectDetail';

interface ProjectDetailPageProps {
  id: string;
}

export function ProjectDetailPage({ id }: ProjectDetailPageProps) {
  const { locale } = useI18n();
  const [project, setProject] = useState<ApiProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProject() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getProjectDetail(id);
        if (response.data) {
          setProject(response.data.project);
        } else {
          setError(response.error || (locale === 'ko' ? '프로젝트를 찾을 수 없습니다' : 'Project not found'));
        }
      } catch {
        setError(locale === 'ko' ? '데이터를 불러올 수 없습니다' : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }

    fetchProject();
  }, [id, locale]);

  const title = project
    ? project.name
    : (locale === 'ko' ? '프로젝트 상세' : 'Project Detail');

  return (
    <DetailPageLayout
      title={title}
      backUrl="/ideas"
      backLabel={locale === 'ko' ? '프로젝트 목록' : 'Back to Projects'}
      loading={loading}
      error={error}
    >
      {project && (
        <ProjectDetail data={{ id: project.id, title: project.name }} />
      )}
    </DetailPageLayout>
  );
}

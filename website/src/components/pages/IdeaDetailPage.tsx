'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiIdea } from '@/lib/api';
import { DetailPageLayout } from '../DetailPageLayout';
import { IdeaDetail } from '../details/IdeaDetail';

interface IdeaDetailPageProps {
  id: string;
}

export function IdeaDetailPage({ id }: IdeaDetailPageProps) {
  const { t, locale } = useI18n();
  const [idea, setIdea] = useState<ApiIdea | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchIdea() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getIdeaDetail(id);
        if (response.data) {
          setIdea(response.data.idea);
        } else {
          setError(response.error || (locale === 'ko' ? '아이디어를 찾을 수 없습니다' : 'Idea not found'));
        }
      } catch {
        setError(locale === 'ko' ? '데이터를 불러올 수 없습니다' : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }

    fetchIdea();
  }, [id, locale]);

  const getLocalizedText = (en: string | null | undefined, ko: string | null | undefined): string => {
    if (locale === 'ko' && ko) return ko;
    return en || '';
  };

  const title = idea
    ? getLocalizedText(idea.title, idea.title_ko)
    : (locale === 'ko' ? '아이디어 상세' : 'Idea Detail');

  return (
    <DetailPageLayout
      title={title}
      backUrl="/ideas"
      backLabel={locale === 'ko' ? '아이디어 목록' : 'Back to Ideas'}
      loading={loading}
      error={error}
    >
      {idea && (
        <IdeaDetail data={{ id: idea.id, title: idea.title }} />
      )}
    </DetailPageLayout>
  );
}

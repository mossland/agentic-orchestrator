'use client';

import { useEffect, useState } from 'react';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiSignal } from '@/lib/api';
import { DetailPageLayout } from '../DetailPageLayout';
import { SignalDetail } from '../details/SignalDetail';

interface SignalDetailPageProps {
  id: string;
}

export function SignalDetailPage({ id }: SignalDetailPageProps) {
  const { t, locale } = useI18n();
  const [signal, setSignal] = useState<ApiSignal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSignal() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getSignalDetail(id);
        if (response.data) {
          setSignal(response.data);
        } else {
          setError(response.error || (locale === 'ko' ? '시그널을 찾을 수 없습니다' : 'Signal not found'));
        }
      } catch {
        setError(locale === 'ko' ? '데이터를 불러올 수 없습니다' : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }

    fetchSignal();
  }, [id, locale]);

  const getLocalizedText = (en: string | null | undefined, ko: string | null | undefined): string => {
    if (locale === 'ko' && ko) return ko;
    return en || '';
  };

  const title = signal
    ? getLocalizedText(signal.title, signal.title_ko)
    : (locale === 'ko' ? '시그널 상세' : 'Signal Detail');

  return (
    <DetailPageLayout
      title={title}
      backUrl="/transparency/signals"
      backLabel={locale === 'ko' ? '시그널 목록' : 'Back to Signals'}
      loading={loading}
      error={error}
    >
      {signal && (
        <SignalDetail data={{ ...signal, title: signal.title }} />
      )}
    </DetailPageLayout>
  );
}

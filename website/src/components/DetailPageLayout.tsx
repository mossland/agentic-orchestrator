'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { useI18n } from '@/lib/i18n';

interface DetailPageLayoutProps {
  title: string;
  backUrl: string;
  backLabel: string;
  loading: boolean;
  error: string | null;
  children: React.ReactNode;
}

export function DetailPageLayout({
  title,
  backUrl,
  backLabel,
  loading,
  error,
  children,
}: DetailPageLayoutProps) {
  const { t, locale } = useI18n();

  return (
    <div className="min-h-screen pt-14 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Navigation */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <Link
            href={backUrl}
            className="inline-flex items-center gap-2 text-sm text-[#6b7280] hover:text-[#00ffff] transition-colors"
          >
            <span>←</span>
            <span>{backLabel}</span>
          </Link>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-xl font-bold text-[#39ff14] mb-2">
            {title}
          </h1>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded border border-[#21262d] bg-[#0d1117] p-6"
        >
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-[#00ffff] animate-pulse">
                $ {locale === 'ko' ? '로딩 중...' : 'Loading...'}
                <span className="cursor-blink">▋</span>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-[#ff5555] mb-4">[ERROR] {error}</div>
              <Link
                href={backUrl}
                className="text-[#00ffff] hover:underline text-sm"
              >
                {locale === 'ko' ? '← 목록으로 돌아가기' : '← Back to list'}
              </Link>
            </div>
          ) : (
            children
          )}
        </motion.div>
      </div>
    </div>
  );
}

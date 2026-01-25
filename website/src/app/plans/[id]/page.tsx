import { Metadata } from 'next';
import { PlanDetailPage } from '@/components/pages/PlanDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;

  return {
    title: `Plan - MOSS.AO`,
    description: `View plan details on MOSS.AO`,
    openGraph: {
      title: `Plan - MOSS.AO`,
      description: `View plan details on MOSS.AO`,
      url: `https://ao.moss.land/plans/${id}`,
      siteName: 'MOSS.AO',
      type: 'website',
    },
    twitter: {
      card: 'summary',
      title: `Plan - MOSS.AO`,
      description: `View plan details on MOSS.AO`,
    },
  };
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <PlanDetailPage id={id} />;
}

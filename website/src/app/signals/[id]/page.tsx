import { Metadata } from 'next';
import { SignalDetailPage } from '@/components/pages/SignalDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;

  return {
    title: `Signal - MOSS.AO`,
    description: `View signal details on MOSS.AO`,
    openGraph: {
      title: `Signal - MOSS.AO`,
      description: `View signal details on MOSS.AO`,
      url: `https://ao.moss.land/signals/${id}`,
      siteName: 'MOSS.AO',
      type: 'website',
    },
    twitter: {
      card: 'summary',
      title: `Signal - MOSS.AO`,
      description: `View signal details on MOSS.AO`,
    },
  };
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <SignalDetailPage id={id} />;
}

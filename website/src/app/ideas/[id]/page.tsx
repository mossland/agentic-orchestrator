import { Metadata } from 'next';
import { IdeaDetailPage } from '@/components/pages/IdeaDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;

  return {
    title: `Idea - MOSS.AO`,
    description: `View idea details on MOSS.AO`,
    openGraph: {
      title: `Idea - MOSS.AO`,
      description: `View idea details on MOSS.AO`,
      url: `https://ao.moss.land/ideas/${id}`,
      siteName: 'MOSS.AO',
      type: 'website',
    },
    twitter: {
      card: 'summary',
      title: `Idea - MOSS.AO`,
      description: `View idea details on MOSS.AO`,
    },
  };
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <IdeaDetailPage id={id} />;
}

import { Metadata } from 'next';
import { ProjectDetailPage } from '@/components/pages/ProjectDetailPage';

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;

  return {
    title: `Project - MOSS.AO`,
    description: `View project details on MOSS.AO`,
    openGraph: {
      title: `Project - MOSS.AO`,
      description: `View project details on MOSS.AO`,
      url: `https://ao.moss.land/projects/${id}`,
      siteName: 'MOSS.AO',
      type: 'website',
    },
    twitter: {
      card: 'summary',
      title: `Project - MOSS.AO`,
      description: `View project details on MOSS.AO`,
    },
  };
}

export default async function Page({ params }: Props) {
  const { id } = await params;
  return <ProjectDetailPage id={id} />;
}

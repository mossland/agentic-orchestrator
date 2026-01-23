'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { ApiClient } from '@/lib/api';
import { formatLocalDate } from '@/lib/date';
import type { ModalData } from '../modals/ModalProvider';

interface PipelineDetailProps {
  data: ModalData;
}

export function PipelineDetail({ data }: PipelineDetailProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stageData, setStageData] = useState<any>(null);
  const stageId = data.stageId as string;
  const stageName = data.stageName as string;
  const count = data.count as number;
  const status = data.status as string;

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch data based on stage type
        if (stageId === 'ideas') {
          const response = await ApiClient.getIdeas({ limit: 5 });
          if (response.data) {
            setStageData({
              items: response.data.ideas,
              total: response.data.total,
              statusCounts: response.data.status_counts,
            });
          }
        } else if (stageId === 'plans') {
          const response = await ApiClient.getPlans({ limit: 5 });
          if (response.data) {
            setStageData({
              items: response.data.plans,
              total: response.data.total,
            });
          }
        } else if (stageId === 'dev') {
          // No data yet for dev stage
          setStageData({ items: [], total: 0 });
        }
      } catch (error) {
        console.error('Failed to fetch pipeline data:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [stageId]);

  const statusColors = {
    active: { bg: 'bg-[#39ff14]/10', text: 'text-[#39ff14]', border: 'border-[#39ff14]' },
    completed: { bg: 'bg-[#6b7280]/10', text: 'text-[#c0c0c0]', border: 'border-[#6b7280]' },
    idle: { bg: 'bg-[#21262d]', text: 'text-[#6b7280]', border: 'border-[#21262d]' },
  };

  const colors = statusColors[status as keyof typeof statusColors] || statusColors.idle;

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="text-[#ff6b35] animate-pulse">
          Loading pipeline data...
          <span className="cursor-blink">_</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stage Header */}
      <div className={`text-center p-4 rounded border ${colors.border} ${colors.bg}`}>
        <div className={`text-3xl font-bold ${colors.text}`}>{count}</div>
        <div className="text-sm text-[#6b7280] uppercase tracking-wider">{stageName}</div>
        <div className="mt-2">
          <span className={`
            text-[10px] px-2 py-0.5 rounded uppercase tracking-wider
            ${status === 'active' ? 'bg-[#39ff14]/20 text-[#39ff14]' : ''}
            ${status === 'completed' ? 'bg-[#6b7280]/20 text-[#c0c0c0]' : ''}
            ${status === 'idle' ? 'bg-[#21262d] text-[#6b7280]' : ''}
          `}>
            {status}
          </span>
        </div>
      </div>

      {/* Stage Description */}
      <div className="text-xs text-[#6b7280]">
        <span className="text-[#bd93f9]"># </span>
        {stageId === 'ideas' && 'Ideas generated from trend analysis and debates'}
        {stageId === 'plans' && 'Detailed plans created through multi-stage debates'}
        {stageId === 'dev' && 'Projects in active development phase'}
      </div>

      {/* Recent Items */}
      {stageData?.items?.length > 0 && (
        <div className="space-y-2">
          <div className="text-[10px] text-[#6b7280] uppercase tracking-wider">
            Recent {stageName}
          </div>
          {stageData.items.map((item: any, idx: number) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="p-3 bg-[#0d1117] rounded border border-[#21262d] hover:border-[#39ff14]/50 transition-colors cursor-pointer"
              onClick={() => {
                // Navigate to the appropriate page
                if (stageId === 'ideas') {
                  router.push('/backlog');
                } else if (stageId === 'plans') {
                  router.push('/backlog?tab=plans');
                }
              }}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-[#c0c0c0] truncate">
                    {item.title}
                  </div>
                  <div className="flex gap-2 mt-1">
                    <span className={`
                      text-[10px] px-1.5 py-0.5 rounded
                      ${item.status === 'pending' ? 'bg-[#00ffff]/10 text-[#00ffff]' : ''}
                      ${item.status === 'approved' ? 'bg-[#39ff14]/10 text-[#39ff14]' : ''}
                      ${item.status === 'rejected' ? 'bg-[#ff5555]/10 text-[#ff5555]' : ''}
                      ${!['pending', 'approved', 'rejected'].includes(item.status) ? 'bg-[#6b7280]/10 text-[#6b7280]' : ''}
                    `}>
                      {item.status}
                    </span>
                    {item.created_at && (
                      <span className="text-[10px] text-[#3b3b3b]">
                        {formatLocalDate(item.created_at)}
                      </span>
                    )}
                  </div>
                </div>
                <span className="text-[#21262d]">→</span>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {stageData?.items?.length === 0 && (
        <div className="text-center py-6">
          <div className="text-4xl mb-3">
            {stageId === 'ideas' && '💡'}
            {stageId === 'plans' && '📋'}
            {stageId === 'dev' && '🚀'}
          </div>
          <div className="text-sm text-[#6b7280]">No items in this stage</div>
          <div className="text-[10px] text-[#3b3b3b] mt-1">
            {stageId === 'ideas' && 'Run trend analysis to generate ideas'}
            {stageId === 'plans' && 'Ideas will become plans through debates'}
            {stageId === 'dev' && 'Approved plans will move to development'}
          </div>
        </div>
      )}

      {/* Status Counts for Ideas */}
      {stageId === 'ideas' && stageData?.statusCounts && (
        <div className="border-t border-[#21262d] pt-4">
          <div className="text-[10px] text-[#6b7280] mb-2 uppercase tracking-wider">
            Status breakdown
          </div>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(stageData.statusCounts).map(([status, count]) => (
              <div key={status} className="text-center p-2 bg-[#0d1117] rounded">
                <div className="text-sm font-bold text-[#c0c0c0]">{count as number}</div>
                <div className="text-[10px] text-[#6b7280]">{status}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View All Button */}
      <div className="text-center pt-2">
        <button
          onClick={() => {
            if (stageId === 'ideas' || stageId === 'plans') {
              router.push('/backlog');
            } else if (stageId === 'dev') {
              router.push('/backlog?tab=in-dev');
            }
          }}
          className="btn-cli text-xs py-1.5 px-4"
        >
          View All {stageName} →
        </button>
      </div>
    </div>
  );
}

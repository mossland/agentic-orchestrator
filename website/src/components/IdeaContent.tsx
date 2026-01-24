'use client';

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';

interface IdeaContentProps {
  content: string;
  contentKo?: string | null;
}

interface IdeaStructure {
  idea_title?: string;
  core_analysis?: string;
  opportunity_risk?: {
    opportunities?: string;
    risks?: string;
    differentiators?: string;
  };
  proposal?: {
    description?: string;
    core_features?: string[];
    tech_stack?: string[];
    mvp_scope?: string;
  };
  roadmap?: {
    week1?: string;
    week2?: string;
    resources?: string;
    [key: string]: string | undefined;
  };
  kpis?: Array<{
    metric?: string;
    target?: string;
    measurement?: string;
  }>;
}

function parseIdeaContent(content: string): IdeaStructure | null {
  try {
    // Remove markdown code block if present
    let jsonStr = content.trim();
    if (jsonStr.startsWith('```json')) {
      jsonStr = jsonStr.slice(7);
    }
    if (jsonStr.startsWith('```')) {
      jsonStr = jsonStr.slice(3);
    }
    if (jsonStr.endsWith('```')) {
      jsonStr = jsonStr.slice(0, -3);
    }
    jsonStr = jsonStr.trim();

    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

export function IdeaContent({ content, contentKo }: IdeaContentProps) {
  const { locale } = useI18n();

  const displayContent = locale === 'ko' && contentKo ? contentKo : content;
  const parsed = useMemo(() => parseIdeaContent(displayContent), [displayContent]);

  // If not valid JSON, display as plain text
  if (!parsed) {
    return (
      <div className="text-sm text-[#c0c0c0] leading-relaxed whitespace-pre-wrap">
        {displayContent}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Core Analysis */}
      {parsed.core_analysis && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h4 className="text-xs uppercase tracking-wider text-[#bd93f9] flex items-center gap-2">
            <span className="text-[#39ff14]">#</span> Core Analysis
          </h4>
          <p className="text-sm text-[#c0c0c0] leading-relaxed pl-4 border-l-2 border-[#bd93f9]/30">
            {parsed.core_analysis}
          </p>
        </motion.div>
      )}

      {/* Opportunity & Risk */}
      {parsed.opportunity_risk && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-3"
        >
          <h4 className="text-xs uppercase tracking-wider text-[#bd93f9] flex items-center gap-2">
            <span className="text-[#39ff14]">#</span> Opportunity & Risk
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {parsed.opportunity_risk.opportunities && (
              <div className="bg-[#39ff14]/5 border border-[#39ff14]/20 rounded p-3">
                <div className="text-[10px] uppercase text-[#39ff14] mb-1">Opportunities</div>
                <p className="text-xs text-[#c0c0c0] leading-relaxed">
                  {parsed.opportunity_risk.opportunities}
                </p>
              </div>
            )}
            {parsed.opportunity_risk.risks && (
              <div className="bg-[#ff5555]/5 border border-[#ff5555]/20 rounded p-3">
                <div className="text-[10px] uppercase text-[#ff5555] mb-1">Risks</div>
                <p className="text-xs text-[#c0c0c0] leading-relaxed">
                  {parsed.opportunity_risk.risks}
                </p>
              </div>
            )}
          </div>
          {parsed.opportunity_risk.differentiators && (
            <div className="bg-[#00ffff]/5 border border-[#00ffff]/20 rounded p-3">
              <div className="text-[10px] uppercase text-[#00ffff] mb-1">Differentiators</div>
              <p className="text-xs text-[#c0c0c0] leading-relaxed">
                {parsed.opportunity_risk.differentiators}
              </p>
            </div>
          )}
        </motion.div>
      )}

      {/* Proposal */}
      {parsed.proposal && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-3"
        >
          <h4 className="text-xs uppercase tracking-wider text-[#bd93f9] flex items-center gap-2">
            <span className="text-[#39ff14]">#</span> Proposal
          </h4>
          {parsed.proposal.description && (
            <p className="text-sm text-[#c0c0c0] leading-relaxed pl-4 border-l-2 border-[#bd93f9]/30">
              {parsed.proposal.description}
            </p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {parsed.proposal.core_features && parsed.proposal.core_features.length > 0 && (
              <div className="bg-black/20 rounded p-3">
                <div className="text-[10px] uppercase text-[#f1fa8c] mb-2">Core Features</div>
                <ul className="space-y-1">
                  {parsed.proposal.core_features.map((feature, idx) => (
                    <li key={idx} className="text-xs text-[#c0c0c0] flex items-start gap-2">
                      <span className="text-[#39ff14]">+</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {parsed.proposal.tech_stack && parsed.proposal.tech_stack.length > 0 && (
              <div className="bg-black/20 rounded p-3">
                <div className="text-[10px] uppercase text-[#f1fa8c] mb-2">Tech Stack</div>
                <div className="flex flex-wrap gap-1">
                  {parsed.proposal.tech_stack.map((tech, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-2 py-0.5 bg-[#00ffff]/10 text-[#00ffff] rounded"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          {parsed.proposal.mvp_scope && (
            <div className="bg-black/20 rounded p-3">
              <div className="text-[10px] uppercase text-[#f1fa8c] mb-1">MVP Scope</div>
              <p className="text-xs text-[#c0c0c0] leading-relaxed">
                {parsed.proposal.mvp_scope}
              </p>
            </div>
          )}
        </motion.div>
      )}

      {/* Roadmap */}
      {parsed.roadmap && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-2"
        >
          <h4 className="text-xs uppercase tracking-wider text-[#bd93f9] flex items-center gap-2">
            <span className="text-[#39ff14]">#</span> Roadmap
          </h4>
          <div className="space-y-2">
            {Object.entries(parsed.roadmap).map(([key, value]) => {
              if (!value) return null;
              const label = key.startsWith('week') ? `Week ${key.slice(4)}` : key.charAt(0).toUpperCase() + key.slice(1);
              return (
                <div key={key} className="flex items-start gap-3 text-xs">
                  <span className="text-[#ff6b35] font-mono w-20 shrink-0">{label}</span>
                  <span className="text-[#c0c0c0]">{value}</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* KPIs */}
      {parsed.kpis && parsed.kpis.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="space-y-2"
        >
          <h4 className="text-xs uppercase tracking-wider text-[#bd93f9] flex items-center gap-2">
            <span className="text-[#39ff14]">#</span> KPIs
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {parsed.kpis.map((kpi, idx) => (
              <div key={idx} className="bg-black/20 rounded p-2 flex items-center justify-between">
                <div>
                  <div className="text-xs text-[#c0c0c0]">{kpi.metric}</div>
                  <div className="text-[10px] text-[#6b7280]">{kpi.measurement}</div>
                </div>
                <div className="text-sm font-bold text-[#39ff14]">{kpi.target}</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

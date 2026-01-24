'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiIdea } from '@/lib/api';

interface IdeaNetworkProps {
  ideas: ApiIdea[];
  onIdeaClick?: (ideaId: string) => void;
  showLabels?: boolean;
}

interface NetworkNode {
  id: string;
  title: string;
  score: number;
  status: string;
  x: number;
  y: number;
  radius: number;
  connections: string[];
}

interface NetworkLink {
  source: string;
  target: string;
  strength: number;
}

export function IdeaNetwork({ ideas, onIdeaClick, showLabels = true }: IdeaNetworkProps) {
  const { t } = useI18n();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const { nodes, links } = useMemo(() => {
    const nodes: NetworkNode[] = [];
    const links: NetworkLink[] = [];

    // Calculate node positions in a force-directed-like layout
    const centerX = 200;
    const centerY = 200;
    const radius = 150;

    ideas.forEach((idea, index) => {
      const angle = (index / ideas.length) * 2 * Math.PI - Math.PI / 2;
      const r = radius * (0.6 + Math.random() * 0.4);

      nodes.push({
        id: idea.id,
        title: idea.title,
        score: idea.score,
        status: idea.status,
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
        radius: 8 + (idea.score / 10) * 12,
        connections: [],
      });
    });

    // Create connections based on similar keywords or source types
    for (let i = 0; i < ideas.length; i++) {
      for (let j = i + 1; j < ideas.length; j++) {
        const ideaA = ideas[i];
        const ideaB = ideas[j];

        // Calculate similarity (simple heuristic based on source and score proximity)
        const sourceMatch = ideaA.source_type === ideaB.source_type ? 0.5 : 0;
        const scoreSimilarity = 1 - Math.abs(ideaA.score - ideaB.score) / 10;
        const statusMatch = ideaA.status === ideaB.status ? 0.3 : 0;

        const strength = sourceMatch + scoreSimilarity * 0.5 + statusMatch;

        if (strength > 0.6) {
          links.push({
            source: ideaA.id,
            target: ideaB.id,
            strength,
          });
          nodes.find((n) => n.id === ideaA.id)?.connections.push(ideaB.id);
          nodes.find((n) => n.id === ideaB.id)?.connections.push(ideaA.id);
        }
      }
    }

    return { nodes, links };
  }, [ideas]);

  const getNodeColor = (status: string, score: number) => {
    if (status === 'promoted') return '#39ff14';
    if (status === 'in-development') return '#ff6b35';
    if (score >= 7) return '#00ffff';
    if (score >= 5) return '#bd93f9';
    return '#6b7280';
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(selectedNode === nodeId ? null : nodeId);
    if (onIdeaClick) {
      onIdeaClick(nodeId);
    }
  };

  const connectedNodes = useMemo(() => {
    if (!hoveredNode && !selectedNode) return new Set<string>();
    const activeNode = hoveredNode || selectedNode;
    const node = nodes.find((n) => n.id === activeNode);
    return new Set([activeNode!, ...(node?.connections || [])]);
  }, [hoveredNode, selectedNode, nodes]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#6b7280] uppercase tracking-wider">
          {t('ideaNetwork.title')}
        </span>
        <span className="text-xs text-[#6b7280]">
          {nodes.length} {t('ideaNetwork.nodes')}, {links.length} {t('ideaNetwork.connections')}
        </span>
      </div>

      {/* Network Graph */}
      <div className="relative bg-[#0d1117] rounded-lg border border-[#21262d] overflow-hidden">
        <svg
          width="100%"
          height="400"
          viewBox="0 0 400 400"
          className="cursor-move"
        >
          {/* Links */}
          <g className="links">
            {links.map((link, idx) => {
              const sourceNode = nodes.find((n) => n.id === link.source);
              const targetNode = nodes.find((n) => n.id === link.target);
              if (!sourceNode || !targetNode) return null;

              const isHighlighted =
                connectedNodes.has(link.source) && connectedNodes.has(link.target);

              return (
                <motion.line
                  key={`link-${idx}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: isHighlighted ? 0.8 : 0.2 }}
                  x1={sourceNode.x}
                  y1={sourceNode.y}
                  x2={targetNode.x}
                  y2={targetNode.y}
                  stroke={isHighlighted ? '#00ffff' : '#21262d'}
                  strokeWidth={link.strength * 2}
                />
              );
            })}
          </g>

          {/* Nodes */}
          <g className="nodes">
            {nodes.map((node, idx) => {
              const isActive = hoveredNode === node.id || selectedNode === node.id;
              const isConnected = connectedNodes.has(node.id);
              const isVisible = connectedNodes.size === 0 || isConnected;

              return (
                <g key={node.id}>
                  {/* Node Circle */}
                  <motion.circle
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{
                      scale: isActive ? 1.3 : 1,
                      opacity: isVisible ? 1 : 0.3,
                    }}
                    transition={{ delay: idx * 0.02 }}
                    cx={node.x}
                    cy={node.y}
                    r={node.radius}
                    fill={getNodeColor(node.status, node.score)}
                    stroke={isActive ? '#ffffff' : 'transparent'}
                    strokeWidth={2}
                    className="cursor-pointer"
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    onClick={() => handleNodeClick(node.id)}
                  />

                  {/* Score Label */}
                  <text
                    x={node.x}
                    y={node.y}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className="text-[8px] fill-black font-bold pointer-events-none"
                  >
                    {node.score.toFixed(0)}
                  </text>

                  {/* Title Label */}
                  {showLabels && (isActive || node.score >= 7) && (
                    <motion.text
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      x={node.x}
                      y={node.y + node.radius + 12}
                      textAnchor="middle"
                      className="text-[9px] fill-[#c0c0c0] pointer-events-none"
                    >
                      {node.title.slice(0, 20)}
                      {node.title.length > 20 ? '...' : ''}
                    </motion.text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-[10px] pt-2 border-t border-[#21262d]">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-[#39ff14]" />
          <span className="text-[#6b7280]">{t('ideaNetwork.promoted')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-[#ff6b35]" />
          <span className="text-[#6b7280]">{t('ideaNetwork.inDev')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-[#00ffff]" />
          <span className="text-[#6b7280]">{t('ideaNetwork.highScore')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-[#bd93f9]" />
          <span className="text-[#6b7280]">{t('ideaNetwork.medScore')}</span>
        </div>
      </div>

      {/* Selected Node Info */}
      {selectedNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-cli p-3"
        >
          {(() => {
            const node = nodes.find((n) => n.id === selectedNode);
            const idea = ideas.find((i) => i.id === selectedNode);
            if (!node || !idea) return null;

            return (
              <>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-[#00ffff] font-bold">
                    {idea.title}
                  </span>
                  <span className={`text-sm font-bold ${
                    idea.score >= 7 ? 'text-[#39ff14]' :
                    idea.score >= 5 ? 'text-[#00ffff]' : 'text-[#6b7280]'
                  }`}>
                    {idea.score.toFixed(1)}
                  </span>
                </div>
                <p className="text-xs text-[#c0c0c0] line-clamp-2">{idea.summary}</p>
                <div className="flex items-center gap-2 mt-2 text-[10px]">
                  <span className="text-[#6b7280]">{t('ideaNetwork.connected')}:</span>
                  <span className="text-[#bd93f9]">{node.connections.length}</span>
                  <span className="text-[#6b7280]">|</span>
                  <span className={`px-1.5 py-0.5 rounded ${
                    idea.status === 'promoted' ? 'bg-[#39ff14]/20 text-[#39ff14]' :
                    idea.status === 'in-development' ? 'bg-[#ff6b35]/20 text-[#ff6b35]' :
                    'bg-[#6b7280]/20 text-[#6b7280]'
                  }`}>
                    {idea.status}
                  </span>
                </div>
              </>
            );
          })()}
        </motion.div>
      )}
    </div>
  );
}

// Mini version showing just connection stats
export function IdeaNetworkStats({ ideas }: { ideas: ApiIdea[] }) {
  const { t } = useI18n();

  const stats = useMemo(() => {
    let connections = 0;
    for (let i = 0; i < ideas.length; i++) {
      for (let j = i + 1; j < ideas.length; j++) {
        const sourceMatch = ideas[i].source_type === ideas[j].source_type ? 0.5 : 0;
        const scoreSimilarity = 1 - Math.abs(ideas[i].score - ideas[j].score) / 10;
        if (sourceMatch + scoreSimilarity * 0.5 > 0.6) connections++;
      }
    }
    return { nodes: ideas.length, connections };
  }, [ideas]);

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-[#00ffff]">{stats.nodes}</span>
      <span className="text-[#6b7280]">{t('ideaNetwork.nodes')}</span>
      <span className="text-[#6b7280]">•</span>
      <span className="text-[#bd93f9]">{stats.connections}</span>
      <span className="text-[#6b7280]">{t('ideaNetwork.connections')}</span>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { AdapterInfo } from '@/lib/types';

interface AdapterDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  adapters: AdapterInfo[];
  isLoading: boolean;
}

export function AdapterDetailModal({
  isOpen,
  onClose,
  adapters,
  isLoading,
}: AdapterDetailModalProps) {
  const { locale } = useI18n();
  const [selectedAdapter, setSelectedAdapter] = useState<AdapterInfo | null>(null);

  // Auto-select first adapter when adapters load
  useEffect(() => {
    if (adapters.length > 0 && !selectedAdapter) {
      setSelectedAdapter(adapters[0]);
    }
  }, [adapters, selectedAdapter]);

  // Reset selection when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSelectedAdapter(null);
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
    }
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const categoryColors: Record<string, string> = {
    news: 'text-[#f1fa8c]',
    crypto: 'text-[#00ffff]',
    social: 'text-[#ff6b35]',
    web3: 'text-[#bd93f9]',
    dev: 'text-[#39ff14]',
  };

  const categoryIcons: Record<string, string> = {
    news: '📰',
    crypto: '⛓️',
    social: '💬',
    web3: '🌐',
    dev: '💻',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-4 md:inset-10 bg-[#0d1117] border border-[#30363d] rounded-lg z-50 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[#30363d]">
              <div className="flex items-center gap-3">
                <span className="text-[#bd93f9]">◈</span>
                <h2 className="text-lg font-mono text-[#c0c0c0]">
                  {locale === 'ko' ? '시그널 어댑터 상세 정보' : 'Signal Adapters Detail'}
                </h2>
                <span className="tag tag-cyan">{adapters.length} adapters</span>
              </div>
              <button
                onClick={onClose}
                className="text-[#6b7280] hover:text-[#c0c0c0] transition-colors text-xl"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden flex">
              {/* Adapter List */}
              <div className="w-1/3 border-r border-[#30363d] overflow-y-auto">
                {isLoading ? (
                  <div className="p-4 text-center text-[#6b7280]">
                    <motion.span
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      Loading adapters...
                    </motion.span>
                  </div>
                ) : (
                  <div className="divide-y divide-[#21262d]">
                    {adapters.map((adapter) => (
                      <button
                        key={adapter.name}
                        onClick={() => setSelectedAdapter(adapter)}
                        className={`w-full p-3 text-left hover:bg-[#21262d]/50 transition-colors ${
                          selectedAdapter?.name === adapter.name ? 'bg-[#21262d]' : ''
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span>{categoryIcons[adapter.category] || '📡'}</span>
                          <span className={`font-mono text-sm ${categoryColors[adapter.category] || 'text-[#c0c0c0]'}`}>
                            {adapter.name}
                          </span>
                          {adapter.enabled ? (
                            <span className="status-dot online ml-auto" style={{ width: 6, height: 6 }} />
                          ) : (
                            <span className="status-dot offline ml-auto" style={{ width: 6, height: 6 }} />
                          )}
                        </div>
                        <div className="text-[10px] text-[#6b7280] truncate">
                          {locale === 'ko' ? adapter.description : adapter.description_en}
                        </div>
                        {adapter.source_count && (
                          <div className="text-[10px] text-[#39ff14] mt-1">
                            {adapter.source_count} sources
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Adapter Detail */}
              <div className="flex-1 overflow-y-auto p-4">
                {selectedAdapter ? (
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{categoryIcons[selectedAdapter.category] || '📡'}</span>
                      <div>
                        <h3 className={`text-lg font-mono ${categoryColors[selectedAdapter.category] || 'text-[#c0c0c0]'}`}>
                          {selectedAdapter.name}
                        </h3>
                        <p className="text-xs text-[#6b7280]">
                          {locale === 'ko' ? selectedAdapter.description : selectedAdapter.description_en}
                        </p>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="bg-[#161b22] rounded-lg p-3 border border-[#30363d]">
                      <div className="text-[#bd93f9] text-xs mb-2"># Status</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-[#6b7280]">enabled:</span>
                          <span className={selectedAdapter.enabled ? 'text-[#39ff14]' : 'text-[#ff6b35]'}>
                            {selectedAdapter.enabled ? 'true' : 'false'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#6b7280]">category:</span>
                          <span className={categoryColors[selectedAdapter.category]}>{selectedAdapter.category}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#6b7280]">last_fetch:</span>
                          <span className="text-[#c0c0c0]">
                            {selectedAdapter.last_fetch || 'never'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#6b7280]">source_count:</span>
                          <span className="text-[#f1fa8c]">{selectedAdapter.source_count || 0}</span>
                        </div>
                      </div>
                    </div>

                    {/* Health Details */}
                    {selectedAdapter.health && Object.keys(selectedAdapter.health).length > 0 && (
                      <div className="bg-[#161b22] rounded-lg p-3 border border-[#30363d]">
                        <div className="text-[#bd93f9] text-xs mb-2"># Health Check</div>
                        <div className="space-y-1 text-xs font-mono">
                          {Object.entries(selectedAdapter.health).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-[#6b7280]">{key}:</span>
                              <span className={
                                value === true || value === 'connected' || value === 'healthy'
                                  ? 'text-[#39ff14]'
                                  : value === false || String(value).includes('error')
                                  ? 'text-[#ff6b35]'
                                  : 'text-[#c0c0c0]'
                              }>
                                {String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Sources List */}
                    {selectedAdapter.sources && selectedAdapter.sources.length > 0 && (
                      <div className="bg-[#161b22] rounded-lg p-3 border border-[#30363d]">
                        <div className="text-[#bd93f9] text-xs mb-2">
                          # Sources ({selectedAdapter.sources.length})
                        </div>
                        <div className="max-h-48 overflow-y-auto space-y-0.5">
                          {selectedAdapter.sources.map((source, idx) => (
                            <div key={idx} className="text-xs font-mono text-[#c0c0c0] flex items-center gap-2">
                              <span className="text-[#00ffff]">[{String(idx + 1).padStart(2, '0')}]</span>
                              <span>{source}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Error */}
                    {selectedAdapter.error && (
                      <div className="bg-[#2d1b1b] rounded-lg p-3 border border-[#ff6b35]/30">
                        <div className="text-[#ff6b35] text-xs mb-1"># Error</div>
                        <div className="text-xs text-[#c0c0c0] font-mono">
                          {selectedAdapter.error}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-[#6b7280] text-sm">
                    {locale === 'ko'
                      ? '왼쪽에서 어댑터를 선택하세요'
                      : 'Select an adapter from the list'
                    }
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-[#30363d] flex justify-between items-center text-xs">
              <div className="text-[#6b7280]">
                {adapters.filter(a => a.enabled).length} / {adapters.length} enabled
              </div>
              <div className="flex gap-2">
                {Object.entries(categoryIcons).map(([cat, icon]) => {
                  const count = adapters.filter(a => a.category === cat).length;
                  if (count === 0) return null;
                  return (
                    <span key={cat} className={`${categoryColors[cat]} flex items-center gap-1`}>
                      {icon} {count}
                    </span>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

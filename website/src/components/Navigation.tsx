'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useI18n, LanguageToggle } from '@/lib/i18n';
import { useState } from 'react';

export function Navigation() {
  const pathname = usePathname();
  const { t } = useI18n();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { href: '/', label: 'dashboard', cmd: 'home' },
    { href: '/trends', label: 'trends', cmd: 'signals' },
    { href: '/backlog', label: 'backlog', cmd: 'tasks' },
    { href: '/agents', label: 'agents', cmd: 'agents' },
    { href: '/system', label: 'system', cmd: 'status' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#21262d] bg-[#0d1117]/95 backdrop-blur-md">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-[#39ff14] font-bold text-sm tracking-wider glow-green">
            MOSS
          </span>
          <span className="text-[#6b7280]">::</span>
          <span className="text-[#00ffff] text-sm">AO</span>
          <span className="hidden sm:inline-block text-[#6b7280] text-xs ml-2">
            v0.4.0
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  relative px-3 py-1.5 text-xs tracking-wide transition-all
                  ${isActive
                    ? 'text-[#39ff14] bg-[#39ff14]/10 border border-[#39ff14]/30'
                    : 'text-[#6b7280] hover:text-[#c0c0c0] hover:bg-[#21262d]'
                  }
                `}
              >
                <span className="text-[#00ffff] mr-1">$</span>
                {item.cmd}
                {isActive && (
                  <motion.span
                    layoutId="cursor"
                    className="absolute -right-0.5 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-[#39ff14] cursor-blink"
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* System Status */}
          <motion.div
            className="hidden sm:flex items-center gap-2 px-2 py-1 border border-[#21262d] bg-[#0d1117]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="status-dot online"
              animate={{
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
            <span className="text-[10px] text-[#39ff14] uppercase tracking-wider">
              {t('nav.running')}
            </span>
          </motion.div>

          <LanguageToggle />

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-1 text-[#6b7280] hover:text-[#39ff14]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="md:hidden border-t border-[#21262d] bg-[#0d1117]"
        >
          <div className="px-4 py-2 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`
                    block px-3 py-2 text-xs
                    ${isActive
                      ? 'text-[#39ff14] bg-[#39ff14]/10'
                      : 'text-[#6b7280]'
                    }
                  `}
                >
                  <span className="text-[#00ffff]">$ </span>
                  {item.cmd}
                </Link>
              );
            })}
          </div>
        </motion.div>
      )}
    </nav>
  );
}

'use client';

import { motion } from 'framer-motion';

const socialLinks = [
  {
    name: 'X',
    href: 'https://x.com/TheMossland',
    icon: (
      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    name: 'Medium',
    href: 'https://medium.com/mossland-blog',
    icon: (
      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z" />
      </svg>
    ),
  },
  {
    name: 'GitHub',
    href: 'https://github.com/MosslandOpenDevs',
    icon: (
      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
      </svg>
    ),
  },
  {
    name: 'Email',
    href: 'mailto:contact@moss.land',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
      </svg>
    ),
  },
];

export function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="border-t border-[#21262d] bg-[#0d1117]"
    >
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left - Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-[#39ff14] font-bold tracking-wider glow-green">
                MOSS
              </span>
              <span className="text-[#6b7280]">::</span>
              <span className="text-[#00ffff]">AO</span>
            </div>
            <p className="text-[10px] text-[#6b7280] leading-relaxed">
              Multi-agent AI orchestration system<br />
              for the Mossland ecosystem
            </p>
            <div className="mt-3 text-[10px] text-[#6b7280]">
              <span className="text-[#bd93f9]"># </span>
              Building the Invisible Bridge
            </div>
          </div>

          {/* Center - Links */}
          <div className="flex justify-center">
            <div className="space-y-2">
              <div className="text-[10px] text-[#6b7280] uppercase tracking-wider mb-3">
                Quick Links
              </div>
              <a
                href="https://github.com/MosslandOpenDevs/agentic-orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs text-[#c0c0c0] hover:text-[#39ff14] transition-colors"
              >
                <span className="text-[#00ffff]">$ </span>source code
              </a>
              <a
                href="https://moss.land"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs text-[#c0c0c0] hover:text-[#39ff14] transition-colors"
              >
                <span className="text-[#00ffff]">$ </span>moss.land
              </a>
              <a
                href="https://docs.moss.land"
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs text-[#c0c0c0] hover:text-[#39ff14] transition-colors"
              >
                <span className="text-[#00ffff]">$ </span>documentation
              </a>
            </div>
          </div>

          {/* Right - Social */}
          <div className="flex flex-col items-end">
            <div className="text-[10px] text-[#6b7280] uppercase tracking-wider mb-3">
              Connect
            </div>
            <div className="flex items-center gap-2">
              {socialLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 border border-[#21262d] text-[#6b7280] hover:border-[#39ff14] hover:text-[#39ff14] transition-all"
                  aria-label={link.name}
                >
                  {link.icon}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-8 pt-4 border-t border-[#21262d] flex flex-wrap items-center justify-between gap-4">
          <div className="text-[10px] text-[#6b7280]">
            © 2025, 2026 MOSSLAND. ALL RIGHTS RESERVED.
          </div>
          <div className="flex items-center gap-4 text-[10px] text-[#6b7280]">
            <span>v0.5.1 "Bilingual"</span>
            <span className="text-[#21262d]">|</span>
            <span className="flex items-center gap-1">
              <span className="status-dot online" style={{ width: 4, height: 4 }} />
              System Online
            </span>
          </div>
        </div>
      </div>
    </motion.footer>
  );
}

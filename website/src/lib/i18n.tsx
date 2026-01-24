'use client';

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

type Locale = 'en' | 'ko';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const translations: Record<Locale, Record<string, string>> = {
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.trends': 'Trends',
    'nav.backlog': 'Backlog',
    'nav.system': 'System',
    'nav.running': 'RUNNING',
    
    'dashboard.title': 'Agentic Orchestrator',
    'dashboard.subtitle': 'Autonomous AI orchestration system for the Mossland ecosystem',
    'dashboard.lastRun': 'Last run:',
    'dashboard.nextRun': 'Next run:',
    
    'stats.totalIdeas': 'Total Ideas',
    'stats.plansGenerated': 'Plans',
    'stats.plansRejected': 'Rejected',
    'stats.inDevelopment': 'In Development',
    'stats.trendsAnalyzed': 'Trends Analyzed',
    
    'pipeline.title': 'Pipeline Status',
    'pipeline.ideas': 'Ideas',
    'pipeline.plans': 'Plans',
    'pipeline.inDev': 'In Dev',
    'pipeline.active': 'Active',
    'pipeline.completed': 'Completed',
    'pipeline.idle': 'Idle',
    
    'activity.title': 'Activity Log',
    'activity.streaming': 'streaming',
    'activity.trend': 'TREND',
    'activity.idea': 'IDEA',
    'activity.plan': 'PLAN',
    'activity.debate': 'DEBATE',
    'activity.dev': 'DEV',
    'activity.system': 'SYSTEM',
    
    'feeds.title': 'RSS Feed Sources',
    'feeds.total': 'Total Feeds',
    
    'providers.title': 'AI Providers',
    'providers.rotation': 'Roles rotate each round',
    
    'trends.title': 'Trend Analysis',
    'trends.subtitle': 'Trend analysis results from 17 RSS feeds',
    'trends.articles': 'articles',
    'trends.score': 'score',
    'trends.ideaSeeds': 'Idea seeds:',
    'trends.schedule': 'Analysis Schedule',
    'trends.scheduleTime': 'Daily at 08:00 KST (23:00 UTC)',
    'trends.scheduleDesc': 'Automated via GitHub Actions',
    
    'backlog.title': 'Backlog',
    'backlog.subtitle': 'Idea and plan management based on GitHub Issues',
    'backlog.ideas': 'Ideas',
    'backlog.plans': 'Plans',
    'backlog.inDevelopment': 'In Development',
    'backlog.debateHistory': 'Debate History',
    'backlog.rounds': 'rounds',
    'backlog.viewOnGithub': 'View on GitHub',
    'backlog.viewAllIssues': 'View All Issues on GitHub',
    
    'system.title': 'System Architecture',
    'system.subtitle': 'Mossland Agentic Orchestrator system structure',
    'system.pipelineStages': 'Pipeline Stages',
    'system.techStack': 'Tech Stack',
    'system.workflow': 'Workflow',
    'system.debate.title': 'Multi-Agent Debate System',
    'system.debate.rotation': 'AI providers rotate each round for diverse perspectives',
    'system.planGenerated': 'Plan Generated',
    
    'system.stage.ideation': 'Idea generation',
    'system.stage.planningDraft': 'PRD/Architecture draft',
    'system.stage.planningReview': 'Multi-agent debate',
    'system.stage.dev': 'Development scaffolding',
    'system.stage.qa': 'Quality assurance',
    'system.stage.done': 'Complete',
    
    'system.workflow.1': 'RSS Feed Collection',
    'system.workflow.1.desc': 'Collect latest articles from 17 feeds',
    'system.workflow.2': 'Trend Analysis',
    'system.workflow.2.desc': 'Extract trends and analyze Web3 relevance with Claude',
    'system.workflow.3': 'Idea Generation',
    'system.workflow.3.desc': 'Generate micro-service ideas based on trends',
    'system.workflow.4': 'Human-in-the-Loop',
    'system.workflow.4.desc': 'Humans decide promotions via labels',
    'system.workflow.5': 'Multi-Agent Debate',
    'system.workflow.5.desc': '4 roles × 3 AI rotation refines plans',
    'system.workflow.6': 'Development Scaffolding',
    'system.workflow.6.desc': 'Auto-generate project structure',
    
    'role.founder': 'Founder',
    'role.founder.perspective': 'Vision, conviction, execution',
    'role.vc': 'VC',
    'role.vc.perspective': 'Market viability, investment value, scalability',
    'role.accelerator': 'Accelerator',
    'role.accelerator.perspective': 'Feasibility, MVP, validation',
    'role.founderFriend': 'Founder Friend',
    'role.founderFriend.perspective': 'Peer perspective, creative ideas',
    
    'common.viewSource': 'View Source Code',

    // Navigation - transparency
    'nav.transparency': 'Transparency',

    // Modal
    'modal.signal.title': 'Signal Details',
    'modal.trend.title': 'Trend Analysis',
    'modal.idea.title': 'Idea Details',
    'modal.debate.title': 'Debate Session',
    'modal.plan.title': 'Plan Document',
    'modal.agent.title': 'Agent Profile',
    'modal.close': 'Close',

    // Detail components
    'detail.loading': 'Loading data...',
    'detail.notFound': 'Data not found',
    'detail.fetchError': 'Failed to fetch data',
    'detail.score': 'Score',
    'detail.relevance': 'Relevance',
    'detail.sentiment': 'Sentiment',
    'detail.summary': 'Summary',
    'detail.description': 'Description',
    'detail.topics': 'Topics',
    'detail.entities': 'Entities',
    'detail.keywords': 'Keywords',
    'detail.metadata': 'Metadata',
    'detail.collectedAt': 'Collected at',
    'detail.analyzedAt': 'Analyzed at',
    'detail.createdAt': 'Created at',
    'detail.updatedAt': 'Updated at',
    'detail.startedAt': 'Started at',
    'detail.completedAt': 'Completed at',
    'detail.source': 'Source',
    'detail.viewOriginal': 'View original',
    'detail.trendScore': 'Trend Score',
    'detail.signalCount': 'Signal Count',
    'detail.relatedSignals': 'Related Signals',
    'detail.ideaScore': 'Idea Score',
    'detail.potential': 'Potential',
    'detail.debatesCount': 'Debates',
    'detail.plansCount': 'Plans',
    'detail.rounds': 'rounds',
    'detail.versions': 'versions',
    'detail.ideaJourney': 'Idea Journey',
    'detail.debateHistory': 'Debate History',
    'detail.planVersions': 'Plan Versions',
    'detail.messages': 'messages',
    'detail.links': 'Links',
    'detail.viewOnGitHub': 'View on GitHub',
    'detail.debateSession': 'Debate Session',
    'detail.participants': 'Participants',
    'detail.currentRound': 'Current Round',
    'detail.maxRounds': 'Max Rounds',
    'detail.conversationView': 'Conversation',
    'detail.timelineView': 'Timeline',
    'detail.outcome': 'Outcome',
    'detail.timestamps': 'Timestamps',
    'detail.inProgress': 'In Progress',
    'detail.noContent': 'No content available',
    'detail.agentDescription': 'Description',
    'detail.personalityProfile': 'Personality Profile',
    'detail.creativity': 'Creativity',
    'detail.analytical': 'Analytical',
    'detail.riskTolerance': 'Risk Tolerance',
    'detail.collaboration': 'Collaboration',
    'detail.rolePerspective': 'Role Perspective',
    'detail.traitRadar': 'Trait Radar',
    'detail.fullDescription': 'Full Description',
    'detail.debateTimeline': 'Debate Timeline',
    'detail.expand': 'Expand',
    'detail.collapse': 'Collapse',
    'detail.clickToShowMessages': 'Click expand to show agent messages',
    'detail.originalContent': 'Original',
    'detail.translatedContent': 'Translated',
    'detail.showOriginal': 'Show Original',
    'detail.showTranslation': 'Show Korean',
    'detail.noTranslation': 'Translation not available',

    // Journey
    'journey.signalCollected': 'Signal Collected',
    'journey.trendIdentified': 'Trend Identified',
    'journey.ideaGenerated': 'Idea Generated',
    'journey.debateRound': 'Debate Round',
    'journey.planVersion': 'Plan v',
    'journey.inDevelopment': 'In Development',
    'journey.completed': 'Completed',

    // Transparency page
    'transparency.title': 'Transparency Dashboard',
    'transparency.subtitle': 'Full visibility into the AI orchestration process',
    'transparency.signals': 'Signals',
    'transparency.signalsDesc': 'Raw data collected from RSS feeds and other sources',
    'transparency.trends': 'Trends',
    'transparency.trendsDesc': 'Analyzed patterns and emerging topics',
    'transparency.ideas': 'Ideas',
    'transparency.ideasDesc': 'Generated ideas from trend analysis',
    'transparency.debates': 'Debates',
    'transparency.debatesDesc': 'Multi-agent discussions refining ideas',
    'transparency.plans': 'Plans',
    'transparency.plansDesc': 'Structured development plans',
    'transparency.agents': 'Agents',
    'transparency.agentsDesc': 'AI personas participating in debates',
    'transparency.today': 'today',
    'transparency.total': 'total',
    'transparency.active': 'active',
    'transparency.viewDetails': 'View details',
    'transparency.info1': 'This dashboard shows the complete AI decision-making process.',
    'transparency.info2': 'Click any card to explore detailed information and full conversation logs.',

    // Signals page
    'signals.title': 'Signal Explorer',
    'signals.subtitle': 'Browse all collected signals from various sources',
    'signals.source': 'Source',
    'signals.category': 'Category',
    'signals.minScore': 'Min Score',
    'signals.allSources': 'All Sources',
    'signals.allCategories': 'All Categories',
    'signals.anyScore': 'Any Score',
    'signals.high': 'High',
    'signals.medium': 'Medium',
    'signals.low': 'Low',
    'signals.noSignals': 'No signals found',

    // Debates page
    'debates.title': 'Debate History',
    'debates.subtitle': 'Explore multi-agent debate sessions',
    'debates.rotationInfo': 'AI providers rotate each round for diverse perspectives',
    'debates.status': 'Status',
    'debates.phase': 'Phase',
    'debates.allStatuses': 'All Statuses',
    'debates.allPhases': 'All Phases',
    'debates.completed': 'Completed',
    'debates.inProgress': 'In Progress',
    'debates.pending': 'Pending',
    'debates.divergence': 'Divergence',
    'debates.convergence': 'Convergence',
    'debates.planning': 'Planning',
    'debates.session': 'Session',
    'debates.messages': 'msgs',
    'debates.started': 'Started',
    'debates.noDebates': 'No debates found',
  },
  ko: {
    'nav.dashboard': '대시보드',
    'nav.trends': '트렌드',
    'nav.backlog': '백로그',
    'nav.system': '시스템',
    'nav.running': '실행중',
    
    'dashboard.title': 'Agentic Orchestrator',
    'dashboard.subtitle': '모스랜드 생태계를 위한 자율 AI 오케스트레이션 시스템',
    'dashboard.lastRun': '마지막 실행:',
    'dashboard.nextRun': '다음 실행:',
    
    'stats.totalIdeas': '전체 아이디어',
    'stats.plansGenerated': '플랜',
    'stats.plansRejected': '거부됨',
    'stats.inDevelopment': '개발 중',
    'stats.trendsAnalyzed': '분석된 트렌드',
    
    'pipeline.title': '파이프라인 상태',
    'pipeline.ideas': 'Ideas',
    'pipeline.plans': 'Plans',
    'pipeline.inDev': 'In Dev',
    'pipeline.active': '활성',
    'pipeline.completed': '완료',
    'pipeline.idle': '대기',
    
    'activity.title': '활동 로그',
    'activity.streaming': '스트리밍',
    'activity.trend': 'TREND',
    'activity.idea': 'IDEA',
    'activity.plan': 'PLAN',
    'activity.debate': 'DEBATE',
    'activity.dev': 'DEV',
    'activity.system': 'SYSTEM',
    
    'feeds.title': 'RSS 피드 소스',
    'feeds.total': '전체 피드',
    
    'providers.title': 'AI 프로바이더',
    'providers.rotation': '라운드마다 역할 순환 배정',
    
    'trends.title': '트렌드 분석',
    'trends.subtitle': '17개 RSS 피드에서 수집한 트렌드 분석 결과',
    'trends.articles': '기사',
    'trends.score': '점수',
    'trends.ideaSeeds': '아이디어 씨앗:',
    'trends.schedule': '분석 스케줄',
    'trends.scheduleTime': '매일 08:00 KST (23:00 UTC)',
    'trends.scheduleDesc': 'GitHub Actions 자동 실행',
    
    'backlog.title': '백로그',
    'backlog.subtitle': 'GitHub Issues 기반 아이디어 및 플랜 관리',
    'backlog.ideas': '아이디어',
    'backlog.plans': '플랜',
    'backlog.inDevelopment': '개발 중',
    'backlog.debateHistory': '토론 이력',
    'backlog.rounds': '라운드',
    'backlog.viewOnGithub': 'GitHub에서 보기',
    'backlog.viewAllIssues': 'GitHub에서 전체 이슈 보기',
    
    'system.title': '시스템 아키텍처',
    'system.subtitle': 'Mossland Agentic Orchestrator 시스템 구조',
    'system.pipelineStages': '파이프라인 단계',
    'system.techStack': '기술 스택',
    'system.workflow': '워크플로우',
    'system.debate.title': '멀티 에이전트 토론 시스템',
    'system.debate.rotation': 'AI 프로바이더가 라운드마다 순환하여 다양한 관점 제공',
    'system.planGenerated': 'Plan 생성 완료',
    
    'system.stage.ideation': '아이디어 생성',
    'system.stage.planningDraft': 'PRD/아키텍처 초안',
    'system.stage.planningReview': '멀티 에이전트 토론',
    'system.stage.dev': '개발 스캐폴딩',
    'system.stage.qa': '품질 검증',
    'system.stage.done': '완료',
    
    'system.workflow.1': 'RSS 피드 수집',
    'system.workflow.1.desc': '17개 피드에서 최신 기사 수집',
    'system.workflow.2': '트렌드 분석',
    'system.workflow.2.desc': 'Claude로 트렌드 추출 및 Web3 연관성 분석',
    'system.workflow.3': '아이디어 생성',
    'system.workflow.3.desc': '트렌드 기반 마이크로 서비스 아이디어 생성',
    'system.workflow.4': 'Human-in-the-Loop',
    'system.workflow.4.desc': '사람이 라벨로 프로모션 결정',
    'system.workflow.5': '멀티 에이전트 토론',
    'system.workflow.5.desc': '4역할 × 3 AI 순환으로 플랜 정제',
    'system.workflow.6': '개발 스캐폴딩',
    'system.workflow.6.desc': '프로젝트 구조 자동 생성',
    
    'role.founder': 'Founder',
    'role.founder.perspective': '비전, 확신, 실행력',
    'role.vc': 'VC',
    'role.vc.perspective': '시장성, 투자 가치, 확장성',
    'role.accelerator': 'Accelerator',
    'role.accelerator.perspective': '실행 가능성, MVP, 검증',
    'role.founderFriend': 'Founder Friend',
    'role.founderFriend.perspective': '동료 관점, 창의적 아이디어',
    
    'common.viewSource': '소스 코드 보기',

    // Navigation - transparency
    'nav.transparency': '투명성',

    // Modal
    'modal.signal.title': '신호 상세',
    'modal.trend.title': '트렌드 분석',
    'modal.idea.title': '아이디어 상세',
    'modal.debate.title': '토론 세션',
    'modal.plan.title': '플랜 문서',
    'modal.agent.title': '에이전트 프로필',
    'modal.close': '닫기',

    // Detail components
    'detail.loading': '데이터 로딩 중...',
    'detail.notFound': '데이터를 찾을 수 없음',
    'detail.fetchError': '데이터 조회 실패',
    'detail.score': '점수',
    'detail.relevance': '관련성',
    'detail.sentiment': '감정',
    'detail.summary': '요약',
    'detail.description': '설명',
    'detail.topics': '토픽',
    'detail.entities': '엔티티',
    'detail.keywords': '키워드',
    'detail.metadata': '메타데이터',
    'detail.collectedAt': '수집 시각',
    'detail.analyzedAt': '분석 시각',
    'detail.createdAt': '생성 시각',
    'detail.updatedAt': '수정 시각',
    'detail.startedAt': '시작 시각',
    'detail.completedAt': '완료 시각',
    'detail.source': '소스',
    'detail.viewOriginal': '원본 보기',
    'detail.trendScore': '트렌드 점수',
    'detail.signalCount': '신호 수',
    'detail.relatedSignals': '관련 신호',
    'detail.ideaScore': '아이디어 점수',
    'detail.potential': '잠재력',
    'detail.debatesCount': '토론',
    'detail.plansCount': '플랜',
    'detail.rounds': '라운드',
    'detail.versions': '버전',
    'detail.ideaJourney': '아이디어 여정',
    'detail.debateHistory': '토론 이력',
    'detail.planVersions': '플랜 버전',
    'detail.messages': '메시지',
    'detail.links': '링크',
    'detail.viewOnGitHub': 'GitHub에서 보기',
    'detail.debateSession': '토론 세션',
    'detail.participants': '참가자',
    'detail.currentRound': '현재 라운드',
    'detail.maxRounds': '최대 라운드',
    'detail.conversationView': '대화형',
    'detail.timelineView': '타임라인',
    'detail.outcome': '결과',
    'detail.timestamps': '타임스탬프',
    'detail.inProgress': '진행 중',
    'detail.noContent': '콘텐츠 없음',
    'detail.agentDescription': '설명',
    'detail.personalityProfile': '성격 프로필',
    'detail.creativity': '창의성',
    'detail.analytical': '분석력',
    'detail.riskTolerance': '위험 감수',
    'detail.collaboration': '협업',
    'detail.rolePerspective': '역할 관점',
    'detail.traitRadar': '특성 레이더',
    'detail.fullDescription': '전체 설명',
    'detail.debateTimeline': '토론 타임라인',
    'detail.expand': '펼치기',
    'detail.collapse': '접기',
    'detail.clickToShowMessages': '에이전트 메시지를 보려면 펼치기를 클릭하세요',
    'detail.originalContent': '원문',
    'detail.translatedContent': '번역',
    'detail.showOriginal': '원문 보기',
    'detail.showTranslation': '한글 보기',
    'detail.noTranslation': '번역 없음',

    // Journey
    'journey.signalCollected': '신호 수집',
    'journey.trendIdentified': '트렌드 식별',
    'journey.ideaGenerated': '아이디어 생성',
    'journey.debateRound': '토론 라운드',
    'journey.planVersion': '플랜 v',
    'journey.inDevelopment': '개발 중',
    'journey.completed': '완료',

    // Transparency page
    'transparency.title': '투명성 대시보드',
    'transparency.subtitle': 'AI 오케스트레이션 과정의 완전한 가시성',
    'transparency.signals': '신호',
    'transparency.signalsDesc': 'RSS 피드 및 기타 소스에서 수집된 원시 데이터',
    'transparency.trends': '트렌드',
    'transparency.trendsDesc': '분석된 패턴 및 신흥 토픽',
    'transparency.ideas': '아이디어',
    'transparency.ideasDesc': '트렌드 분석에서 생성된 아이디어',
    'transparency.debates': '토론',
    'transparency.debatesDesc': '아이디어를 정제하는 멀티 에이전트 토론',
    'transparency.plans': '플랜',
    'transparency.plansDesc': '구조화된 개발 계획',
    'transparency.agents': '에이전트',
    'transparency.agentsDesc': '토론에 참여하는 AI 페르소나',
    'transparency.today': '오늘',
    'transparency.total': '전체',
    'transparency.active': '활성',
    'transparency.viewDetails': '상세 보기',
    'transparency.info1': '이 대시보드는 완전한 AI 의사결정 과정을 보여줍니다.',
    'transparency.info2': '카드를 클릭하여 상세 정보와 전체 대화 기록을 탐색하세요.',

    // Signals page
    'signals.title': '신호 탐색기',
    'signals.subtitle': '다양한 소스에서 수집된 모든 신호 탐색',
    'signals.source': '소스',
    'signals.category': '카테고리',
    'signals.minScore': '최소 점수',
    'signals.allSources': '전체 소스',
    'signals.allCategories': '전체 카테고리',
    'signals.anyScore': '모든 점수',
    'signals.high': '높음',
    'signals.medium': '중간',
    'signals.low': '낮음',
    'signals.noSignals': '신호를 찾을 수 없음',

    // Debates page
    'debates.title': '토론 이력',
    'debates.subtitle': '멀티 에이전트 토론 세션 탐색',
    'debates.rotationInfo': 'AI 프로바이더가 라운드마다 순환하여 다양한 관점 제공',
    'debates.status': '상태',
    'debates.phase': '단계',
    'debates.allStatuses': '전체 상태',
    'debates.allPhases': '전체 단계',
    'debates.completed': '완료',
    'debates.inProgress': '진행 중',
    'debates.pending': '대기 중',
    'debates.divergence': '발산',
    'debates.convergence': '수렴',
    'debates.planning': '계획',
    'debates.session': '세션',
    'debates.messages': '메시지',
    'debates.started': '시작',
    'debates.noDebates': '토론을 찾을 수 없음',
  },
};

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>('en');

  const t = useCallback(
    (key: string): string => {
      return translations[locale][key] || key;
    },
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}

export function LanguageToggle() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex items-center gap-1 rounded-lg border border-zinc-700 bg-zinc-800/50 p-0.5">
      <button
        onClick={() => setLocale('en')}
        className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
          locale === 'en'
            ? 'bg-zinc-600 text-white'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLocale('ko')}
        className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
          locale === 'ko'
            ? 'bg-zinc-600 text-white'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        KO
      </button>
    </div>
  );
}

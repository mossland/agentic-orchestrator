export interface SystemStats {
  totalIdeas: number;
  totalPlans: number;
  plansRejected: number;
  inDevelopment: number;
  trendsAnalyzed: number;
  lastRun: string;
  nextRun: string;
}

export interface ActivityItem {
  time: string;
  type: string;
  message: string;
}

export interface Trend {
  title: string;
  score: number;
  category: string;
  articles: number;
  summary?: string;
  ideaSeeds?: string[];
}

export interface Idea {
  id: number;
  title: string;
  status: string;
  source: string;
  created: string;
  issueUrl?: string;
}

export interface Plan {
  id: number;
  title: string;
  ideaId: number;
  status: string;
  debateRounds: number;
  created: string;
  issueUrl?: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  count: number;
  status: 'active' | 'completed' | 'idle';
}

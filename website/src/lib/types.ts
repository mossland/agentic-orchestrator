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
  analyzedAt?: string;
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

// Transparency Dashboard Types
export interface SignalDetail {
  id: string;
  source: string;
  category: string;
  title: string;
  summary: string | null;
  url: string | null;
  score: number;
  sentiment: string | null;
  topics: string[];
  entities: string[];
  collected_at: string | null;
}

export interface TrendDetail {
  id: string;
  period: string;
  name: string;
  description: string | null;
  score: number;
  signal_count: number;
  category: string | null;
  keywords: string[];
  analyzed_at: string | null;
  related_signals?: SignalDetail[];
  generated_ideas?: string[];
}

export interface IdeaJourney {
  idea: {
    id: string;
    title: string;
    title_ko: string | null;
    summary: string;
    summary_ko: string | null;
    description: string | null;
    description_ko: string | null;
    source_type: string;
    status: string;
    score: number;
    created_at: string | null;
  };
  source_trend?: TrendDetail;
  debates: DebateSession[];
  plans: PlanVersion[];
  timeline: TimelineEvent[];
}

export interface DebateSession {
  id: string;
  idea_id: string;
  phase: string;
  round_number: number;
  max_rounds: number;
  status: string;
  participants: string[];
  outcome: string | null;
  started_at: string | null;
  completed_at: string | null;
  message_count?: number;
}

export interface DebateMessage {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_handle: string | null;
  message_type: string;
  content: string;
  content_ko: string | null;
  created_at: string | null;
}

export interface DebateTranscript {
  debate: DebateSession;
  messages: DebateMessage[];
  participants: Array<{
    id: string;
    name: string;
    role: string;
  }>;
}

export interface PlanVersion {
  id: string;
  idea_id: string;
  title: string;
  title_ko: string | null;
  version: number;
  status: string;
  final_plan: string | null;
  final_plan_ko: string | null;
  created_at: string | null;
}

export interface TimelineEvent {
  timestamp: string;
  type: 'signal' | 'trend' | 'idea' | 'debate' | 'plan' | 'status_change';
  title: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

// Adapter types
export interface AdapterInfo {
  name: string;
  category: string;
  description: string;
  description_en: string;
  enabled: boolean;
  last_fetch: string | null;
  health: Record<string, unknown>;
  sources?: string[];
  source_count?: number;
  error?: string;
}

// Project types
export interface Project {
  id: string;
  plan_id: string;
  name: string;
  directory_path: string | null;
  tech_stack: {
    frontend?: string;
    backend?: string;
    database?: string;
    blockchain?: string;
    additional?: string[];
  };
  status: 'pending' | 'generating' | 'ready' | 'error';
  files_generated: number;
  created_at: string | null;
  completed_at: string | null;
}

export interface GenerateProjectResponse {
  job_id: string;
  status: 'accepted' | 'exists' | 'in_progress';
  message: string;
}

export interface ProjectJobStatus {
  job_id: string;
  plan_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: {
    success: boolean;
    project_id?: string;
    project_path?: string;
    files_generated?: number;
    error?: string;
  };
  error?: string;
}

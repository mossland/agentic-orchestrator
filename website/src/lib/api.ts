/**
 * API Client for MOSS.AO Backend
 *
 * Provides typed API calls to the FastAPI backend with fallback to mock data
 * when the API is unavailable.
 */

import type {
  SystemStats,
  ActivityItem,
  Trend,
  Idea,
  Plan,
  PipelineStage,
} from './types';
import {
  mockStats,
  mockActivity,
  mockTrends,
  mockIdeas,
  mockPlans,
  mockPipeline,
} from '@/data/mock';

// API base URL - can be configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

// Types for API responses
export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  isFromCache: boolean;
}

export interface StatusResponse {
  status: string;
  timestamp: string;
  components: Record<string, { status: string }>;
  stats: {
    signals_today: number;
    debates_today: number;
    ideas_generated: number;
    plans_created: number;
    agents_active: number;
  };
}

export interface SignalsResponse {
  signals: ApiSignal[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiSignal {
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

export interface TrendsResponse {
  trends: ApiTrend[];
  total: number;
  limit: number;
  offset: number;
  period: string;
}

export interface ApiTrend {
  id: string;
  period: string;
  name: string;
  description: string | null;
  score: number;
  signal_count: number;
  category: string | null;
  keywords: string[];
  analyzed_at: string | null;
}

export interface IdeasResponse {
  ideas: ApiIdea[];
  total: number;
  limit: number;
  offset: number;
  status_counts: Record<string, number>;
}

export interface ApiIdea {
  id: string;
  title: string;
  summary: string;
  source_type: string;
  status: string;
  score: number;
  github_issue_url: string | null;
  created_at: string | null;
}

export interface PlansResponse {
  plans: ApiPlan[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiPlan {
  id: string;
  idea_id: string;
  title: string;
  version: number;
  status: string;
  github_issue_url: string | null;
  created_at: string | null;
}

export interface DebatesResponse {
  debates: ApiDebate[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiDebate {
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

export interface UsageResponse {
  today: {
    total_cost: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_requests: number;
  };
  today_by_provider: Record<string, {
    cost: number;
    input_tokens: number;
    output_tokens: number;
    requests: number;
  }>;
  month_total: number;
  history: Array<{
    date: string;
    cost: number;
    requests: number;
  }>;
  days: number;
}

export interface ActivityResponse {
  activities: Array<{
    time: string;
    type: string;
    message: string;
    level: string;
  }>;
  total: number;
}

export interface AgentsResponse {
  agents: Array<{
    id: string;
    name: string;
    role: string;
    phase: string;
    personality: {
      creativity: number;
      analytical: number;
      risk_tolerance: number;
      collaboration: number;
    };
  }>;
  total: number;
}

// Generic fetch function with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return { data, error: null, isFromCache: false };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.warn(`API request failed for ${endpoint}:`, errorMessage);
    return { data: null, error: errorMessage, isFromCache: false };
  }
}

// API Client class
export class ApiClient {
  // Health & Status
  static async getHealth() {
    return apiFetch<{ status: string; timestamp: string; version: string }>('/health');
  }

  static async getStatus(): Promise<ApiResponse<StatusResponse>> {
    return apiFetch<StatusResponse>('/status');
  }

  // Signals
  static async getSignals(params?: {
    limit?: number;
    offset?: number;
    source?: string;
    category?: string;
    min_score?: number;
    hours?: number;
  }): Promise<ApiResponse<SignalsResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.source) searchParams.set('source', params.source);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.min_score) searchParams.set('min_score', params.min_score.toString());
    if (params?.hours) searchParams.set('hours', params.hours.toString());

    const query = searchParams.toString();
    return apiFetch<SignalsResponse>(`/signals${query ? `?${query}` : ''}`);
  }

  // Trends
  static async getTrends(params?: {
    limit?: number;
    offset?: number;
    period?: '24h' | '7d' | '30d';
    category?: string;
  }): Promise<ApiResponse<TrendsResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.period) searchParams.set('period', params.period);
    if (params?.category) searchParams.set('category', params.category);

    const query = searchParams.toString();
    return apiFetch<TrendsResponse>(`/trends${query ? `?${query}` : ''}`);
  }

  // Ideas
  static async getIdeas(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<IdeasResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    return apiFetch<IdeasResponse>(`/ideas${query ? `?${query}` : ''}`);
  }

  static async getIdeaDetail(ideaId: string) {
    return apiFetch<{
      idea: ApiIdea;
      debates: ApiDebate[];
      plans: ApiPlan[];
    }>(`/ideas/${ideaId}`);
  }

  // Plans
  static async getPlans(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<PlansResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    return apiFetch<PlansResponse>(`/plans${query ? `?${query}` : ''}`);
  }

  static async getPlanDetail(planId: string) {
    return apiFetch<ApiPlan & {
      prd_content: string | null;
      architecture_content: string | null;
      user_research_content: string | null;
      business_model_content: string | null;
      project_plan_content: string | null;
      final_plan: string | null;
      updated_at: string | null;
    }>(`/plans/${planId}`);
  }

  // Debates
  static async getDebates(params?: {
    limit?: number;
    offset?: number;
    status?: string;
    phase?: string;
  }): Promise<ApiResponse<DebatesResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.status) searchParams.set('status', params.status);
    if (params?.phase) searchParams.set('phase', params.phase);

    const query = searchParams.toString();
    return apiFetch<DebatesResponse>(`/debates${query ? `?${query}` : ''}`);
  }

  static async getDebateDetail(sessionId: string) {
    return apiFetch<{
      debate: ApiDebate;
      messages: Array<{
        id: string;
        agent_id: string;
        agent_name: string;
        agent_handle: string | null;
        message_type: string;
        content: string;
        content_ko: string | null;
        created_at: string | null;
      }>;
      message_count: number;
    }>(`/debates/${sessionId}`);
  }

  // Usage
  static async getUsage(days?: number): Promise<ApiResponse<UsageResponse>> {
    const query = days ? `?days=${days}` : '';
    return apiFetch<UsageResponse>(`/usage${query}`);
  }

  // Activity
  static async getActivity(limit?: number): Promise<ApiResponse<ActivityResponse>> {
    const query = limit ? `?limit=${limit}` : '';
    return apiFetch<ActivityResponse>(`/activity${query}`);
  }

  // Agents
  static async getAgents(phase?: string): Promise<ApiResponse<AgentsResponse>> {
    const query = phase ? `?phase=${phase}` : '';
    return apiFetch<AgentsResponse>(`/agents${query}`);
  }
}

// Helper functions to convert API data to frontend types with mock fallback

export async function fetchSystemStats(): Promise<SystemStats> {
  const { data, error } = await ApiClient.getStatus();

  if (error || !data) {
    console.warn('Using mock stats due to API error');
    return mockStats;
  }

  // Try to get ideas/plans counts
  const ideasRes = await ApiClient.getIdeas({ limit: 1 });
  const plansRes = await ApiClient.getPlans({ limit: 1 });

  const totalIdeas = ideasRes.data?.total ?? mockStats.totalIdeas;
  const totalPlans = plansRes.data?.total ?? mockStats.totalPlans;

  return {
    totalIdeas,
    totalPlans,
    plansRejected: 0, // Would need status filter
    inDevelopment: 0,
    trendsAnalyzed: data.stats.signals_today,
    lastRun: new Date().toISOString(),
    nextRun: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  };
}

export async function fetchActivity(): Promise<ActivityItem[]> {
  const { data, error } = await ApiClient.getActivity(20);

  if (error || !data || data.activities.length === 0) {
    console.warn('Using mock activity due to API error or empty data');
    return mockActivity;
  }

  return data.activities.map((a) => ({
    time: a.time,
    type: a.type,
    message: a.message,
  }));
}

export async function fetchTrends(): Promise<Trend[]> {
  const { data, error } = await ApiClient.getTrends({ limit: 20 });

  if (error || !data || data.trends.length === 0) {
    console.warn('Using mock trends due to API error or empty data');
    return mockTrends;
  }

  return data.trends.map((t) => ({
    title: t.name,
    score: t.score,
    category: t.category || 'other',
    articles: t.signal_count,
    summary: t.description || undefined,
    ideaSeeds: t.keywords?.slice(0, 3),
  }));
}

export async function fetchIdeas(): Promise<Idea[]> {
  const { data, error } = await ApiClient.getIdeas({ limit: 50 });

  if (error || !data || data.ideas.length === 0) {
    console.warn('Using mock ideas due to API error or empty data');
    return mockIdeas;
  }

  return data.ideas.map((i, index) => ({
    id: index + 1, // Use index for display number
    title: i.title,
    status: i.status,
    source: i.source_type,
    created: i.created_at?.split('T')[0] || '',
    issueUrl: i.github_issue_url || undefined,
  }));
}

export async function fetchPlans(): Promise<Plan[]> {
  const { data, error } = await ApiClient.getPlans({ limit: 50 });

  if (error || !data || data.plans.length === 0) {
    console.warn('Using mock plans due to API error or empty data');
    return mockPlans;
  }

  return data.plans.map((p, index) => ({
    id: index + 1,
    title: p.title,
    ideaId: parseInt(p.idea_id) || index + 1,
    status: p.status,
    debateRounds: p.version,
    created: p.created_at?.split('T')[0] || '',
    issueUrl: p.github_issue_url || undefined,
  }));
}

export async function fetchPipeline(): Promise<PipelineStage[]> {
  const ideasRes = await ApiClient.getIdeas({ limit: 1 });
  const plansRes = await ApiClient.getPlans({ limit: 1 });

  if (ideasRes.error || plansRes.error) {
    console.warn('Using mock pipeline due to API error');
    return mockPipeline;
  }

  return [
    {
      id: 'ideas',
      name: 'Ideas',
      count: ideasRes.data?.total || 0,
      status: 'completed',
    },
    {
      id: 'plans',
      name: 'Plans',
      count: plansRes.data?.total || 0,
      status: 'active',
    },
    {
      id: 'dev',
      name: 'In Dev',
      count: 0,
      status: 'idle',
    },
  ];
}

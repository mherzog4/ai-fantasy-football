export interface Player {
  lineup_slot: number;
  player?: string;
  player_name: string;
  position: string;
  nfl_team: string;
  projection: number;
  injury_status: string;
  ownership?: number;
  player_id?: number;
}

export interface Team {
  team_name: string;
  record: string;
  roster: Player[];
}

export interface MatchupData {
  my_team: Team;
  opponent_team: Team;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  tool?: string;
}

export interface ChatRequest {
  message: string;
  conversation_history?: Array<{role: string; content: string}>;
  league_context?: {
    scoring: string;
    league_size: number;
    season: number;
  };
}

export interface ChatResponse {
  status: string;
  response: string;
  tool_calls: Array<{tool: string}>;
  enhanced_data: Array<{
    tool: string;
    data?: Record<string, unknown>;
    error?: string;
  }>;
}

export interface UsageStats {
  current_hourly_usage: number;
  hourly_limit: number;
  remaining_budget: number;
  percentage_used: number;
  rate_limiting_enabled: boolean;
}

export interface LineupOptimization {
  optimal_lineup: Record<string, {
    name: string;
    projection: number;
    reason: string;
  }>;
  projected_total: number;
  confidence_level: string;
  key_decisions: string[];
}

export interface WaiverWireRecommendation {
  player_name: string;
  position: string;
  nfl_team: string;
  projected_value: number;
  priority: 'High' | 'Medium' | 'Low';
  reasoning: string;
}

export interface WaiverWireAnalysis {
  top_recommendations: WaiverWireRecommendation[];
}

export interface TradeTarget {
  target_team: string;
  trade_proposal: {
    give: string[];
    receive: string[];
  };
  confidence: 'High' | 'Medium' | 'Low';
  trade_reasoning: string;
}

export interface TradeAnalysis {
  trade_targets: TradeTarget[];
}

export interface InjuryReport {
  summary: {
    healthy_count: number;
    total_players: number;
    injury_percentage: number;
  };
  healthy_players: Player[];
  questionable_players: Player[];
  doubtful_players: Player[];
  out_players: Player[];
  ir_players: Player[];
  web_search_results?: Array<{results: string}>;
}

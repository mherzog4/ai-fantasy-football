import axios from 'axios';
import { ChatRequest, ChatResponse, MatchupData, UsageStats } from './types';

// Use environment variable or fallback to localhost
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Matchup data
  getMatchup: async (): Promise<MatchupData> => {
    const response = await api.get('/get_matchup');
    return response.data;
  },

  // Chat endpoints
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/chat/enhanced', request);
    return response.data;
  },

  // Usage statistics
  getUsageStats: async (): Promise<UsageStats> => {
    const response = await api.get('/usage/stats');
    return response.data;
  },

  // Test ESPN connection
  testEspn: async () => {
    const response = await api.get('/test_espn');
    return response.data;
  },
};

// Error handler for API calls
export const handleApiError = (error: unknown): string => {
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    
    if (err.response && typeof err.response === 'object' && err.response !== null) {
      const response = err.response as Record<string, unknown>;
      if (response.status === 429) {
        return 'Rate limit exceeded. Please wait before making another request.';
      }
      
      if (response.data && typeof response.data === 'object' && response.data !== null) {
        const data = response.data as Record<string, unknown>;
        if (data.detail && typeof data.detail === 'string') {
          return data.detail;
        }
      }
    }
    
    if (err.code === 'ECONNABORTED') {
      return 'Request timed out. The AI analysis is taking too long. Please try a simpler question or try again later.';
    }
    
    if (err.message && typeof err.message === 'string') {
      return err.message;
    }
  }
  
  return 'An unexpected error occurred. Please try again.';
};

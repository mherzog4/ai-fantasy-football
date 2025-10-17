import { type ClassValue, clsx } from "clsx"

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatPosition(positionId: number | string): string {
  // If it's already a string position name, return it directly
  if (typeof positionId === 'string' && ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'FLEX', 'BENCH', 'IR'].includes(positionId)) {
    return positionId;
  }
  
  const positions: Record<number | string, string> = {
    0: "QB", 1: "RB", 2: "RB", 3: "WR", 4: "WR", 5: "TE", 6: "TE", 7: "FLEX", 
    8: "K", 9: "DEF", 10: "DEF", 11: "DEF", 12: "DEF", 13: "DEF", 14: "DEF", 
    15: "DEF", 16: "DEF", 17: "K", 18: "DEF", 19: "DEF", 20: "BENCH", 21: "IR",
    22: "FLEX", 23: "FLEX"
  };
  return positions[positionId] || `${positionId}`;
}

export function formatTeam(teamId: number): string {
  const teams: Record<number, string> = {
    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
    9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
    17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
    25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 31: "BAL", 32: "HOU",
    34: "HOU"
  };
  return teams[teamId] || `TEAM${teamId}`;
}

export function formatProjection(projection: number): string {
  return Math.round(projection).toString();
}

export function getPriorityText(priority: 'High' | 'Medium' | 'Low'): string {
  switch (priority) {
    case 'High': return 'HIGH';
    case 'Medium': return 'MED';
    case 'Low': return 'LOW';
    default: return 'UNK';
  }
}

export function getConfidenceText(confidence: 'High' | 'Medium' | 'Low'): string {
  switch (confidence) {
    case 'High': return 'HIGH';
    case 'Medium': return 'MED';
    case 'Low': return 'LOW';
    default: return 'UNK';
  }
}

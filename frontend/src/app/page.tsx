'use client';

import { useState, useEffect } from 'react';
import { MatchupData, Player } from '../lib/types';
import { apiClient, handleApiError } from '../lib/api';
import { formatPosition } from '../lib/utils';
import MatchupHeader from '../components/MatchupHeader';
import RosterTable from '../components/RosterTable';
import UsageMonitor from '../components/UsageMonitor';
import ChatInterface from '../components/ChatInterface';
import { Loader2, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const [matchupData, setMatchupData] = useState<MatchupData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMatchupData = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getMatchup();
        setMatchupData(data);
      } catch (err) {
        setError(handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchMatchupData();
  }, []);

  const calculateProjections = (roster: Player[]): number => {
    return roster
      .filter(player => player.lineup_slot < 20 || [22, 23].includes(player.lineup_slot))
      .reduce((total, player) => total + (player.projection || 0), 0);
  };

  const comparePositions = (myRoster: Player[], opponentRoster: Player[]) => {
    const myPositions: Record<string, Player[]> = {};
    const oppPositions: Record<string, Player[]> = {};

    // Group starting lineup players by position
    myRoster
      .filter(player => player.lineup_slot < 20 || [22, 23].includes(player.lineup_slot))
      .forEach(player => {
        const pos = formatPosition(player.position);
        if (!myPositions[pos]) myPositions[pos] = [];
        myPositions[pos].push(player);
      });

    opponentRoster
      .filter(player => player.lineup_slot < 20 || [22, 23].includes(player.lineup_slot))
      .forEach(player => {
        const pos = formatPosition(player.position);
        if (!oppPositions[pos]) oppPositions[pos] = [];
        oppPositions[pos].push(player);
      });

    const positionAdvantages: Record<string, 'my_team' | 'opponent' | 'tie'> = {};

    const allPositions = new Set([...Object.keys(myPositions), ...Object.keys(oppPositions)]);

    allPositions.forEach(pos => {
      const myTotal = (myPositions[pos] || []).reduce((sum, p) => sum + (p.projection || 0), 0);
      const oppTotal = (oppPositions[pos] || []).reduce((sum, p) => sum + (p.projection || 0), 0);

      if (myTotal > oppTotal) {
        positionAdvantages[pos] = 'my_team';
      } else if (oppTotal > myTotal) {
        positionAdvantages[pos] = 'opponent';
      } else {
        positionAdvantages[pos] = 'tie';
      }
    });

    return positionAdvantages;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-indigo-600" />
          <p className="text-gray-600">Loading your fantasy dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!matchupData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No matchup data available</p>
        </div>
      </div>
    );
  }

  const myProjectedTotal = calculateProjections(matchupData.my_team.roster);
  const opponentProjectedTotal = calculateProjections(matchupData.opponent_team.roster);
  const positionAdvantages = comparePositions(matchupData.my_team.roster, matchupData.opponent_team.roster);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Fantasy Football Dashboard
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-6 gap-6">
          {/* Sidebar */}
          <div className="xl:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h2 className="text-base font-semibold mb-3 text-black">
                AI Assistant
              </h2>
              <p className="text-xs text-gray-800 mb-3">
                Your AI fantasy expert!
              </p>
              <div className="space-y-1 text-xs text-gray-800">
                <div>
                  • Lineup optimization
                </div>
                <div>
                  • Start/sit decisions
                </div>
                <div>
                  • Waiver wire analysis
                </div>
                <div>
                  • Trade opportunities
                </div>
              </div>
            </div>

            <UsageMonitor />
          </div>

          {/* Main Content */}
          <div className="xl:col-span-5 space-y-8 w-full">
            {/* Matchup Header */}
            <MatchupHeader
              myTeam={matchupData.my_team}
              opponentTeam={matchupData.opponent_team}
              myProjectedTotal={myProjectedTotal}
              opponentProjectedTotal={opponentProjectedTotal}
            />

            {/* Roster Tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
              <RosterTable
                teamName={matchupData.my_team.team_name}
                roster={matchupData.my_team.roster}
                positionAdvantages={positionAdvantages}
                isMyTeam={true}
              />
              <RosterTable
                teamName={matchupData.opponent_team.team_name}
                roster={matchupData.opponent_team.roster}
                positionAdvantages={positionAdvantages}
                isMyTeam={false}
              />
            </div>

            {/* Chat Interface */}
            <ChatInterface />

            {/* Footer */}
            <footer className="text-center py-4 text-sm text-gray-500 border-t border-gray-200">
              <p>Powered by ESPN Fantasy API + OpenAI GPT-4</p>
            </footer>
          </div>
        </div>
      </main>
    </div>
  );
}

'use client';

import { Team } from '../lib/types';

interface MatchupHeaderProps {
  myTeam: Team;
  opponentTeam: Team;
  myProjectedTotal: number;
  opponentProjectedTotal: number;
}

export default function MatchupHeader({ 
  myTeam, 
  opponentTeam, 
  myProjectedTotal, 
  opponentProjectedTotal 
}: MatchupHeaderProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl w-full mb-8 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-purple-700 text-white p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
          {/* My Team */}
          <div className="text-left">
            <div className="w-20 h-20 bg-white/20 border-3 border-white/30 rounded-full flex items-center justify-center text-2xl font-bold text-white mb-4 mx-auto md:mx-0">
              {myTeam.team_name.charAt(0)}
            </div>
            <h2 className="text-2xl font-bold mb-2 text-center md:text-left">{myTeam.team_name}</h2>
            <div className="text-lg text-white/90 mb-2 text-center md:text-left">{myTeam.record}</div>
            <div className="text-3xl font-bold text-center md:text-left">{myProjectedTotal.toFixed(0)}</div>
            <div className="text-sm text-white/80 uppercase tracking-wide text-center md:text-left">Projected Points</div>
          </div>

          {/* VS */}
          <div className="text-center">
            <div className="text-2xl font-bold opacity-80">VS</div>
          </div>

          {/* Opponent Team */}
          <div className="text-right">
            <div className="w-20 h-20 bg-white/20 border-3 border-white/30 rounded-full flex items-center justify-center text-2xl font-bold text-white mb-4 mx-auto md:mx-0 md:ml-auto">
              {opponentTeam.team_name.charAt(0)}
            </div>
            <h2 className="text-2xl font-bold mb-2 text-center md:text-right">{opponentTeam.team_name}</h2>
            <div className="text-lg text-white/90 mb-2 text-center md:text-right">{opponentTeam.record}</div>
            <div className="text-3xl font-bold text-center md:text-right">{opponentProjectedTotal.toFixed(0)}</div>
            <div className="text-sm text-white/80 uppercase tracking-wide text-center md:text-right">Projected Points</div>
          </div>
        </div>
      </div>
    </div>
  );
}

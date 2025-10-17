'use client';

import { Player } from '@/lib/types';
import { formatPosition, formatTeam, formatProjection } from '@/lib/utils';

interface RosterTableProps {
  teamName: string;
  roster: Player[];
  positionAdvantages: Record<string, 'my_team' | 'opponent' | 'tie'>;
  isMyTeam?: boolean;
}

export default function RosterTable({ 
  teamName, 
  roster, 
  positionAdvantages, 
  isMyTeam = false 
}: RosterTableProps) {
  // Define proper lineup order
  const getPositionOrder = (lineup_slot: number): number => {
    // Standard lineup order: QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BENCH, IR
    const slotOrder: Record<number, number> = {
      0: 0,   // QB
      1: 1,   // RB  
      2: 2,   // RB
      3: 3,   // WR
      4: 4,   // WR
      5: 5,   // TE
      6: 6,   // TE (backup)
      7: 7,   // FLEX
      22: 7,  // FLEX (alternative slot)
      23: 7,  // FLEX (alternative slot)
      17: 8,  // K
      8: 8,   // K (alternative slot)
      16: 9,  // DEF
      9: 9,   // DEF (alternative slot)
      20: 10, // BENCH
      21: 11, // IR
    };
    return slotOrder[lineup_slot] ?? 999; // Unknown slots go to end
  };

  // Sort roster by proper lineup order
  const sortedRoster = [...roster].sort((a, b) => {
    const orderA = getPositionOrder(a.lineup_slot);
    const orderB = getPositionOrder(b.lineup_slot);
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    // If same position order, sort by original slot number
    return a.lineup_slot - b.lineup_slot;
  });
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 w-full">
      <h3 className="text-base font-semibold mb-3 text-black">
        {teamName}
      </h3>
      
      <div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-300">
              <th className="text-center py-2 px-1 w-8 text-black font-semibold">Adv</th>
              <th className="text-left py-2 px-1 w-12 text-black font-semibold">Pos</th>
              <th className="text-left py-2 px-2 min-w-0 text-black font-semibold">Player</th>
              <th className="text-center py-2 px-1 w-10 text-black font-semibold">Team</th>
              <th className="text-right py-2 px-1 w-12 text-black font-semibold">Proj</th>
              <th className="text-center py-2 px-1 w-8 text-black font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedRoster.map((player, index) => {
              const position = formatPosition(player.position);
              const nflTeam = typeof player.nfl_team === 'number' 
                ? formatTeam(player.nfl_team) 
                : player.nfl_team;
              
              const hasAdvantage = isMyTeam 
                ? positionAdvantages[position] === 'my_team'
                : positionAdvantages[position] === 'opponent';
              
              const isStarter = player.lineup_slot < 20 || [22, 23].includes(player.lineup_slot);
              
              return (
                <tr 
                  key={`${player.player || player.player_name}-${index}`} 
                  className={`border-b border-gray-100 hover:bg-gray-50 ${
                    isStarter ? 'bg-blue-50/30' : ''
                  }`}
                >
                  <td className="py-1 px-1 text-center text-black font-semibold">
                    {hasAdvantage ? 'Yes' : ''}
                  </td>
                  <td className="py-1 px-1 font-semibold text-black">
                    {position}
                  </td>
                  <td className="py-1 px-2">
                    <div className="font-medium text-black truncate">
                      {player.player_name || player.player || 'Unknown'}
                    </div>
                  </td>
                  <td className="py-1 px-1 text-black text-center">
                    {nflTeam}
                  </td>
                  <td className="py-1 px-1 text-right font-semibold text-black">
                    {formatProjection(player.projection)}
                  </td>
                  <td className="py-1 px-1 text-center">
                    {player.injury_status && player.injury_status !== 'ACTIVE' ? (
                      <span className="text-xs px-1 py-0.5 rounded bg-red-100 text-red-700">
                        {player.injury_status.substring(0, 1)}
                      </span>
                    ) : (
                    <span className="text-green-500">Active</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

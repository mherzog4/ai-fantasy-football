#!/usr/bin/env python3
"""
Test script to verify waiver wire filtering is working correctly
"""

import sys
import os
sys.path.append('.')

from api.main import get_mock_waiver_players_filtered

def test_waiver_filtering():
    print("🧪 Testing waiver wire filtering...")
    
    # Mock league rosters with some owned players
    mock_league_rosters = [
        {
            "team_id": 1,
            "roster": [
                {"player": "Denver Broncos", "position": "DEF"},
                {"player": "Cam Akers", "position": "RB"},
                {"player": "Tyler Allgeier", "position": "RB"}
            ]
        },
        {
            "team_id": 2, 
            "roster": [
                {"player": "Justice Hill", "position": "RB"},
                {"player": "Cairo Santos", "position": "K"}
            ]
        }
    ]
    
    print(f"Mock owned players:")
    for roster in mock_league_rosters:
        for player in roster["roster"]:
            print(f"  - {player['player']} ({player['position']})")
    
    # Get available players
    available = get_mock_waiver_players_filtered(5, mock_league_rosters)
    
    print(f"\n✅ Available players (should exclude owned players):")
    for player in available:
        print(f"  - {player['name']} ({player['position']}) - {player['nfl_team']} - {player['projection']} pts")
    
    # Check that owned players are filtered out
    available_names = {p['name'].lower() for p in available}
    
    should_be_filtered = [
        "Denver Broncos".lower(),  # Note: mock data has "Broncos" not "Denver Broncos"
        "Cam Akers".lower(),
        "Tyler Allgeier".lower(),
        "Justice Hill".lower(),
        "Cairo Santos".lower()
    ]
    
    print(f"\n🔍 Checking filtering:")
    for name in should_be_filtered:
        if name in available_names:
            print(f"  ❌ FAILED: {name} should be filtered out but is still available")
        else:
            print(f"  ✅ PASSED: {name} correctly filtered out")
    
    # Special check for Broncos (since mock data just says "Broncos")
    broncos_available = any("broncos" in p['name'].lower() for p in available)
    if broncos_available:
        print(f"  ❌ FAILED: Broncos defense should be filtered out")
    else:
        print(f"  ✅ PASSED: Broncos defense correctly not available")
    
    print(f"\n📊 Summary: Found {len(available)} available players after filtering")

if __name__ == "__main__":
    test_waiver_filtering()
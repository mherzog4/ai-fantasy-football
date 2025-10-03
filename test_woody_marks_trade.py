#!/usr/bin/env python3

import requests
import json

def test_woody_marks_trade():
    """Test trade analysis specifically for Woody Marks"""
    
    # Mock roster data with Woody Marks on the team
    my_roster = [
        {"name": "Josh Allen", "position": "QB", "projection": 22.5, "lineup_slot": 0},
        {"name": "Saquon Barkley", "position": "RB", "projection": 18.2, "lineup_slot": 2},
        {"name": "Woody Marks", "position": "RB", "projection": 6.8, "lineup_slot": 20},  # Bench player
        {"name": "Tyreek Hill", "position": "WR", "projection": 16.5, "lineup_slot": 4},
        {"name": "A.J. Brown", "position": "WR", "projection": 15.8, "lineup_slot": 5},
        {"name": "Travis Kelce", "position": "TE", "projection": 12.1, "lineup_slot": 6},
    ]
    
    # Mock league rosters
    league_rosters = [
        {
            "team_id": 2,
            "team_name": "Team 2",
            "record": "(2-2)",
            "roster": [
                {"name": "Kyren Williams", "position": "RB", "projection": 14.2, "lineup_slot": 2},  # Starter
                {"name": "Lamar Jackson", "position": "QB", "projection": 21.8, "lineup_slot": 0},
                {"name": "Some Backup RB", "position": "RB", "projection": 7.1, "lineup_slot": 20},  # Similar to Woody
            ]
        }
    ]
    
    # Test with the AI service directly
    from api.ai_services import FantasyAIService
    
    ai_service = FantasyAIService()
    
    # Mock league context with specific target player
    league_context = {
        "current_week": 5,
        "target_player": "Woody Marks",
        "player_research": "⚠️ Research shows Woody Marks is a bench/fringe RB with limited trade value"
    }
    
    print("🔍 TESTING WOODY MARKS TRADE ANALYSIS")
    print("=" * 50)
    
    try:
        result = ai_service.analyze_trade_opportunities(my_roster, league_rosters, league_context)
        
        if result.get("status") == "success":
            trade_targets = result.get("trade_targets", [])
            
            if not trade_targets:
                print("✅ GOOD: No unrealistic trades suggested for Woody Marks")
            else:
                print(f"📋 Found {len(trade_targets)} trade suggestions:")
                
                for i, trade in enumerate(trade_targets, 1):
                    give_players = trade.get("trade_proposal", {}).get("give", [])
                    receive_players = trade.get("trade_proposal", {}).get("receive", [])
                    
                    print(f"\n{i}. {trade.get('target_team', 'Unknown Team')}")
                    print(f"   📤 Give: {', '.join(give_players)}")
                    print(f"   📥 Receive: {', '.join(receive_players)}")
                    print(f"   🎯 Reasoning: {trade.get('trade_reasoning', 'No reasoning provided')}")
                    
                    # Check if trade seems realistic
                    if "Woody Marks" in give_players:
                        print("   ✅ Correctly includes Woody Marks as requested")
                        
                        # Check if it's a realistic trade
                        if len(give_players) == 1 and len(receive_players) == 1:
                            receive_player = receive_players[0]
                            if "Williams" in receive_player or "starter" in trade.get('trade_reasoning', '').lower():
                                print("   ❌ UNREALISTIC: Trading bench player for starter")
                            else:
                                print("   ✅ REALISTIC: Trading for similar-value player")
                        else:
                            print("   ✅ REALISTIC: Multi-player trade (likely 2-for-1 or similar)")
                    else:
                        print("   ❌ ERROR: Does not include Woody Marks as requested")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_woody_marks_trade()

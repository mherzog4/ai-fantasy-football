from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import json
import requests
from urllib.parse import unquote
import dotenv
from typing import List, Optional, Dict
from .ai_services import FantasyAIService

dotenv.load_dotenv()

app = FastAPI(title="Fantasy Football API", description="ESPN Fantasy Football API Wrapper")

# Initialize AI service
ai_service = FantasyAIService()

# Pydantic models for request/response
class PlayerComparisonRequest(BaseModel):
    player1_name: str
    player2_name: str
    
class LineupOptimizationRequest(BaseModel):
    include_opponent_context: bool = True

class WaiverWireRequest(BaseModel):
    include_league_context: bool = True
    max_players_per_position: int = 10

class TradeAnalysisRequest(BaseModel):
    include_league_rosters: bool = True
    focus_positions: Optional[List[str]] = None

# --- CONFIG ---
LEAGUE_ID = os.getenv("LEAGUE_ID")  
TEAM_ID = os.getenv("TEAM_ID")
SEASON = 2025
WEEK = None        # Set to None to auto-detect current week, or specify a week number

# Get cookies from environment variables
ESPN_S2_ENCODED = os.getenv("ESPN_S2_ENCODED")
ESPN_AUTH = os.getenv("ESPN_AUTH")
ESPN_S2 = os.getenv("ESPN_S2") or (unquote(ESPN_S2_ENCODED) if ESPN_S2_ENCODED else None)
SWID = os.getenv("SWID")

BASE = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

def get_current_week():
    """Get the current week from ESPN's league settings."""
    try:
        # Use mMatchupScoreLite to get current week from status
        data = espn_get(["mMatchupScoreLite"])
        
        # Check status for current week
        status = data.get("status", {})
        current_week = status.get("currentMatchupPeriod")
        if current_week:
            print(f"Found current week from status: {current_week}")
            return current_week
        
        # Fallback to scoringPeriodId
        current_week = data.get("scoringPeriodId")
        if current_week:
            print(f"Found current week from scoringPeriodId: {current_week}")
            return current_week
            
        return 4  # Current week based on your data
    except Exception as e:
        print(f"Warning: Could not auto-detect current week: {e}")
        return 4

def espn_get(views, extra_params=None):
    """GET helper for ESPN league endpoints with one or more views."""
    params = []
    for v in views:
        params.append(("view", v))
    if extra_params:
        for k, v in extra_params.items():
            params.append((k, str(v)))

    with requests.Session() as s:
        auth_cookies = {
            "ESPN_S2": ESPN_S2, 
            "SWID": SWID,
            "espn_s2": ESPN_S2_ENCODED,
            "espnAuth": ESPN_AUTH,
        }
        s.cookies.update(auth_cookies)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://fantasy.espn.com/',
            'Origin': 'https://fantasy.espn.com',
            'x-fantasy-filter': '{"players":{}}',
            'x-fantasy-platform': 'kona-PROD-1eb11d9ef8e2d38718627f7aae409e9065630000',
            'x-fantasy-source': 'kona'
        }
        
        r = s.get(BASE, params=params, headers=headers, timeout=20)
        
        if r.status_code >= 400:
            snippet = r.text[:500].replace("\n", " ")
            raise RuntimeError(f"HTTP {r.status_code} error: {snippet}")
        return r.json()

def get_position_name(position_id):
    """Convert ESPN position ID to readable name"""
    positions = {
        0: "QB", 1: "RB", 2: "RB", 3: "WR", 4: "WR", 5: "TE", 6: "TE", 7: "FLEX", 
        8: "K", 9: "DEF", 10: "DEF", 11: "DEF", 12: "DEF", 13: "DEF", 14: "DEF", 
        15: "DEF", 16: "DEF", 17: "K", 18: "DEF", 19: "DEF", 20: "BENCH", 21: "IR",
        22: "FLEX", 23: "FLEX"  # Additional FLEX slots
    }
    return positions.get(position_id, f"POS{position_id}")

def get_nfl_team_name(team_id):
    """Convert ESPN NFL team ID to readable name"""
    teams = {
        1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
        9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
        17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
        25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 31: "BAL", 32: "HOU",
        34: "HOU"  # Alternative mapping for Houston
    }
    return teams.get(team_id, f"TEAM{team_id}")

@app.get("/")
def read_root():
    return {"message": "Fantasy Football API", "endpoints": ["/get_roster", "/get_matchup", "/test_espn", "/ai/optimize_lineup", "/ai/compare_players", "/ai/waiver_wire", "/ai/trade_analysis"]}

@app.get("/test_espn")
def test_espn():
    """Test endpoint to verify ESPN API access"""
    try:
        views = ["mTeam", "mSettings", "mRoster"]
        data = espn_get(views)
        
        teams = data.get("teams", [])
        settings = data.get("settings", {})
        
        return {
            "status": "success",
            "api_url": BASE,
            "views_requested": views,
            "response_keys": list(data.keys()),
            "teams_count": len(teams),
            "teams_found": [{"id": t.get("id"), "name": t.get("name", ""), "location": t.get("location", ""), "nickname": t.get("nickname", "")} for t in teams],
            "settings_keys": list(settings.keys()),
            "roster_data_present": "roster" in str(data),
            "full_response_sample": {k: str(v)[:100] + "..." if len(str(v)) > 100 else v for k, v in data.items()}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_url": BASE
        }

@app.get("/get_roster")
def get_roster():
    try:
        # Convert string IDs to integers for comparison
        league_id = int(LEAGUE_ID) if LEAGUE_ID else 1866946053
        team_id = int(TEAM_ID) if TEAM_ID else 8
        
        # Auto-detect current week if not specified
        current_week = WEEK if WEEK is not None else get_current_week()
        print(f"Using week: {current_week}")
        
        # Use expanded views to get projections, opponents, and more detailed data
        views = ["mTeam", "mSettings", "mRoster", "mPlayer", "mMatchupScore", "mSchedule"]
        
        # Add logging to see what's happening
        print(f"Fetching data with views: {views}")
        data = espn_get(views)
        print(f"Data keys received: {list(data.keys()) if data else 'None'}")
        
        if not data:
            raise HTTPException(status_code=500, detail="No data returned from ESPN API")
        
        teams = data.get("teams", [])
        settings = data.get("settings", {})
        schedule = data.get("schedule", [])
        
        print(f"Teams found: {len(teams)}")
        print(f"Schedule found: {len(schedule)}")
        
        if not teams:
            raise HTTPException(status_code=404, detail="No teams returned from ESPN API")
        
        # Find the specific team
        team_obj = None
        for t in teams:
            if t.get("id") == team_id:
                team_obj = t
                break
        
        if not team_obj:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found. Available teams: {[t.get('id') for t in teams]}")
        
        # Get current week matchup
        current_matchup = None
        for matchup in schedule:
            if matchup.get("matchupPeriodId") == current_week:
                # Find our team's matchup
                for team in matchup.get("teams", []):
                    if team.get("id") == team_id:
                        current_matchup = matchup
                        break
                if current_matchup:
                    break
        
        # Get roster data
        roster = team_obj.get("roster", {})
        entries = roster.get("entries", [])
        
        print(f"Roster entries found: {len(entries)}")
        
        # Build team name
        team_name = f"{team_obj.get('location','').strip()} {team_obj.get('nickname','').strip()}".strip()
        if not team_name.strip():
            team_name = f"Team {team_id}"
        
        # Process roster entries with enhanced data
        roster_rows = []
        for entry in entries:
            try:
                print(f"Processing entry: {entry}")
                
                # Check if entry has the expected structure
                if not isinstance(entry, dict):
                    print(f"Entry is not a dict: {type(entry)} - {entry}")
                    continue
                
                player_pool_entry = entry.get("playerPoolEntry")
                if not player_pool_entry:
                    print(f"No playerPoolEntry found in entry: {entry}")
                    continue
                
                player = player_pool_entry.get("player")
                if not player:
                    print(f"No player found in playerPoolEntry: {player_pool_entry}")
                    continue
                
                print(f"Processing player: {player.get('fullName', 'Unknown')}")
                
                # Get player stats and projections
                stats = player.get("stats", [])
                current_season_stats = None
                last_season_stats = None
                weekly_projection = None
                
                # Find relevant stats
                for stat in stats:
                    season_id = stat.get("seasonId")
                    scoring_period = stat.get("scoringPeriodId")
                    stat_source = stat.get("statSourceId")
                    
                    # Current season actual stats (Season=2025, Period=0, Source=0)
                    if season_id == 2025 and scoring_period == 0 and stat_source == 0:
                        current_season_stats = stat
                    
                    # Last season stats for comparison (prefer Source=0 over Source=1)
                    if season_id == 2024 and scoring_period == 0:
                        if not last_season_stats or stat_source == 0:
                            last_season_stats = stat
                    
                    # Weekly projections (current week)
                    if season_id == 2025 and scoring_period == current_week:
                        weekly_projection = stat
                
                # Get ownership data
                ownership = player.get("ownership", {})
                
                # Get player rankings for projections
                rankings = player.get("rankings", {})
                current_rankings = rankings.get("0", [])  # Current week rankings
                
                # Get opponent for this week
                opponent = "BYE"
                if current_matchup:
                    # Find the opponent team
                    for team in current_matchup.get("teams", []):
                        if team.get("id") != team_id:
                            opponent_team = team
                            opponent_abbrev = opponent_team.get("abbrev", "TBD")
                            opponent = opponent_abbrev
                            break
                
                # Calculate weekly projection
                weekly_proj = 0.0
                if weekly_projection:
                    weekly_proj = round(weekly_projection.get("appliedTotal", 0), 1)
                else:
                    # Fallback to draft rankings if available
                    draft_ranks = player.get("draftRanksByRankType", {})
                    if draft_ranks:
                        ppr_ranks = draft_ranks.get("PPR", {})
                        standard_ranks = draft_ranks.get("STANDARD", {})
                        
                        if ppr_ranks:
                            # Get the first ranking from the '0' key (current week)
                            current_ppr_ranks = ppr_ranks.get("0", [])
                            if current_ppr_ranks:
                                rank = current_ppr_ranks[0].get("rank", 100)
                                if rank <= 10:
                                    weekly_proj = 20.0
                                elif rank <= 20:
                                    weekly_proj = 15.0
                                elif rank <= 30:
                                    weekly_proj = 12.0
                                elif rank <= 50:
                                    weekly_proj = 10.0
                                elif rank <= 100:
                                    weekly_proj = 8.0
                                else:
                                    weekly_proj = 5.0
                        elif standard_ranks:
                            # Get the first ranking from the '0' key (current week)
                            current_standard_ranks = standard_ranks.get("0", [])
                            if current_standard_ranks:
                                rank = current_standard_ranks[0].get("rank", 100)
                                if rank <= 10:
                                    weekly_proj = 18.0
                                elif rank <= 20:
                                    weekly_proj = 13.0
                                elif rank <= 30:
                                    weekly_proj = 10.0
                                elif rank <= 50:
                                    weekly_proj = 8.0
                                elif rank <= 100:
                                    weekly_proj = 6.0
                                else:
                                    weekly_proj = 4.0
                
                # Calculate ownership change (this would need historical data, but for now we'll simulate)
                ownership_change = 0.0
                percent_owned = ownership.get("percentOwned", 0)
                if percent_owned > 95:
                    ownership_change = 0.5
                elif percent_owned > 90:
                    ownership_change = 1.2
                elif percent_owned > 80:
                    ownership_change = 2.1
                elif percent_owned > 70:
                    ownership_change = 3.5
                else:
                    ownership_change = 5.2
                
                roster_rows.append({
                    "lineup_slot": entry.get("lineupSlotId", "Unknown"),
                    "player": player.get("fullName", "Unknown"),
                    "position": player.get("defaultPositionId", "Unknown"),
                    "nfl_team": player.get("proTeamId", "Unknown"),
                    "injury_status": player.get("injuryStatus", ""),
                    "raw_entry": entry,  # Include raw data for debugging
                    "raw_player": player,  # Include raw player data for debugging
                    "current_season_stats": current_season_stats,
                    "last_season_stats": last_season_stats,
                    "weekly_projection": weekly_projection,
                    "weekly_proj_value": weekly_proj,
                    "opponent": opponent,
                    "ownership": ownership,
                    "ownership_change": ownership_change,
                    "rankings": current_rankings,
                    "draft_ranks": player.get("draftRanksByRankType", {}),
                    "season_outlook": player.get("seasonOutlook", ""),
                    "pro_team_id": player.get("proTeamId", 0),
                    "player_id": player.get("id", 0),
                    "active": player.get("active", True),
                    "droppable": player.get("droppable", False),
                    "eligible_slots": player.get("eligibleSlots", []),
                    "last_news_date": player.get("lastNewsDate", 0),
                    "ratings": player.get("ratings", {}),
                    "universe_id": player.get("universeId", 0)
                })
                
                print(f"Successfully processed player: {player.get('fullName', 'Unknown')}")
                
            except Exception as player_error:
                print(f"Error processing player entry: {player_error}")
                print(f"Entry that caused error: {entry}")
                import traceback
                traceback.print_exc()
                # Continue with next player instead of failing completely
                continue
        
        print(f"Successfully processed {len(roster_rows)} roster entries")
        
        # Deduplicate roster entries by player name, keeping the one with the lowest lineup slot
        # This fixes players appearing in both starting lineup and bench
        unique_players = {}
        for player_entry in roster_rows:
            player_name = player_entry["player"]
            lineup_slot = player_entry["lineup_slot"]
            
            # If we haven't seen this player, or this slot is more "starting" (lower number)
            if player_name not in unique_players or lineup_slot < unique_players[player_name]["lineup_slot"]:
                unique_players[player_name] = player_entry
        
        deduplicated_roster = list(unique_players.values())
        print(f"After deduplication: {len(deduplicated_roster)} unique players")
        
        return {
            "team_name": team_name,
            "week": current_week,
            "roster": deduplicated_roster,
            "current_matchup": current_matchup,
            "debug_info": {
                "league_id": str(league_id),
                "team_id": str(team_id),
                "season": SEASON,
                "week": current_week,
                "roster_count": len(roster_rows),
                "api_endpoint": BASE,
                "views_used": views,
                "team_object_keys": list(team_obj.keys()) if team_obj else [],
                "roster_keys": list(roster.keys()) if roster else [],
                "schedule_keys": len(schedule) if schedule else 0,
                "raw_team_data": team_obj,
                "raw_roster_data": roster,
                "available_data_keys": list(data.keys()),
                "sample_player_data": roster_rows[0] if roster_rows else None
            }
        }
    except Exception as e:
        print(f"Error in get_roster: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching roster: {str(e)}")

@app.get("/get_matchup")
def get_matchup():
    """Get current week matchup data for both teams"""
    try:
        # Convert string IDs to integers for comparison
        league_id = int(LEAGUE_ID) if LEAGUE_ID else 1866946053
        team_id = int(TEAM_ID) if TEAM_ID else 8
        
        # Auto-detect current week if not specified
        current_week = WEEK if WEEK is not None else get_current_week()
        print(f"Using week: {current_week}")
        
        # Use expanded views to get matchup data - use mMatchupScoreLite for real schedule data
        views = ["mTeam", "mSettings", "mRoster", "mMatchupScoreLite", "mPlayer"]
        
        data = espn_get(views)
        
        if not data:
            raise HTTPException(status_code=500, detail="No data returned from ESPN API")
        
        teams = data.get("teams", [])
        schedule = data.get("schedule", [])
        
        if not teams:
            raise HTTPException(status_code=404, detail="No teams returned from ESPN API")
        
        # Find current week matchup using the new schedule format
        current_matchup = None
        for matchup in schedule:
            if matchup.get("matchupPeriodId") == current_week:
                # Check if our team is in this matchup (new format uses away/home with teamId)
                home_team_id = matchup.get("home", {}).get("teamId")
                away_team_id = matchup.get("away", {}).get("teamId")
                
                if home_team_id == team_id or away_team_id == team_id:
                    current_matchup = matchup
                    break
        
        # If no matchup found for current week, try to find any matchup with our team
        if not current_matchup:
            print(f"No matchup found for week {current_week}, searching for any matchup with team {team_id}")
            for matchup in schedule:
                home_team_id = matchup.get("home", {}).get("teamId")
                away_team_id = matchup.get("away", {}).get("teamId")
                
                if home_team_id == team_id or away_team_id == team_id:
                    current_matchup = matchup
                    current_week = matchup.get("matchupPeriodId", current_week)
                    print(f"Found matchup in week {current_week}")
                    break
        
        if not current_matchup:
            # Return a mock matchup for testing
            print("No matchup found, returning mock data")
            return {
                "week": current_week,
                "my_team": {
                    "team_id": team_id,
                    "team_name": f"Team {team_id}",
                    "manager": "Unknown",
                    "record": "(0-0-0)",
                    "current_score": 0,
                    "projected_total": 0,
                    "roster": []
                },
                "opponent_team": {
                    "team_id": 999,
                    "team_name": "Mock Opponent",
                    "manager": "Unknown",
                    "record": "(0-0-0)",
                    "current_score": 0,
                    "projected_total": 0,
                    "roster": []
                },
                "my_win_probability": 50,
                "opponent_win_probability": 50,
                "matchup_id": None,
                "debug_info": {
                    "league_id": str(league_id),
                    "team_id": str(team_id),
                    "current_week": current_week,
                    "my_roster_count": 0,
                    "opponent_roster_count": 0,
                    "note": "Mock data - no real matchup found"
                }
            }
        
        # Get both teams from the matchup using new format
        home_team_id = current_matchup.get("home", {}).get("teamId")
        away_team_id = current_matchup.get("away", {}).get("teamId")
        
        # Determine which team is ours and which is opponent
        if home_team_id == team_id:
            my_team_id = home_team_id
            opponent_team_id = away_team_id
            my_score = current_matchup.get("home", {}).get("totalPoints", 0)
            opponent_score = current_matchup.get("away", {}).get("totalPoints", 0)
        else:
            my_team_id = away_team_id
            opponent_team_id = home_team_id  
            my_score = current_matchup.get("away", {}).get("totalPoints", 0)
            opponent_score = current_matchup.get("home", {}).get("totalPoints", 0)
        
        # Find team objects from the teams array
        my_team = None
        opponent_team = None
        
        for team in teams:
            if team.get("id") == my_team_id:
                my_team = team
            elif team.get("id") == opponent_team_id:
                opponent_team = team
        
        if not my_team or not opponent_team:
            raise HTTPException(status_code=404, detail="Could not find both teams in matchup")
        
        # Get rosters for both teams
        my_roster = my_team.get("roster", {}).get("entries", [])
        opponent_roster = opponent_team.get("roster", {}).get("entries", [])
        
        # Process my team roster
        my_team_data = {
            "team_id": my_team.get("id"),
            "team_name": "My Team",
            "manager": "Unknown",  # Temporarily simplified
            "record": f"({my_team.get('record', {}).get('overall', {}).get('wins', 0)}-{my_team.get('record', {}).get('overall', {}).get('losses', 0)}-{my_team.get('record', {}).get('overall', {}).get('ties', 0)})",
            "current_score": my_score,  # Real score from matchup data
            "projected_total": my_team.get("roster", {}).get("appliedStatTotal", 0),
            "roster": []
        }
        
        # Process opponent team roster
        opponent_team_data = {
            "team_id": opponent_team.get("id"),
            "team_name": "Opponent",
            "manager": "Unknown",  # Temporarily simplified
            "record": f"({opponent_team.get('record', {}).get('overall', {}).get('wins', 0)}-{opponent_team.get('record', {}).get('overall', {}).get('losses', 0)}-{opponent_team.get('record', {}).get('overall', {}).get('ties', 0)})",
            "current_score": opponent_score,  # Real score from matchup data
            "projected_total": opponent_team.get("roster", {}).get("appliedStatTotal", 0),
            "roster": []
        }
        
        # Process rosters with lineup positions
        def process_roster(roster_entries, team_name):
            processed_roster = []
            print(f"Processing roster for {team_name} with {len(roster_entries)} entries:")
            
            for entry in roster_entries:
                player_pool_entry = entry.get("playerPoolEntry", {})
                player = player_pool_entry.get("player", {})
                lineup_slot = entry.get("lineupSlotId", 20)
                
                print(f"  Player: {player.get('fullName', 'Unknown')} - Lineup Slot: {lineup_slot} - Position: {get_position_name(lineup_slot)}")
                
                # Get current week stats
                current_score = 0
                stats = player.get("stats", [])
                for stat in stats:
                    if stat.get("seasonId") == 2025 and stat.get("scoringPeriodId") == current_week:
                        current_score = stat.get("appliedTotal", 0)
                        break
                
                # Get weekly projection
                weekly_proj = 0
                for stat in stats:
                    if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == current_week:
                        weekly_proj = stat.get("appliedTotal", 0)
                        break
                
                processed_roster.append({
                    "lineup_slot": lineup_slot,
                    "position": get_position_name(lineup_slot),
                    "player_name": player.get("fullName", "Unknown"),
                    "nfl_team": get_nfl_team_name(player.get("proTeamId", 0)),
                    "injury_status": player.get("injuryStatus", "ACTIVE"),
                    "current_score": current_score,
                    "projection": weekly_proj,
                    "opponent": "TBD"
                })
            
            # Sort by lineup slot (starters first)
            processed_roster.sort(key=lambda x: x["lineup_slot"])
            return processed_roster
        
        my_team_data["roster"] = process_roster(my_roster, my_team_data["team_name"])
        opponent_team_data["roster"] = process_roster(opponent_roster, opponent_team_data["team_name"])
        
        # Calculate win probability (simplified) - include FLEX positions
        my_total_proj = sum(player["projection"] for player in my_team_data["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        opponent_total_proj = sum(player["projection"] for player in opponent_team_data["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        
        total_proj = my_total_proj + opponent_total_proj
        my_win_prob = int((my_total_proj / total_proj * 100)) if total_proj > 0 else 50
        opponent_win_prob = 100 - my_win_prob
        
        return {
            "week": current_week,
            "my_team": my_team_data,
            "opponent_team": opponent_team_data,
            "my_win_probability": my_win_prob,
            "opponent_win_probability": opponent_win_prob,
            "matchup_id": current_matchup.get("id"),
            "debug_info": {
                "league_id": str(league_id),
                "team_id": str(team_id),
                "current_week": current_week,
                "my_roster_count": len(my_roster),
                "opponent_roster_count": len(opponent_roster)
            }
        }
        
    except Exception as e:
        print(f"Error in get_matchup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching matchup: {str(e)}")

@app.post("/ai/optimize_lineup")
async def ai_optimize_lineup(request: LineupOptimizationRequest):
    """AI-powered lineup optimization"""
    try:
        # Get current roster data
        matchup_data = None
        roster_data = []
        opponent_data = []
        
        # Fetch matchup data if requested
        if request.include_opponent_context:
            try:
                current_week = get_current_week()
                data = espn_get(["mTeam", "mRoster", "mMatchupScore", "mSchedule"])
                
                teams = data.get("teams", [])
                schedule = data.get("schedule", [])
                
                # Find my team and current matchup
                team_id = int(TEAM_ID) if TEAM_ID else 8
                my_team = None
                current_matchup = None
                
                # Find my team
                for team in teams:
                    if team.get("id") == team_id:
                        my_team = team
                        break
                
                # Find current matchup
                for matchup in schedule:
                    if matchup.get("matchupPeriodId") == current_week:
                        for team in matchup.get("teams", []):
                            if team.get("id") == team_id:
                                current_matchup = matchup
                                break
                        if current_matchup:
                            break
                
                if my_team and current_matchup:
                    # Process roster data
                    my_roster = my_team.get("roster", {}).get("entries", [])
                    roster_data = process_roster(my_roster, "My Team")
                    
                    # Get opponent data
                    matchup_teams = current_matchup.get("teams", [])
                    opponent_team = None
                    for team in matchup_teams:
                        if team.get("id") != team_id:
                            opponent_team = team
                            break
                    
                    if opponent_team:
                        opp_roster = opponent_team.get("roster", {}).get("entries", [])
                        opponent_data = process_roster(opp_roster, "Opponent")
                        
            except Exception as e:
                print(f"Warning: Could not fetch matchup context: {e}")
                # Continue without opponent context
        
        # If we don't have roster data, get it from our own roster endpoint
        if not roster_data:
            try:
                # Get roster data from our own get_roster function
                roster_response = get_roster()
                if roster_response and "roster" in roster_response:
                    # Convert to format expected by AI service
                    roster_data = []
                    for player in roster_response["roster"]:
                        # Convert ESPN position ID to fantasy position
                        espn_position = player.get("position", 0)
                        fantasy_position = "BENCH"
                        if espn_position == 1:  # QB
                            fantasy_position = "QB"
                        elif espn_position == 2:  # RB
                            fantasy_position = "RB"
                        elif espn_position == 3:  # WR 
                            fantasy_position = "WR"
                        elif espn_position == 4:  # TE
                            fantasy_position = "TE"
                        elif espn_position == 5:  # K
                            fantasy_position = "K"
                        elif espn_position == 16:  # DEF
                            fantasy_position = "DEF"
                            
                        roster_data.append({
                            "player_name": player.get("player", "Unknown"),
                            "position": fantasy_position,
                            "lineup_slot": player.get("lineup_slot", 20),
                            "injury_status": player.get("injury_status", "ACTIVE"),
                            "projection": player.get("weekly_proj_value", 0),
                            "nfl_team": get_nfl_team_name(player.get("nfl_team", 0)),
                            "current_avg": player.get("current_season_stats", {}).get("appliedAverage", 0) if player.get("current_season_stats") else 0,
                            "opponent": "vs TBD"  # Default to indicate they have a game, just unknown opponent
                        })
            except Exception as e:
                print(f"Warning: Could not fetch roster data: {e}")
                pass
        
        if not roster_data:
            raise HTTPException(status_code=400, detail="Could not retrieve roster data")
        
        # Call AI service
        result = ai_service.optimize_lineup(roster_data, opponent_data if opponent_data else None)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI lineup optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI lineup optimization failed: {str(e)}")

@app.post("/ai/compare_players")
async def ai_compare_players(request: PlayerComparisonRequest):
    """AI-powered player comparison for start/sit decisions"""
    try:
        # Get current roster and matchup data
        current_week = get_current_week()
        data = espn_get(["mTeam", "mRoster", "mMatchupScore", "mSchedule"])
        
        teams = data.get("teams", [])
        schedule = data.get("schedule", [])
        
        # Find my team
        team_id = int(TEAM_ID) if TEAM_ID else 8
        my_team = None
        current_matchup = None
        
        for team in teams:
            if team.get("id") == team_id:
                my_team = team
                break
        
        # Find current matchup
        for matchup in schedule:
            if matchup.get("matchupPeriodId") == current_week:
                for team in matchup.get("teams", []):
                    if team.get("id") == team_id:
                        current_matchup = matchup
                        break
                if current_matchup:
                    break
        
        if not my_team:
            raise HTTPException(status_code=404, detail="Could not find your team")
        
        # Process roster to find the requested players
        my_roster = my_team.get("roster", {}).get("entries", [])
        roster_data = process_roster(my_roster, "My Team")
        
        # Find the two players to compare
        player1 = None
        player2 = None
        
        for player in roster_data:
            player_name = player.get("player_name", "").lower()
            if request.player1_name.lower() in player_name:
                player1 = player
            elif request.player2_name.lower() in player_name:
                player2 = player
        
        if not player1:
            raise HTTPException(status_code=404, detail=f"Could not find player: {request.player1_name}")
        if not player2:
            raise HTTPException(status_code=404, detail=f"Could not find player: {request.player2_name}")
        
        # Build matchup context
        matchup_context = {
            "week": current_week,
            "my_projection": sum(p.get("projection", 0) for p in roster_data),
            "opponent_projection": 100.0  # Default if opponent data not available
        }
        
        if current_matchup:
            matchup_teams = current_matchup.get("teams", [])
            for team in matchup_teams:
                if team.get("id") != team_id:
                    # Calculate opponent projection
                    opp_roster = team.get("roster", {}).get("entries", [])
                    if opp_roster:
                        opp_data = process_roster(opp_roster, "Opponent")
                        matchup_context["opponent_projection"] = sum(p.get("projection", 0) for p in opp_data)
                    break
        
        # Call AI service
        result = ai_service.analyze_player_matchup(player1, player2, matchup_context)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI player comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI player comparison failed: {str(e)}")

# Helper function to reuse roster processing logic
def process_roster(roster_entries, team_name):
    """Process roster entries into standardized format"""
    processed_roster = []
    current_week = get_current_week()
    
    for entry in roster_entries:
        player_pool_entry = entry.get("playerPoolEntry", {})
        player = player_pool_entry.get("player", {})
        lineup_slot = entry.get("lineupSlotId", 20)
        
        # Get current week stats
        current_score = 0
        stats = player.get("stats", [])
        for stat in stats:
            if stat.get("seasonId") == 2025 and stat.get("scoringPeriodId") == current_week:
                current_score = stat.get("appliedTotal", 0)
                break
        
        # Get weekly projection
        weekly_proj = 0
        for stat in stats:
            if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == current_week:
                weekly_proj = stat.get("appliedTotal", 0)
                break
        
        processed_roster.append({
            "lineup_slot": lineup_slot,
            "position": get_position_name(lineup_slot),
            "player_name": player.get("fullName", "Unknown"),
            "player_id": player.get("id", 0),
            "nfl_team": get_nfl_team_name(player.get("proTeamId", 0)),
            "injury_status": player.get("injuryStatus", "ACTIVE"),
            "current_score": current_score,
            "projection": weekly_proj,
            "opponent": "TBD"  # This would need game schedule data
        })
    
    return processed_roster

@app.post("/ai/waiver_wire")
async def ai_waiver_wire_analysis(request: WaiverWireRequest):
    """AI-powered waiver wire analysis and recommendations"""
    try:
        # Get current roster data
        current_week = get_current_week()
        data = espn_get(["mTeam", "mRoster", "mPlayer", "mMatchupScore"])
        
        teams = data.get("teams", [])
        
        # Find my team
        team_id = int(TEAM_ID) if TEAM_ID else 8
        my_team = None
        
        for team in teams:
            if team.get("id") == team_id:
                my_team = team
                break
        
        if not my_team:
            raise HTTPException(status_code=404, detail="Could not find your team")
        
        # Process current roster
        my_roster = my_team.get("roster", {}).get("entries", [])
        roster_data = process_roster(my_roster, "My Team")
        
        # Get all league rosters to filter out owned players
        league_rosters = []
        for team in teams:
            team_roster = team.get("roster", {}).get("entries", [])
            processed_roster = process_roster(team_roster, f"Team {team.get('id')}")
            league_rosters.append({
                "team_id": team.get("id"),
                "roster": processed_roster
            })
        
        # Get available players from ESPN player pool, filtering out owned players
        available_players = get_available_players(request.max_players_per_position, league_rosters)
        
        # Build league context
        league_context = {
            "scoring_format": "PPR",  # You could detect this from league settings
            "roster_size": 16,
            "playoff_teams": 6,
            "current_week": current_week,
            "trade_deadline": 12
        } if request.include_league_context else None
        
        # Call AI service
        result = ai_service.analyze_waiver_wire_targets(roster_data, available_players, league_context)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI waiver wire analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI waiver wire analysis failed: {str(e)}")

@app.post("/ai/trade_analysis")
async def ai_trade_analysis(request: TradeAnalysisRequest):
    """AI-powered trade analysis and recommendations"""
    try:
        # Get current roster and league data
        current_week = get_current_week()
        data = espn_get(["mTeam", "mRoster", "mPlayer", "mMatchupScore"])
        
        teams = data.get("teams", [])
        
        # Find my team
        team_id = int(TEAM_ID) if TEAM_ID else 8
        my_team = None
        
        for team in teams:
            if team.get("id") == team_id:
                my_team = team
                break
        
        if not my_team:
            raise HTTPException(status_code=404, detail="Could not find your team")
        
        # Process my roster
        my_roster = my_team.get("roster", {}).get("entries", [])
        roster_data = process_roster(my_roster, "My Team")
        
        # Get other teams' data for trade analysis
        league_rosters = []
        if request.include_league_rosters:
            for team in teams:
                if team.get("id") != team_id:
                    team_roster = team.get("roster", {}).get("entries", [])
                    processed_roster = process_roster(team_roster, f"Team {team.get('id')}")
                    
                    # Simplified team analysis
                    team_analysis = analyze_team_needs(processed_roster)
                    
                    # Build team name from location and nickname
                    team_name = f"{team.get('location','').strip()} {team.get('nickname','').strip()}".strip()
                    if not team_name.strip():
                        team_name = f"Team {team.get('id')}"
                    
                    # Get detailed team record
                    record_data = team.get('record', {}).get('overall', {})
                    wins = record_data.get('wins', 0)
                    losses = record_data.get('losses', 0)
                    ties = record_data.get('ties', 0)
                    
                    # Calculate team total projection for strength assessment
                    starters = [p for p in processed_roster if p['lineup_slot'] < 20 or p['lineup_slot'] in [22, 23]]
                    total_projection = sum(p.get('projection', 0) for p in starters)
                    
                    league_rosters.append({
                        "team_id": team.get("id"),
                        "team_name": team_name,
                        "record": f"({wins}-{losses}-{ties})",
                        "total_projection": total_projection,
                        "roster": processed_roster,
                        "starters": starters,
                        "bench": [p for p in processed_roster if p['lineup_slot'] >= 20 and p['lineup_slot'] not in [22, 23]],
                        "strengths": team_analysis.get("strengths", []),
                        "needs": team_analysis.get("needs", [])
                    })
        
        # Build league context
        league_context = {
            "current_week": current_week,
            "trade_deadline": 12,
            "playoff_format": "Top 6 teams",
            "scoring_format": "PPR"
        }
        
        # Call AI service
        result = ai_service.analyze_trade_opportunities(roster_data, league_rosters, league_context)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in AI trade analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI trade analysis failed: {str(e)}")

def get_available_players(max_per_position: int = 10, league_rosters: List = None) -> List[Dict]:
    """Get available players from ESPN player pool, filtering out owned players"""
    try:
        # Get player pool data from ESPN
        current_week = get_current_week()
        
        # Use different approaches to get player pool data
        data = None
        try:
            # First try: Use mPlayer view for player pool
            data = espn_get(["mPlayer"], extra_params={
                "scoringPeriodId": current_week
            })
        except Exception as e1:
            print(f"mPlayer view failed: {e1}")
            try:
                # Second try: Use mTeam view with additional player data
                data = espn_get(["mTeam", "mPlayer"])
            except Exception as e2:
                print(f"mTeam+mPlayer view failed: {e2}")
                # Will use fallback mock data
        
        # Get all owned players from league rosters
        owned_player_ids = set()
        if league_rosters:
            for roster_entry in league_rosters:
                for player in roster_entry.get("roster", []):
                    player_id = player.get("player_id", 0)
                    if player_id:
                        owned_player_ids.add(player_id)
        
        available_players = []
        
        # Check if we got valid player pool data
        if not data or not data.get("players"):
            print("No player pool data available from ESPN, using filtered mock data")
            return get_mock_waiver_players_filtered(max_per_position, league_rosters)
        
        players_pool = data.get("players", [])
        print(f"Found {len(players_pool)} players in ESPN player pool")
        
        # Track players per position to limit results
        position_counts = {}
        
        for player_entry in players_pool:
            player = player_entry.get("player", {})
            player_id = player.get("id", 0)
            
            # Skip if player is owned
            if player_id in owned_player_ids:
                continue
            
            # Get player details
            full_name = player.get("fullName", "Unknown")
            default_position = player.get("defaultPositionId", 0)
            
            # Convert ESPN position to fantasy position
            position_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DEF"}
            position = position_map.get(default_position, "UNKNOWN")
            
            # Skip unknown positions
            if position == "UNKNOWN":
                continue
            
            # Limit players per position
            if position_counts.get(position, 0) >= max_per_position:
                continue
            
            # Get ownership data
            ownership = player.get("ownership", {})
            percent_owned = ownership.get("percentOwned", 0)
            
            # Skip players with very high ownership (likely owned but not in our data)
            if percent_owned > 95:
                continue
            
            # Get projections
            stats = player.get("stats", [])
            weekly_proj = 0
            
            for stat in stats:
                season_id = stat.get("seasonId")
                scoring_period = stat.get("scoringPeriodId")
                stat_source = stat.get("statSourceId")
                
                # Weekly projections (current week, source 1 = projections)
                if season_id == 2025 and scoring_period == current_week and stat_source == 1:
                    weekly_proj = stat.get("appliedTotal", 0)
                    break
            
            # Skip players with very low projections
            if weekly_proj < 3:
                continue
            
            nfl_team = get_nfl_team_name(player.get("proTeamId", 0))
            
            available_players.append({
                "name": full_name,
                "position": position,
                "nfl_team": nfl_team,
                "ownership": percent_owned,
                "projection": weekly_proj,
                "player_id": player_id,
                "injury_status": player.get("injuryStatus", "ACTIVE")
            })
            
            position_counts[position] = position_counts.get(position, 0) + 1
        
        # Sort by projection within each position
        available_players.sort(key=lambda x: (x["position"], -x["projection"]))
        
        print(f"Found {len(available_players)} available players")
        return available_players
        
    except Exception as e:
        print(f"Error fetching available players from ESPN: {e}")
        # Fall back to filtered mock data
        return get_mock_waiver_players_filtered(max_per_position, league_rosters)

def get_mock_waiver_players_filtered(max_per_position: int = 10, league_rosters: List = None) -> List[Dict]:
    """Generate filtered mock waiver wire players (fallback when ESPN API fails)"""
    # Get owned player names to filter out
    owned_players = set()
    if league_rosters:
        for roster_entry in league_rosters:
            for player in roster_entry.get("roster", []):
                player_name = player.get("player", "").lower()
                if player_name:
                    owned_players.add(player_name)
    
    # Mock players with more realistic availability
    mock_players = [
        # RBs - Only include players likely to be available
        {"name": "Tyler Allgeier", "position": "RB", "nfl_team": "ATL", "ownership": 45.2, "projection": 8.5},
        {"name": "Roschon Johnson", "position": "RB", "nfl_team": "CHI", "ownership": 15.8, "projection": 6.2},
        {"name": "Justice Hill", "position": "RB", "nfl_team": "BAL", "ownership": 25.4, "projection": 7.1},
        {"name": "Cam Akers", "position": "RB", "nfl_team": "HOU", "ownership": 35.1, "projection": 9.2},
        {"name": "Ty Chandler", "position": "RB", "nfl_team": "MIN", "ownership": 18.9, "projection": 6.8},
        
        {"name": "Dontayvion Wicks", "position": "WR", "nfl_team": "GB", "ownership": 22.3, "projection": 9.1},
        {"name": "Jahan Dotson", "position": "WR", "nfl_team": "PHI", "ownership": 28.7, "projection": 8.4},
        {"name": "Demario Douglas", "position": "WR", "nfl_team": "NE", "ownership": 12.5, "projection": 7.2},
        {"name": "Noah Brown", "position": "WR", "nfl_team": "HOU", "ownership": 8.9, "projection": 6.5},
        {"name": "Tre Tucker", "position": "WR", "nfl_team": "LV", "ownership": 5.2, "projection": 5.8},
        
        # TEs - Streaming options
        {"name": "Juwan Johnson", "position": "TE", "nfl_team": "NO", "ownership": 15.2, "projection": 7.8},
        {"name": "Logan Thomas", "position": "TE", "nfl_team": "SF", "ownership": 12.1, "projection": 6.9},
        {"name": "Mike Gesicki", "position": "TE", "nfl_team": "CIN", "ownership": 18.4, "projection": 7.5},
        
        # QBs - Backup/streaming options only
        {"name": "Gardner Minshew", "position": "QB", "nfl_team": "LV", "ownership": 8.5, "projection": 16.2},
        {"name": "Jameis Winston", "position": "QB", "nfl_team": "CLE", "ownership": 12.8, "projection": 15.8},
        
        # DEF - Streaming defenses only (avoid commonly owned ones like Broncos)
        {"name": "Cardinals", "position": "DEF", "nfl_team": "ARI", "ownership": 25.1, "projection": 8.2},
        {"name": "Titans", "position": "DEF", "nfl_team": "TEN", "ownership": 15.8, "projection": 7.5},
        {"name": "Panthers", "position": "DEF", "nfl_team": "CAR", "ownership": 12.4, "projection": 6.8},
        
        # K - Streaming options
        {"name": "Cairo Santos", "position": "K", "nfl_team": "CHI", "ownership": 35.2, "projection": 8.1},
        {"name": "Matt Gay", "position": "K", "nfl_team": "IND", "ownership": 28.9, "projection": 7.8}
    ]
    
    # Filter out owned players
    filtered_players = []
    for player in mock_players:
        player_name = player["name"].lower()
        if player_name not in owned_players:
            filtered_players.append(player)
    
    return filtered_players[:max_per_position * 7]  # Limit total players

def analyze_team_needs(roster_data: List[Dict]) -> Dict:
    """Enhanced team analysis to identify strengths, needs, and tradeable assets"""
    # Group by position, only counting fantasy-relevant positions
    positions = {}
    for player in roster_data:
        pos_name = player.get("position", "UNKNOWN")
        # Convert position names to standard format
        if pos_name in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            if pos_name not in positions:
                positions[pos_name] = []
            positions[pos_name].append(player)
    
    strengths = []
    needs = []
    tradeable_assets = []
    
    # Enhanced analysis logic with better thresholds
    for pos, players in positions.items():
        if not players:
            needs.append(f"Missing {pos}")
            continue
            
        # Sort players by projection
        sorted_players = sorted(players, key=lambda x: x.get("projection", 0), reverse=True)
        best_player = sorted_players[0]
        
        if pos in ["QB", "TE", "K", "DEF"]:
            # Single position analysis
            if best_player.get("projection", 0) > 15:
                strengths.append(f"Elite {pos} - {best_player.get('player_name', 'Unknown')}")
            elif best_player.get("projection", 0) > 10:
                strengths.append(f"Solid {pos}")
            else:
                needs.append(f"{pos} upgrade needed")
                
            # Check for tradeable backup
            if len(sorted_players) > 1 and sorted_players[1].get("projection", 0) > 8:
                tradeable_assets.append(f"Backup {pos} - {sorted_players[1].get('player_name', 'Unknown')}")
                
        elif pos in ["RB", "WR"]:
            # Multi-position analysis
            elite_players = [p for p in sorted_players if p.get("projection", 0) > 15]
            solid_players = [p for p in sorted_players if p.get("projection", 0) > 10]
            
            if len(elite_players) >= 2:
                strengths.append(f"Elite {pos} depth")
                # Third elite player could be tradeable
                if len(elite_players) >= 3:
                    tradeable_assets.append(f"Surplus elite {pos} - {elite_players[2].get('player_name', 'Unknown')}")
            elif len(solid_players) >= 3:
                strengths.append(f"Good {pos} depth")
                # Could trade depth for upgrade
                tradeable_assets.append(f"Depth {pos} - {solid_players[-1].get('player_name', 'Unknown')}")
            elif len(solid_players) >= 2:
                strengths.append(f"Adequate {pos}")
            elif len(solid_players) == 1:
                needs.append(f"{pos} depth needed")
            else:
                needs.append(f"{pos} major upgrade needed")
    
    return {
        "strengths": strengths, 
        "needs": needs, 
        "tradeable_assets": tradeable_assets,
        "position_breakdown": positions
    }

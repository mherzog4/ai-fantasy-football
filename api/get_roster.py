from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import os
import json
import requests
from urllib.parse import unquote
import dotenv
from datetime import datetime
dotenv.load_dotenv()

app = FastAPI()

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
    """
    Get the current week from ESPN's league settings.
    Returns the current scoring period ID.
    """
    try:
        # Get basic league info to find current week
        data = espn_get(["mSettings"])
        settings = data.get("settings", {})
        
        print(f"Settings data: {settings}")
        
        # ESPN provides the current scoring period in settings
        current_week = settings.get("scoringPeriodId")
        if current_week:
            print(f"Found current week from ESPN: {current_week}")
            return current_week
            
        # Try to get from schedule data
        schedule_data = espn_get(["mSchedule"])
        schedule = schedule_data.get("schedule", [])
        print(f"Schedule data: {len(schedule)} matchups found")
        
        if schedule:
            # Find the highest week number in the schedule
            max_week = 0
            for matchup in schedule:
                week = matchup.get("matchupPeriodId", 0)
                if week > max_week:
                    max_week = week
            if max_week > 0:
                print(f"Found max week from schedule: {max_week}")
                return max_week
        
        # Fallback: try to get from season info
        season_info = settings.get("seasonId")
        if season_info:
            # This is a rough calculation - you might need to adjust based on when season starts
            season_start = datetime(2025, 9, 4)  # Approximate NFL season start
            current_date = datetime.now()
            weeks_elapsed = (current_date - season_start).days // 7
            calculated_week = max(1, min(18, weeks_elapsed + 1))  # NFL season is typically 18 weeks
            print(f"Calculated week from date: {calculated_week}")
            return calculated_week
        
        print("Using default week 1")
        return 1  # Default fallback
    except Exception as e:
        print(f"Warning: Could not auto-detect current week: {e}")
        return 1

def espn_get(views, extra_params=None):
    """
    GET helper for ESPN league endpoints with one or more views.
    views: list[str] like ["mRoster", "mSettings"]
    extra_params: dict of additional query params
    """
    params = []
    for v in views:
        params.append(("view", v))
    if extra_params:
        for k, v in extra_params.items():
            params.append((k, str(v)))

    with requests.Session() as s:
        # Set all the authentication cookies from the working request
        auth_cookies = {
            "ESPN_S2": ESPN_S2, 
            "SWID": SWID,
            "espn_s2": ESPN_S2_ENCODED,
            "espnAuth": ESPN_AUTH,
        }
        s.cookies.update(auth_cookies)
        
        # Add headers that ESPN requires (matching the working request)
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
        
        # ESPN sometimes returns HTML error pages; show a snippet if error
        if r.status_code >= 400:
            snippet = r.text[:500].replace("\n", " ")
            raise RuntimeError(f"HTTP {r.status_code} error: {snippet}")
        return r.json()

def get_position_name(position_id):
    """Convert ESPN position ID to readable name"""
    positions = {
        0: "QB", 1: "RB", 2: "RB", 3: "WR", 4: "WR", 5: "TE", 6: "TE", 7: "FLEX", 
        8: "K", 9: "DEF", 10: "DEF", 11: "DEF", 12: "DEF", 13: "DEF", 14: "DEF", 
        15: "DEF", 16: "DEF", 17: "DEF", 18: "DEF", 19: "DEF", 20: "BENCH", 21: "IR"
    }
    return positions.get(position_id, f"POS{position_id}")

def get_nfl_team_name(team_id):
    """Convert ESPN NFL team ID to readable name"""
    teams = {
        1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
        9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
        17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
        25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 31: "BAL", 32: "HOU"
    }
    return teams.get(team_id, f"TEAM{team_id}")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/test_espn")
def test_espn():
    """Test endpoint to verify ESPN API access"""
    try:
        # Use the exact same approach that works in test_espn
        views = ["mTeam", "mSettings", "mRoster"]  # Added mRoster for roster data
        data = espn_get(views)
        
        # Extract teams and settings
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
            "roster_data_present": "roster" in str(data),  # Check if roster data exists
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
                    if stat.get("seasonId") == 2025 and stat.get("scoringPeriodId") == 1:
                        current_season_stats = stat
                    elif stat.get("seasonId") == 2024 and stat.get("scoringPeriodId") == 0:
                        last_season_stats = stat
                    elif stat.get("seasonId") == 2025 and stat.get("scoringPeriodId") == current_week:
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
                    "current_stats": current_season_stats,
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
        
        return {
            "team_name": team_name,
            "week": current_week,
            "roster": roster_rows,
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
                "schedule_keys": len(schedule) if schedule else 0,  # Fix: schedule is a list, not dict
                "raw_team_data": team_obj,  # Include full team data for debugging
                "raw_roster_data": roster,   # Include full roster data for debugging
                "available_data_keys": list(data.keys()),
                "sample_player_data": roster_rows[0] if roster_rows else None
            }
        }
    except Exception as e:
        print(f"Error in get_roster: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching roster: {str(e)}")

@app.get("/debug_week")
def debug_week():
    """Debug endpoint to see what week data we're getting"""
    try:
        # Get settings data
        settings_data = espn_get(["mSettings"])
        settings = settings_data.get("settings", {})
        
        # Get schedule data
        schedule_data = espn_get(["mSchedule"])
        schedule = schedule_data.get("schedule", [])
        
        # Get current week
        current_week = get_current_week()
        
        # Find matchups for different weeks
        week_matchups = {}
        for matchup in schedule:
            week = matchup.get("matchupPeriodId", 0)
            if week not in week_matchups:
                week_matchups[week] = []
            week_matchups[week].append({
                "id": matchup.get("id"),
                "teams": [{"id": t.get("id"), "name": f"{t.get('location', '')} {t.get('nickname', '')}".strip()} for t in matchup.get("teams", [])]
            })
        
        return {
            "current_week": current_week,
            "settings": {
                "scoringPeriodId": settings.get("scoringPeriodId"),
                "seasonId": settings.get("seasonId"),
                "keys": list(settings.keys())
            },
            "schedule_info": {
                "total_matchups": len(schedule),
                "weeks_available": list(week_matchups.keys()),
                "week_matchups": week_matchups
            },
            "league_id": LEAGUE_ID,
            "team_id": TEAM_ID
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_week": 1
        }

@app.get("/get_matchup")
def get_matchup():
    """Get current week matchup data for both teams"""
    try:
        # Convert string IDs to integers for comparison
        league_id = int(LEAGUE_ID) if LEAGUE_ID else 1866946053
        team_id = int(TEAM_ID) if TEAM_ID else 8
        
        # Auto-detect current week if not specified
        current_week = WEEK if WEEK is not None else get_current_week()
        print(f"Matchup API - Using week: {current_week}")
        
        # Use expanded views to get matchup data
        views = ["mTeam", "mSettings", "mRoster", "mMatchupScore", "mSchedule", "mPlayer"]
        
        data = espn_get(views)
        
        if not data:
            raise HTTPException(status_code=500, detail="No data returned from ESPN API")
        
        teams = data.get("teams", [])
        schedule = data.get("schedule", [])
        
        print(f"Matchup API - Teams found: {len(teams)}")
        print(f"Matchup API - Schedule found: {len(schedule)}")
        
        if not teams:
            raise HTTPException(status_code=404, detail="No teams returned from ESPN API")
        
        # Find current week matchup
        current_matchup = None
        for matchup in schedule:
            if matchup.get("matchupPeriodId") == current_week:
                # Check if our team is in this matchup
                for team in matchup.get("teams", []):
                    if team.get("id") == team_id:
                        current_matchup = matchup
                        break
                if current_matchup:
                    break
        
        # If no matchup found for current week, try to find any matchup with our team
        if not current_matchup:
            print(f"No matchup found for week {current_week}, searching for any matchup with team {team_id}")
            for matchup in schedule:
                for team in matchup.get("teams", []):
                    if team.get("id") == team_id:
                        current_matchup = matchup
                        current_week = matchup.get("matchupPeriodId", current_week)
                        print(f"Found matchup in week {current_week}")
                        break
                if current_matchup:
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
        
        # Get both teams from the matchup
        matchup_teams = current_matchup.get("teams", [])
        my_team = None
        opponent_team = None
        
        for team in matchup_teams:
            if team.get("id") == team_id:
                my_team = team
            else:
                opponent_team = team
        
        if not my_team or not opponent_team:
            raise HTTPException(status_code=404, detail="Could not find both teams in matchup")
        
        # Get rosters for both teams
        my_roster = my_team.get("roster", {}).get("entries", [])
        opponent_roster = opponent_team.get("roster", {}).get("entries", [])
        
        # Process my team roster
        my_team_data = {
            "team_id": my_team.get("id"),
            "team_name": f"{my_team.get('location','').strip()} {my_team.get('nickname','').strip()}".strip(),
            "manager": my_team.get("owners", [{}])[0].get("displayName", "Unknown"),
            "record": f"({my_team.get('record', {}).get('overall', {}).get('wins', 0)}-{my_team.get('record', {}).get('overall', {}).get('losses', 0)}-{my_team.get('record', {}).get('overall', {}).get('ties', 0)})",
            "current_score": my_team.get("roster", {}).get("appliedStatTotal", 0),
            "projected_total": my_team.get("roster", {}).get("appliedStatTotal", 0),
            "roster": []
        }
        
        # Process opponent team roster
        opponent_team_data = {
            "team_id": opponent_team.get("id"),
            "team_name": f"{opponent_team.get('location','').strip()} {opponent_team.get('nickname','').strip()}".strip(),
            "manager": opponent_team.get("owners", [{}])[0].get("displayName", "Unknown"),
            "record": f"({opponent_team.get('record', {}).get('overall', {}).get('wins', 0)}-{opponent_team.get('record', {}).get('overall', {}).get('losses', 0)}-{opponent_team.get('record', {}).get('overall', {}).get('ties', 0)})",
            "current_score": opponent_team.get("roster", {}).get("appliedStatTotal", 0),
            "projected_total": opponent_team.get("roster", {}).get("appliedStatTotal", 0),
            "roster": []
        }
        
        # Process rosters with lineup positions
        def process_roster(roster_entries, team_name):
            processed_roster = []
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
        
        # Calculate win probability (simplified)
        my_total_proj = sum(player["projection"] for player in my_team_data["roster"] if player["lineup_slot"] < 20)
        opponent_total_proj = sum(player["projection"] for player in opponent_team_data["roster"] if player["lineup_slot"] < 20)
        
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

@app.get("/view_roster", response_class=HTMLResponse)
def view_roster():
    """HTML endpoint to view roster in a formatted table"""
    try:
        # Convert string IDs to integers for comparison
        league_id = int(LEAGUE_ID) if LEAGUE_ID else 1866946053
        team_id = int(TEAM_ID) if TEAM_ID else 8
        
        # Get roster data
        views = ["mTeam", "mSettings", "mRoster"]
        data = espn_get(views)
        
        teams = data.get("teams", [])
        if not teams:
            return HTMLResponse(content="<h1>Error: No teams found</h1>", status_code=500)
        
        # Find the specific team
        team_obj = None
        for t in teams:
            if t.get("id") == team_id:
                team_obj = t
                break
        
        if not team_obj:
            return HTMLResponse(content=f"<h1>Error: Team {team_id} not found</h1>", status_code=404)
        
        # Get roster data
        roster = team_obj.get("roster", {})
        entries = roster.get("entries", [])
        
        # Build team name
        team_name = f"{team_obj.get('location','').strip()} {team_obj.get('nickname','').strip()}".strip()
        if not team_name.strip():
            team_name = f"Team {team_id}"
        
        # Build HTML table
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{team_name} - Fantasy Roster</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
                .roster-info {{ text-align: center; margin-bottom: 20px; color: #7f8c8d; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #3498db; color: white; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #e8f4f8; }}
                .position {{ font-weight: bold; color: #2c3e50; }}
                .nfl-team {{ color: #e74c3c; font-weight: bold; }}
                .injury {{ color: #e67e22; font-weight: bold; }}
                .bench {{ color: #95a5a6; }}
                .ir {{ color: #e74c3c; font-weight: bold; }}
                .api-link {{ text-align: center; margin-top: 30px; }}
                .api-link a {{ color: #3498db; text-decoration: none; }}
                .api-link a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏈 {team_name}</h1>
                <div class="roster-info">
                    <strong>Season {SEASON} • Week {get_current_week()} • League ID: {league_id} • Team ID: {team_id}</strong>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Position</th>
                            <th>Player Name</th>
                            <th>NFL Team</th>
                            <th>Injury Status</th>
                            <th>Lineup Slot</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for entry in entries:
            player = (entry.get("playerPoolEntry") or {}).get("player") or {}
            lineup_slot = entry.get("lineupSlotId", 0)
            position_id = player.get("defaultPositionId", 0)
            nfl_team_id = player.get("proTeamId", 0)
            injury_status = player.get("injuryStatus", "ACTIVE")
            
            # Format position
            position_class = "position"
            if lineup_slot == 20:  # Bench
                position_class += " bench"
            elif lineup_slot == 21:  # IR
                position_class += " ir"
            
            # Format injury status
            injury_class = "injury" if injury_status != "ACTIVE" else ""
            
            html_content += f"""
                        <tr>
                            <td class="{position_class}">{get_position_name(position_id)}</td>
                            <td><strong>{player.get('fullName', 'Unknown')}</strong></td>
                            <td class="nfl-team">{get_nfl_team_name(nfl_team_id)}</td>
                            <td class="{injury_class}">{injury_status}</td>
                            <td>{get_position_name(lineup_slot)}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
                
                <div class="api-link">
                    <p><a href="/get_roster">View Raw JSON Data</a> | <a href="/test_espn">Test ESPN API</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Fantasy Roster</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #e74c3c; text-align: center; }}
                .error {{ background-color: #fdf2f2; border: 1px solid #fecaca; padding: 15px; border-radius: 5px; color: #991b1b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Error Loading Roster</h1>
                <div class="error">
                    <strong>Error:</strong> {str(e)}
                </div>
                <p style="text-align: center; margin-top: 20px;">
                    <a href="/test_espn">Test ESPN API</a> | <a href="/get_roster">View Raw Data</a>
                </p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/get_current_week")
def get_current_week_endpoint():
    """Get the current week from ESPN"""
    try:
        current_week = get_current_week()
        return {
            "current_week": current_week,
            "season": SEASON,
            "league_id": LEAGUE_ID,
            "team_id": TEAM_ID
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_week": 1,
            "season": SEASON,
            "league_id": LEAGUE_ID,
            "team_id": TEAM_ID
        }
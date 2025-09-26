from fastapi import FastAPI, HTTPException
import os
import json
import requests
from urllib.parse import unquote
import dotenv
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
    """Get the current week from ESPN's league settings."""
    try:
        data = espn_get(["mSettings"])
        settings = data.get("settings", {})
        current_week = settings.get("scoringPeriodId")
        if current_week:
            return current_week
        return 1  # Default fallback
    except Exception as e:
        print(f"Warning: Could not auto-detect current week: {e}")
        return 1

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
        
        # Use expanded views to get matchup data
        views = ["mTeam", "mSettings", "mRoster", "mMatchupScore", "mSchedule", "mPlayer"]
        
        data = espn_get(views)
        
        if not data:
            raise HTTPException(status_code=500, detail="No data returned from ESPN API")
        
        teams = data.get("teams", [])
        schedule = data.get("schedule", [])
        
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
        
        if not current_matchup:
            raise HTTPException(status_code=404, detail=f"No matchup found for week {current_week}")
        
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
            "projected_total": my_team.get("roster", {}).get("appliedStatTotal", 0),  # This would need projection data
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
                    "opponent": "TBD"  # This would need game schedule data
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

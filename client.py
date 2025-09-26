import streamlit as st
import requests as req
import pandas as pd
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import rate limiter
try:
    from rate_limiter import display_usage_dashboard, show_feature_costs, rate_limiter
    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False
    def display_usage_dashboard():
        pass
    def show_feature_costs():
        pass

# Configuration check for Streamlit Cloud deployment
def check_environment_setup():
    """Check if required environment variables are set up"""
    openai_key = os.getenv("OPENAI_API_KEY")
    espn_s2 = os.getenv("ESPN_S2")
    league_id = os.getenv("LEAGUE_ID")
    
    if not openai_key:
        st.error("⚠️ OpenAI API key not configured. Please set OPENAI_API_KEY in your Streamlit secrets.")
        return False
    
    if not espn_s2 or not league_id:
        st.warning("⚠️ ESPN credentials not fully configured. Some features may not work.")
        st.info("To use ESPN features, please configure: ESPN_S2, SWID, ESPN_AUTH, LEAGUE_ID, TEAM_ID")
        return False
    
    return True

# Set OpenAI API key with error handling
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = None
        # Will show error later in the UI
        print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
except Exception as e:
    client = None
    print(f"Error initializing OpenAI client: {e}")

# API Configuration
API_BASE_URL = "https://ai-fantasy-football.onrender.com"

@st.cache_data(ttl=30)  # Cache for 30 seconds only
def get_roster():
    """Fetch roster data from FastAPI server"""
    try:
        response = req.get(f"{API_BASE_URL}/get_roster", timeout=10)
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to connect to API server: {e}")
        return None

def get_matchup():
    """Fetch matchup data from FastAPI server"""
    try:
        response = req.get(f"{API_BASE_URL}/get_matchup")
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to connect to matchup API: {e}")
        return None

def get_ai_lineup_optimization():
    """Fetch AI lineup optimization from FastAPI server"""
    try:
        response = req.post(f"{API_BASE_URL}/ai/optimize_lineup", json={"include_opponent_context": True})
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to get AI lineup optimization: {e}")
        return None

def get_ai_player_comparison(player1_name, player2_name):
    """Fetch AI player comparison from FastAPI server"""
    try:
        response = req.post(f"{API_BASE_URL}/ai/compare_players", json={
            "player1_name": player1_name,
            "player2_name": player2_name
        })
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to get AI player comparison: {e}")
        return None

def get_ai_waiver_wire_analysis():
    """Fetch AI waiver wire analysis from FastAPI server"""
    try:
        response = req.post(f"{API_BASE_URL}/ai/waiver_wire", json={
            "include_league_context": True,
            "max_players_per_position": 10
        })
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to get AI waiver wire analysis: {e}")
        return None

def get_ai_trade_analysis():
    """Fetch AI trade analysis from FastAPI server"""
    try:
        response = req.post(f"{API_BASE_URL}/ai/trade_analysis", json={
            "include_league_rosters": True,
            "focus_positions": None
        })
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        st.error(f"Failed to get AI trade analysis: {e}")
        return None

# Set page config
st.set_page_config(
    page_title="Fantasy Football Dashboard",
    page_icon="🏈",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>

.matchup-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin: 30px auto;
    max-width: 1000px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    overflow: hidden;
}

.espn-matchup-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 40px 30px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 50px;
}

.espn-team-left {
    text-align: left;
}

.espn-team-right {
    text-align: right;
}

.espn-team-logo {
    width: 80px;
    height: 80px;
    background: rgba(255, 255, 255, 0.2);
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 28px;
    color: white;
    margin-bottom: 15px;
}

.espn-team-info h2 {
    margin: 0;
    font-size: 28px;
    font-weight: bold;
    color: white;
    margin-bottom: 8px;
}

.espn-team-info .record {
    font-size: 18px;
    color: rgba(255, 255, 255, 0.9);
    margin: 5px 0;
    font-weight: 500;
}

.espn-team-info .manager {
    font-size: 16px;
    color: rgba(255, 255, 255, 0.8);
}

.espn-projected-total {
    text-align: center;
    color: white;
}

.espn-score-large {
    font-size: 56px;
    font-weight: bold;
    line-height: 1;
    margin-bottom: 8px;
}

.espn-vs {
    font-size: 24px;
    font-weight: bold;
    margin: 0 20px;
    opacity: 0.8;
}

.espn-projected-label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.espn-stats-breakdown {
    background: #ffffff;
    padding: 15px 20px;
    border-bottom: 1px solid #d0d0d0;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    font-size: 12px;
    color: #666;
}

.espn-stats-left {
    text-align: left;
}

.espn-stats-right {
    text-align: right;
}

.espn-stats-center {
    text-align: center;
    padding: 0 20px;
    border-left: 1px solid #e0e0e0;
    border-right: 1px solid #e0e0e0;
}

.espn-roster-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}

.espn-roster-table th {
    background: #2d3748;
    padding: 12px 16px;
    font-size: 11px;
    font-weight: 600;
    color: #ffffff;
    border-bottom: 1px solid #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.espn-roster-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
    background: white;
}

.espn-roster-table tr:nth-child(even) {
    background-color: #f8fafc;
}

.espn-roster-table tr:hover {
    background-color: #edf2f7;
}

.espn-position-badge {
    display: inline-block;
    background: #e2e8f0;
    color: #2d3748;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    min-width: 32px;
    text-align: center;
}

.espn-player-name {
    font-weight: 600;
    color: #2d3748;
    font-size: 15px;
}

.espn-team-abbr {
    color: #718096;
    font-size: 13px;
    margin-left: 6px;
}

.espn-projection-cell {
    font-weight: 600;
    color: #2d3748;
    font-size: 15px;
}

.espn-advantage {
    color: #38a169;
    font-weight: bold;
    font-size: 16px;
}

.espn-bench-section {
    background: #f9f9f9;
    border-top: 1px solid #d0d0d0;
}

.espn-bench-header {
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
    color: #666;
    background: #f1f1f1;
    border-bottom: 1px solid #d0d0d0;
}

.team-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

.team-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.team-logo {
    width: 50px;
    height: 50px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #1e3c72;
}

.team-details h3 {
    margin: 0;
    font-size: 24px;
}

.team-details p {
    margin: 5px 0;
    opacity: 0.9;
}

.team-stats {
    text-align: right;
}

.team-stats .score {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 5px;
}

.team-stats .projection {
    font-size: 16px;
    opacity: 0.8;
}

.win-probability {
    background: rgba(255, 255, 255, 0.2);
    padding: 10px 20px;
    border-radius: 20px;
    text-align: center;
    margin: 20px 0;
}

.win-prob-bar {
    display: flex;
    height: 30px;
    border-radius: 15px;
    overflow: hidden;
    margin: 10px 0;
}

.win-prob-my {
    background: linear-gradient(90deg, #4CAF50, #45a049);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
}

.win-prob-opponent {
    background: linear-gradient(90deg, #f44336, #d32f2f);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
}

.matchup-roster {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 20px;
    margin-top: 20px;
}

.position-label {
    text-align: center;
    font-weight: bold;
    padding: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
}

.player-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 20px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.player-info {
    display: flex;
    align-items: center;
    gap: 10px;
}

.player-avatar {
    width: 30px;
    height: 30px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: #1e3c72;
}

.player-details h4 {
    margin: 0;
    font-size: 14px;
}

.player-details p {
    margin: 2px 0;
    font-size: 12px;
    opacity: 0.8;
}

.player-score {
    text-align: center;
    font-weight: bold;
    font-size: 16px;
}

.ai-button {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 15px 30px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}

.ai-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

.analysis-result {
    background: white;
    color: black;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    border-left: 5px solid #4ECDC4;
}

.stButton > button {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 15px 30px;
    font-size: 18px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🏈 Fantasy Football Dashboard")

# Check for OpenAI API key
if not client:
    st.error("⚠️ **OpenAI API key not configured**")
    st.info("Please set the OPENAI_API_KEY environment variable or in Streamlit secrets to use AI features.")
    st.stop()

# Display rate limiting dashboard in sidebar
if RATE_LIMITING_ENABLED:
    try:
        display_usage_dashboard()
        show_feature_costs()
    except Exception as e:
        st.sidebar.error(f"Rate limiting dashboard error: {str(e)}")

# Add cache clearing button
if st.button("🔄 Refresh Data", help="Clear cache and fetch fresh data"):
    st.cache_data.clear()
    st.rerun()

# Initialize session state for AI analysis
if 'ai_analysis_done' not in st.session_state:
    st.session_state.ai_analysis_done = False

if 'ai_analysis_result' not in st.session_state:
    st.session_state.ai_analysis_result = ""

# Fetch matchup data first
try:
    matchup_data = get_matchup()
    
    if matchup_data:
        my_team = matchup_data["my_team"]
        opponent_team = matchup_data["opponent_team"]
        
        # Calculate projections and stats - include FLEX positions
        my_projected_total = sum(player["projection"] for player in my_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        opponent_projected_total = sum(player["projection"] for player in opponent_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        
        # Calculate player status counts for my team
        my_currently_playing = len([p for p in my_team["roster"] if p["lineup_slot"] < 20 and p.get("game_started", False)])
        my_yet_to_play = len([p for p in my_team["roster"] if p["lineup_slot"] < 20 and not p.get("game_started", False)])
        my_proj_total = my_projected_total
        my_mins_left = sum([p.get("minutes_left", 0) for p in my_team["roster"] if p["lineup_slot"] < 20])
        
        # Calculate player status counts for opponent team
        opp_currently_playing = len([p for p in opponent_team["roster"] if p["lineup_slot"] < 20 and p.get("game_started", False)])
        opp_yet_to_play = len([p for p in opponent_team["roster"] if p["lineup_slot"] < 20 and not p.get("game_started", False)])
        opp_proj_total = opponent_projected_total
        opp_mins_left = sum([p.get("minutes_left", 0) for p in opponent_team["roster"] if p["lineup_slot"] < 20])
        
        # Display enhanced ESPN-style matchup
        st.markdown(f'''
        <div class="matchup-container">
            <div class="espn-matchup-header">
                <div class="espn-team-left">
                    <div class="espn-team-logo">{my_team["team_name"][0] if my_team["team_name"] else "M"}</div>
                    <div class="espn-team-info">
                        <h2>{my_team["team_name"]}</h2>
                        <div class="record">{my_team["record"]}</div>
                        <div class="manager">{my_team["manager"]}</div>
                    </div>
                </div>
                <div class="espn-projected-total">
                    <div class="espn-score-large">{my_projected_total:.1f} <span class="espn-vs">vs</span> {opponent_projected_total:.1f}</div>
                    <div class="espn-projected-label">Projected Total</div>
                </div>
                <div class="espn-team-right">
                    <div class="espn-team-logo">{opponent_team["team_name"][0] if opponent_team["team_name"] else "O"}</div>
                    <div class="espn-team-info">
                        <h2>{opponent_team["team_name"]}</h2>
                        <div class="record">{opponent_team["record"]}</div>
                        <div class="manager">{opponent_team["manager"]}</div>
                    </div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Enhanced roster comparison using Streamlit dataframe
        st.markdown('<div style="margin: 20px 0;">', unsafe_allow_html=True)
        
        # Deduplicate matchup roster data (same fix as in roster section)
        def deduplicate_matchup_roster(roster_data):
            unique_players = {}
            for player in roster_data:
                player_name = player.get("player_name", "Unknown")
                lineup_slot = player.get("lineup_slot", 999)
                
                # Keep player with lowest (most starting) lineup slot
                if player_name not in unique_players or lineup_slot < unique_players[player_name]["lineup_slot"]:
                    unique_players[player_name] = player
            return list(unique_players.values())
        
        # Apply deduplication to both teams
        my_team_deduped = deduplicate_matchup_roster(my_team["roster"])
        opp_team_deduped = deduplicate_matchup_roster(opponent_team["roster"])
        
        # Check for overlap (simplified debug)
        my_starters_names = [p.get("player_name", "Unknown") for p in my_team_deduped if p.get("lineup_slot", 999) < 20 or p.get("lineup_slot", 999) in [22, 23]]
        my_bench_names = [p.get("player_name", "Unknown") for p in my_team_deduped if p.get("lineup_slot", 999) >= 20 and p.get("lineup_slot", 999) not in [22, 23]]
        
        overlap = set(my_starters_names).intersection(set(my_bench_names))
        if overlap:
            st.error(f"⚠️ Duplicate players detected: {overlap}")
        # No success message needed since duplication is now resolved
        
        # Get starters for comparison - handle multiple players in same slot
        # Include FLEX positions (slots 22, 23) as starters
        my_starters = [p for p in my_team_deduped if p["lineup_slot"] < 20 or p["lineup_slot"] in [22, 23]]
        opp_starters = [p for p in opp_team_deduped if p["lineup_slot"] < 20 or p["lineup_slot"] in [22, 23]]
        
        # Group by slot but keep all players
        my_roster_by_slot = {}
        opp_roster_by_slot = {}
        
        for player in my_starters:
            slot = player["lineup_slot"]
            if slot not in my_roster_by_slot:
                my_roster_by_slot[slot] = []
            my_roster_by_slot[slot].append(player)
        
        for player in opp_starters:
            slot = player["lineup_slot"]
            if slot not in opp_roster_by_slot:
                opp_roster_by_slot[slot] = []
            opp_roster_by_slot[slot].append(player)
        
        # Get all unique lineup slots used and sort them with custom order
        all_slots = set(list(my_roster_by_slot.keys()) + list(opp_roster_by_slot.keys()))
        
        # Custom sort order: QB, RB, WR, TE, FLEX, K, DEF
        slot_order = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4, 7: 5, 22: 5, 23: 5, 8: 6, 17: 6, 16: 7, 9: 7}
        all_slots = sorted(all_slots, key=lambda x: (slot_order.get(x, 99), x))
        
        # Fetch roster data for enhanced player information
        try:
            enhanced_roster_data = get_roster()
        except:
            enhanced_roster_data = None
        
        # Helper function to get enhanced player data from roster
        def get_enhanced_player_data(player_name, roster_data_source):
            """Get additional player data (opp, status, ownership, etc.) from roster data"""
            if not roster_data_source or not player_name or player_name == "--":
                return {
                    "opp": "--", "STATUS": "--", "avg": "--"
                }
            
            # Find player in roster data
            for entry in roster_data_source.get("roster", []):
                if entry.get("player", "").lower() == player_name.split()[0].lower() or \
                   player_name.lower() in entry.get("player", "").lower():
                    # Get opponent from the entry
                    opponent = entry.get("opponent", "BYE")
                    
                    # Since all players are showing BYE (likely because it's offseason or API issue),
                    # let's show their NFL team instead for now
                    if opponent == "BYE" or not opponent or opponent == "--":
                        # Get NFL team from raw data
                        raw_player = entry.get("raw_player", {})
                        team_id = raw_player.get("proTeamId", 0)
                        nfl_teams = {
                            1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET", 
                            9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
                            17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
                            25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 31: "BAL", 32: "HOU"
                        }
                        opponent = nfl_teams.get(team_id, "BYE")
                    
                    return {
                        "opp": opponent,
                        "STATUS": entry.get("injury_status", "ACTIVE"),
                        "avg": f"{entry.get('current_season_stats', {}).get('appliedAverage', 0):.1f}" if entry.get('current_season_stats') else "--"
                    }
            
            return {
                "opp": "--", "STATUS": "--", "avg": "--"
            }
        
        # Build enhanced table data using actual lineup slots found in rosters
        table_data = []
        
        for slot in all_slots:
            my_players = my_roster_by_slot.get(slot, [])
            opp_players = opp_roster_by_slot.get(slot, [])
            
            # Handle multiple players in same slot
            max_players = max(len(my_players), len(opp_players), 1)
            
            for i in range(max_players):
                my_player = my_players[i] if i < len(my_players) else None
                opp_player = opp_players[i] if i < len(opp_players) else None
                
                # Get position name from the player or slot
                pos_name = ""
                if my_player:
                    pos_name = my_player['position']
                elif opp_player:
                    pos_name = opp_player['position']
                else:
                    pos_name = f"SLOT{slot}"
                
                my_name = f"{my_player['player_name']} {my_player['nfl_team']}" if my_player else "--"
                my_proj = my_player['projection'] if my_player else 0
                
                opp_name = f"{opp_player['nfl_team']} {opp_player['player_name']}" if opp_player else "--"
                opp_proj = opp_player['projection'] if opp_player else 0
                
                # Get enhanced data from roster
                my_enhanced = get_enhanced_player_data(my_player['player_name'] if my_player else "", enhanced_roster_data)
                opp_enhanced = get_enhanced_player_data(opp_player['player_name'] if opp_player else "", None)  # No opponent roster data
                
                # Calculate advantage  
                advantage = ""
                if my_player and opp_player:
                    diff = my_player["projection"] - opp_player["projection"]
                    if abs(diff) >= 0.1:  # Lower threshold to catch the 8.2 vs 8.0 case
                        advantage = "✓" if diff > 0 else ""
                
                table_data.append({
                    "MY TEAM": my_name,
                    "POS": pos_name,
                    "STATUS": my_enhanced["STATUS"],
                    "AVG": my_enhanced["avg"],
                    "PROJ": f"{my_proj:.1f}" if my_proj > 0 else "--",
                    "VS": advantage,
                    "PROJ ": f"{opp_proj:.1f}" if opp_proj > 0 else "--",
                    "OPPONENT TEAM": opp_name
                })
        
        # Add totals row
        total_diff = my_projected_total - opponent_projected_total
        table_data.append({
            "MY TEAM": "**TOTALS**",
            "POS": "",
            "STATUS": "",
            "AVG": "",
            "PROJ": f"**{my_projected_total:.1f}**",
            "VS": "✓" if total_diff > 0 else "",
            "PROJ ": f"**{opponent_projected_total:.1f}**",
            "OPPONENT TEAM": "**TOTALS**"
        })
        
        # Create and display the dataframe
        matchup_df = pd.DataFrame(table_data)
        st.markdown("**Starters**")
        st.dataframe(matchup_df, use_container_width=True, hide_index=True)
        
        # Bench section (using deduplicated data)
        # Be specific: bench is >= 20 BUT exclude FLEX slots 22, 23
        my_bench = [p for p in my_team_deduped if p["lineup_slot"] >= 20 and p["lineup_slot"] not in [22, 23]]
        opp_bench = [p for p in opp_team_deduped if p["lineup_slot"] >= 20 and p["lineup_slot"] not in [22, 23]]
        
        # Bench filtering applied (FLEX slots 22,23 excluded from bench)
        
        if my_bench or opp_bench:
            st.markdown("**Bench**")
            
            # Create bench table data
            bench_data = []
            max_bench = max(len(my_bench), len(opp_bench))
            for i in range(max_bench):
                my_player = my_bench[i] if i < len(my_bench) else None
                opp_player = opp_bench[i] if i < len(opp_bench) else None
                
                my_name = f"{my_player['player_name']} {my_player['nfl_team']}" if my_player else "--"
                my_pos = my_player["position"] if my_player else ""
                my_proj = my_player['projection'] if my_player else 0
                
                opp_name = f"{opp_player['nfl_team']} {opp_player['player_name']}" if opp_player else "--"
                opp_pos = opp_player["position"] if opp_player else ""
                opp_proj = opp_player['projection'] if opp_player else 0
                
                # Get enhanced data for bench players
                my_enhanced = get_enhanced_player_data(my_player['player_name'] if my_player else "", enhanced_roster_data)
                
                bench_data.append({
                    "MY TEAM": my_name,
                    "POS": my_pos,
                    "STATUS": my_enhanced["STATUS"],
                    "AVG": my_enhanced["avg"],
                    "PROJ": f"{my_proj:.1f}" if my_proj > 0 else "--",
                    "VS": "",
                    "PROJ ": f"{opp_proj:.1f}" if opp_proj > 0 else "--",
                    "OPPONENT TEAM": opp_name
                })
            
            if bench_data:
                bench_df = pd.DataFrame(bench_data)
                st.dataframe(bench_df, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # AI-Powered Features Section
        st.markdown("---")
        
        # Header with API status
        header_col1, header_col2 = st.columns([3, 1])
        
        with header_col1:
            st.header("🤖 AI-Powered Fantasy Tools")
        
        with header_col2:
            # Check if OpenAI API key is available
            if os.getenv("OPENAI_API_KEY"):
                st.success("✅ AI Ready - OpenAI API key found and configured")
            else:
                st.error("❌ API Key Missing - OpenAI API key not found in .env file")
        
        # Add some spacing
        st.write("")
        
        # Create four columns for the AI features
        ai_col1, ai_col2, ai_col3, ai_col4 = st.columns(4)
        
        with ai_col1:
            with st.container():
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    color: white;
                    margin-bottom: 10px;
                ">
                    <h3 style="margin: 0; color: white;">🎯 Lineup Optimizer</h3>
                    <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">Get AI recommendations for your optimal starting lineup</p>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Optimize My Lineup", key="optimize_lineup", help="Get AI-powered lineup recommendations", use_container_width=True):
                # Check rate limits before proceeding
                if RATE_LIMITING_ENABLED:
                    can_proceed, cost, reason = rate_limiter.can_make_request(
                        "gpt-4-turbo", 1500, 800
                    )
                    if not can_proceed:
                        st.error(f"🚫 **Rate Limit Exceeded**\n\n{reason}")
                        st.info("💡 **Tip:** Try again later or use simpler queries to reduce costs.")
                    else:
                        st.info(f"💰 Estimated cost: ~${cost:.3f}")
                        # Store the request in session state to handle results display
                        st.session_state.lineup_optimization_requested = True
                else:
                    # No rate limiting, proceed normally
                    st.session_state.lineup_optimization_requested = True
        
        with ai_col2:
            with st.container():
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    color: white;
                    margin-bottom: 10px;
                ">
                    <h3 style="margin: 0; color: white;">⚡ Start/Sit Analyzer</h3>
                    <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">Compare two players to decide who to start</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Player selection
            if matchup_data:
                all_players = []
                for player in my_team.get("roster", []):
                    player_name = player.get("player_name", "Unknown")
                    if player_name != "Unknown":
                        all_players.append(player_name)
                
                if len(all_players) >= 2:
                    player1 = st.selectbox("Player 1:", all_players, key="player1_select")
                    player2 = st.selectbox("Player 2:", all_players, key="player2_select", index=1)
                    
                    if st.button("🤔 Who Should I Start?", key="compare_players", help="Get AI analysis of which player to start", use_container_width=True):
                        if player1 != player2:
                            # Store comparison request in session state
                            st.session_state.player_comparison_requested = True
                            st.session_state.selected_player1 = player1
                            st.session_state.selected_player2 = player2
                        else:
                            st.warning("⚠️ Please select two different players")
                else:
                    st.info("Need at least 2 players on your roster to compare")
            else:
                st.info("Matchup data needed for player comparison")
        
        with ai_col3:
            with st.container():
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    color: white;
                    margin-bottom: 10px;
                ">
                    <h3 style="margin: 0; color: white;">🔍 Waiver Wire Scout</h3>
                    <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">Find the best available players to improve your team</p>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Analyze Waiver Wire", key="waiver_wire", help="Get AI recommendations for waiver wire pickups", use_container_width=True):
                # Check rate limits before proceeding
                if RATE_LIMITING_ENABLED:
                    can_proceed, cost, reason = rate_limiter.can_make_request(
                        "gpt-4-turbo", 2000, 1200
                    )
                    if not can_proceed:
                        st.error(f"🚫 **Rate Limit Exceeded**\n\n{reason}")
                        st.info("💡 **Tip:** Try again later or use simpler queries to reduce costs.")
                    else:
                        st.info(f"💰 Estimated cost: ~${cost:.3f}")
                        with st.spinner("🤖 AI is scouting the waiver wire..."):
                            waiver_result = get_ai_waiver_wire_analysis()
                        
                            if waiver_result and waiver_result.get("status") == "success":
                                st.success("✅ Waiver wire analysis complete!")
                                
                                # Display top recommendations
                                top_recs = waiver_result.get("top_recommendations", [])
                                if top_recs:
                                    st.write("**🏆 Top Waiver Wire Targets:**")
                                    
                                    for i, rec in enumerate(top_recs[:5]):  # Top 5
                                        priority_color = "🔴" if rec.get("priority") == "High" else "🟡" if rec.get("priority") == "Medium" else "🟢"
                                        st.write(f"{priority_color} **{rec.get('player_name', 'Unknown')}** ({rec.get('position', 'UNK')}) - {rec.get('nfl_team', 'UNK')}")
                                        st.write(f"   📈 Projection: {rec.get('projected_value', 0):.1f} pts")
                                        st.write(f"   💡 {rec.get('reasoning', 'No reasoning')}")
                                        if rec.get('drop_candidate'):
                                            st.write(f"   ⬇️ Consider dropping: {rec.get('drop_candidate')}")
                                        st.write("")
                                
                                # Show positional needs
                                pos_needs = waiver_result.get("positional_needs", {})
                                if pos_needs:
                                    st.write("**📊 Positional Needs Analysis:**")
                                    for pos, analysis in pos_needs.items():
                                        priority = "🔴" if "High priority" in analysis else "🟡" if "Medium priority" in analysis else "🟢"
                                        st.write(f"{priority} **{pos}:** {analysis}")
                                
                                # Show injury watch list
                                injury_watch = waiver_result.get("injury_watch", [])
                                if injury_watch:
                                    st.write("**🏥 Injury Watch:**")
                                    for item in injury_watch:
                                        st.write(f"⚠️ {item}")
                            
                            elif waiver_result:
                                st.error(f"❌ {waiver_result.get('message', 'Waiver wire analysis failed')}")
                            else:
                                st.error("❌ Could not connect to AI service")
                else:
                    with st.spinner("🤖 AI is scouting the waiver wire..."):
                        waiver_result = get_ai_waiver_wire_analysis()
                    
                    if waiver_result and waiver_result.get("status") == "success":
                        st.success("✅ Waiver wire analysis complete!")
                        
                        # Display top recommendations
                        top_recs = waiver_result.get("top_recommendations", [])
                        if top_recs:
                            st.write("**🏆 Top Waiver Wire Targets:**")
                            
                            for i, rec in enumerate(top_recs[:5]):  # Top 5
                                priority_color = "🔴" if rec.get("priority") == "High" else "🟡" if rec.get("priority") == "Medium" else "🟢"
                                st.write(f"{priority_color} **{rec.get('player_name', 'Unknown')}** ({rec.get('position', 'UNK')}) - {rec.get('nfl_team', 'UNK')}")
                                st.write(f"   📈 Projection: {rec.get('projected_value', 0):.1f} pts")
                                st.write(f"   💡 {rec.get('reasoning', 'No reasoning')}")
                                if rec.get('drop_candidate'):
                                    st.write(f"   ⬇️ Consider dropping: {rec.get('drop_candidate')}")
                                st.write("")
                        
                        # Show positional needs
                        pos_needs = waiver_result.get("positional_needs", {})
                        if pos_needs:
                            st.write("**📊 Positional Needs Analysis:**")
                            for pos, analysis in pos_needs.items():
                                priority = "🔴" if "High priority" in analysis else "🟡" if "Medium priority" in analysis else "🟢"
                                st.write(f"{priority} **{pos}:** {analysis}")
                        
                        # Show injury watch list
                        injury_watch = waiver_result.get("injury_watch", [])
                        if injury_watch:
                            st.write("**🏥 Injury Watch:**")
                            for item in injury_watch:
                                st.write(f"⚠️ {item}")
                    
                    elif waiver_result:
                        st.error(f"❌ {waiver_result.get('message', 'Waiver wire analysis failed')}")
                    else:
                        st.error("❌ Could not connect to AI service")
        
        with ai_col4:
            with st.container():
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    color: white;
                    margin-bottom: 10px;
                ">
                    <h3 style="margin: 0; color: white;">🤝 Trade Analyzer</h3>
                    <p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9);">Discover beneficial trades to upgrade your roster</p>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🚀 Find Trade Opportunities", key="trade_analysis", help="Get AI recommendations for trades", use_container_width=True):
                with st.spinner("🤖 AI is analyzing trade opportunities..."):
                    trade_result = get_ai_trade_analysis()
                    
                    if trade_result and trade_result.get("status") == "success":
                        st.success("✅ Trade analysis complete!")
                        
                        # Display trade targets
                        trade_targets = trade_result.get("trade_targets", [])
                        if trade_targets:
                            st.write("**🎯 Recommended Trade Targets:**")
                            
                            for i, target in enumerate(trade_targets[:3]):  # Top 3
                                st.write(f"**Trade {i+1}: {target.get('target_team', 'Unknown Team')}**")
                                
                                proposal = target.get('trade_proposal', {})
                                give = proposal.get('give', [])
                                receive = proposal.get('receive', [])
                                
                                if give and receive:
                                    st.write(f"📤 **Give:** {', '.join(give)}")
                                    st.write(f"📥 **Receive:** {', '.join(receive)}")
                                
                                confidence = target.get('confidence', 'Unknown')
                                confidence_color = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
                                st.write(f"{confidence_color} **Confidence:** {confidence}")
                                
                                reasoning = target.get('trade_reasoning', 'No reasoning provided')
                                st.write(f"💭 **Why:** {reasoning}")
                                
                                impact = target.get('expected_impact', '')
                                if impact:
                                    st.write(f"📈 **Impact:** {impact}")
                                st.write("---")
                        
                        # Show roster analysis
                        roster_analysis = trade_result.get("roster_analysis", {})
                        if roster_analysis:
                            st.write("**📊 Your Roster Analysis:**")
                            
                            strengths = roster_analysis.get("strengths", [])
                            if strengths:
                                st.write("**💪 Strengths:**")
                                for strength in strengths:
                                    st.write(f"✅ {strength}")
                            
                            weaknesses = roster_analysis.get("weaknesses", [])
                            if weaknesses:
                                st.write("**🔧 Areas to Improve:**")
                                for weakness in weaknesses:
                                    st.write(f"❌ {weakness}")
                        
                        # Show market analysis
                        market_analysis = trade_result.get("market_analysis", {})
                        if market_analysis:
                            buy_low = market_analysis.get("buy_low_candidates", [])
                            sell_high = market_analysis.get("sell_high_candidates", [])
                            
                            if buy_low or sell_high:
                                st.write("**📈 Market Opportunities:**")
                                
                                if buy_low:
                                    st.write("**Buy Low Targets:**")
                                    for candidate in buy_low:
                                        st.write(f"📉 {candidate.get('player', 'Unknown')}: {candidate.get('reasoning', '')}")
                                
                                if sell_high:
                                    st.write("**Sell High Candidates:**")
                                    for candidate in sell_high:
                                        st.write(f"📈 {candidate.get('player', 'Unknown')}: {candidate.get('reasoning', '')}")
                    
                    elif trade_result:
                        st.error(f"❌ {trade_result.get('message', 'Trade analysis failed')}")
                    else:
                        st.error("❌ Could not connect to AI service")

        # Handle Lineup Optimization Results Display (outside columns to prevent duplication)
        if hasattr(st.session_state, 'lineup_optimization_requested') and st.session_state.lineup_optimization_requested:
            st.markdown("---")
            st.subheader("🎯 AI Lineup Optimization Results")
            
            with st.spinner("🤖 AI is analyzing your roster..."):
                optimization_result = get_ai_lineup_optimization()
                
                if optimization_result and optimization_result.get("status") == "success":
                    st.success("✅ Lineup optimization complete!")
                    
                    # Display optimal lineup
                    st.write("**🏆 Recommended Starting Lineup:**")
                    optimal_lineup = optimization_result.get("optimal_lineup", {})
                    
                    lineup_data = []
                    for position, player_info in optimal_lineup.items():
                        lineup_data.append({
                            "Position": position,
                            "Player": player_info.get("name", "Unknown"),
                            "Projection": f"{player_info.get('projection', 0):.1f}",
                            "Reasoning": player_info.get("reason", "No reason provided")
                        })
                    
                    if lineup_data:
                        lineup_df = pd.DataFrame(lineup_data)
                        st.dataframe(lineup_df, use_container_width=True, hide_index=True)
                        
                        # Show summary stats
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Projected Total", f"{optimization_result.get('projected_total', 0):.1f}")
                        with col_b:
                            st.metric("Confidence", optimization_result.get('confidence_level', 'Unknown'))
                        with col_c:
                            st.metric("Risk Level", optimization_result.get('risk_assessment', 'Unknown'))
                        
                        # Show key decisions
                        key_decisions = optimization_result.get("key_decisions", [])
                        if key_decisions:
                            st.write("**🔑 Key Decisions:**")
                            for decision in key_decisions:
                                st.write(f"• {decision}")
                
                elif optimization_result:
                    st.error(f"❌ {optimization_result.get('message', 'Optimization failed')}")
                else:
                    st.error("❌ Could not connect to AI service")
                
                # Clear the request flag to prevent re-running
                st.session_state.lineup_optimization_requested = False

        # Handle Start/Sit Analysis Results Display (outside columns to prevent duplication)
        if hasattr(st.session_state, 'player_comparison_requested') and st.session_state.player_comparison_requested:
            st.markdown("---")
            st.subheader("⚡ AI Start/Sit Analysis Results")
            
            with st.spinner("🤖 AI is analyzing the matchup..."):
                player1 = st.session_state.selected_player1
                player2 = st.session_state.selected_player2
                comparison_result = get_ai_player_comparison(player1, player2)
                
                if comparison_result and comparison_result.get("status") == "success":
                    st.success("✅ Analysis complete!")
                    
                    # Show recommendation
                    recommended = comparison_result.get("recommendation", "Unknown")
                    confidence = comparison_result.get("confidence", "Unknown")
                    reasoning = comparison_result.get("reasoning", "No reasoning provided")
                    
                    st.write(f"**🏆 Recommendation:** Start **{recommended}**")
                    st.write(f"**🎯 Confidence:** {confidence}")
                    st.write(f"**💭 Reasoning:** {reasoning}")
                    
                    # Show detailed analysis
                    player1_analysis = comparison_result.get("player1_analysis", {})
                    player2_analysis = comparison_result.get("player2_analysis", {})
                    
                    if player1_analysis and player2_analysis:
                        st.write("**📊 Detailed Analysis:**")
                        
                        p1_col, p2_col = st.columns(2)
                        
                        with p1_col:
                            st.write(f"**{player1}**")
                            st.write(f"Projection: {player1_analysis.get('projection', 0):.1f}")
                            st.write(f"Floor: {player1_analysis.get('floor', 0):.1f}")  
                            st.write(f"Ceiling: {player1_analysis.get('ceiling', 0):.1f}")
                            
                            pros = player1_analysis.get('pros', [])
                            cons = player1_analysis.get('cons', [])
                            if pros:
                                st.write("**Pros:**")
                                for pro in pros:
                                    st.write(f"✅ {pro}")
                            if cons:
                                st.write("**Cons:**")
                                for con in cons:
                                    st.write(f"❌ {con}")
                        
                        with p2_col:
                            st.write(f"**{player2}**")
                            st.write(f"Projection: {player2_analysis.get('projection', 0):.1f}")
                            st.write(f"Floor: {player2_analysis.get('floor', 0):.1f}")
                            st.write(f"Ceiling: {player2_analysis.get('ceiling', 0):.1f}")
                            
                            pros = player2_analysis.get('pros', [])
                            cons = player2_analysis.get('cons', [])
                            if pros:
                                st.write("**Pros:**")
                                for pro in pros:
                                    st.write(f"✅ {pro}")
                            if cons:
                                st.write("**Cons:**")
                                for con in cons:
                                    st.write(f"❌ {con}")
                
                elif comparison_result:
                    st.error(f"❌ {comparison_result.get('message', 'Analysis failed')}")
                else:
                    st.error("❌ Could not connect to AI service")
                
                # Clear the request flag to prevent re-running
                st.session_state.player_comparison_requested = False
        
    else:
        st.warning("No matchup data available. Showing roster only.")

except Exception as e:
    st.error(f"Error fetching matchup data: {str(e)}")
    st.info("Continuing with roster display...")


# Team Analysis Section (moved from separate section)
if os.getenv("OPENAI_API_KEY"):
    st.markdown("---")
    st.subheader("📊 AI Team Analysis")
    
    # AI Analysis Button
    if st.button("🚀 Get AI Team Analysis", key="ai_analysis_button"):
        st.session_state.ai_analysis_done = True

        # Show loading spinner
        with st.spinner("🤖 AI is analyzing your team..."):
            try:
                # Get roster data if not available
                if 'roster_data' not in locals():
                    roster_data = get_roster()
                    
                if roster_data and "roster" in roster_data:
                    roster_entries = roster_data["roster"]

                    # Create a comprehensive team summary for AI analysis
                    team_summary = f"""
                    **Team Analysis Request:**
                    
                    Team Name: {roster_data.get('team_name', 'Your Team')}
                    Current Week: {roster_data.get('week', 1)}
                    Season: 2025
                    Total Players: {len(roster_entries)}
                    
                    **Roster Breakdown:**
                    """

                    # Group players by position
                    position_groups = {}
                    for entry in roster_entries:
                        player = entry.get("raw_player", {})
                        position = entry.get("position", "Unknown")
                        lineup_slot = entry.get("lineup_slot", "Unknown")
                        injury_status = entry.get("injury_status", "Unknown")
                        weekly_proj = entry.get("weekly_proj_value", 0.0)
                        opponent = entry.get("opponent", "TBD")
                        ownership = entry.get("ownership", {})

                        if position not in position_groups:
                            position_groups[position] = []

                        position_groups[position].append({
                            "name": player.get('fullName', 'Unknown'),
                            "lineup_slot": lineup_slot,
                            "projection": weekly_proj,
                            "status": injury_status,
                            "opponent": opponent,
                            "percent_owned": ownership.get("percentOwned", 0),
                            "percent_started": ownership.get("percentStarted", 0)
                        })

                    # Add position breakdown to summary
                    for pos, players in position_groups.items():
                        team_summary += f"\n**{pos} Position ({len(players)} players):**\n"
                        for player in players:
                            team_summary += f"• {player['name']} - {player['lineup_slot']} - Projected: {player['projection']} pts - Status: {player['status']} - vs {player['opponent']} - Owned: {player['percent_owned']:.1f}% - Started: {player['percent_started']:.1f}%\n"

                    # AI Analysis prompt
                    analysis_prompt = f"""
                    You are a fantasy football expert analyst. Based on this roster data, provide a comprehensive analysis including:
                    
                    1. **Team Strengths**: What positions are strongest and why?
                    2. **Team Weaknesses**: What areas need improvement?
                    3. **Injury Concerns**: Any players with injury issues that could impact performance?
                    4. **Trade Recommendations**: Who should I trade for/away and why?
                    5. **Waiver Wire Targets**: What positions should I target on the waiver wire?
                    6. **Lineup Optimization**: What's the best starting lineup for this week?
                    7. **Season Outlook**: How does this team look for the season?
                    8. **Weekly Strategy**: Any specific strategies for this week's matchup?
                    
                    Roster Data: {team_summary}
                    
                    Please provide specific, actionable advice. Be detailed but concise. Focus on practical fantasy football management tips.
                    """

                    # Call OpenAI API
                    response = client.chat.completions.create(model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a fantasy football expert analyst with deep knowledge of NFL players, strategies, and fantasy football management. Provide actionable, specific advice."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.7,)

                    # Store the result
                    st.session_state.ai_analysis_result = response.choices[0].message.content

                else:
                    st.error("No roster data available for analysis")

            except Exception as e:
                st.error(f"❌ Error calling OpenAI API: {str(e)}")
                st.info("Please check your API key and internet connection")

    # Display AI Analysis Result
    if st.session_state.ai_analysis_done and st.session_state.ai_analysis_result:
        st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
        st.subheader("🎯 AI Team Analysis Results")
        st.markdown(st.session_state.ai_analysis_result)

        # Clear analysis button
        if st.button("🗑️ Clear Analysis", key="clear_analysis"):
            st.session_state.ai_analysis_done = False
            st.session_state.ai_analysis_result = ""
            st.rerun()


# Footer
st.markdown("---")
st.markdown("*Powered by ESPN Fantasy API + OpenAI GPT-4* 🚀")
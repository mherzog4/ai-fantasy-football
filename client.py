import openai
import streamlit as st
import requests as req
from api.get_roster import espn_get, get_roster
import pandas as pd
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")


# Set page config
st.set_page_config(
    page_title="Fantasy Football Roster",
    page_icon="🏈",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
.ai-analysis-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 20px 0;
    color: white;
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
st.title("🏈 Fantasy Football Roster Dashboard")

# Initialize session state for AI analysis
if 'ai_analysis_done' not in st.session_state:
    st.session_state.ai_analysis_done = False

if 'ai_analysis_result' not in st.session_state:
    st.session_state.ai_analysis_result = ""

# Fetch roster data
try:
    roster_data = get_roster()

    # Debug: Show what we got from the API
    st.write("**Debug: API Response Structure:**")
    st.write(f"Keys in roster_data: {list(roster_data.keys()) if roster_data else 'None'}")

    if roster_data and "roster" in roster_data:
        # Extract roster entries
        roster_entries = roster_data["roster"]
        st.write(f"**Debug: Roster entries count: {len(roster_entries)}**")

        if roster_entries:
            # Show first entry structure
            st.write("**Debug: First roster entry structure:**")
            st.json(roster_entries[0])

        # Create a list to store processed data
        processed_data = []

        for entry in roster_entries:
            # Debug: Show what's in each entry
            st.write(f"**Debug: Processing entry with keys: {list(entry.keys())}**")

            player = entry.get("raw_player", {})
            raw_entry = entry.get("raw_entry", {})

            # Get enhanced data from the updated API
            current_stats = entry.get("current_stats")
            last_season_stats = entry.get("last_season_stats")
            weekly_proj = entry.get("weekly_proj_value", 0.0)
            opponent = entry.get("opponent", "TBD")
            ownership = entry.get("ownership", {})
            ownership_change = entry.get("ownership_change", 0.0)
            rankings = entry.get("rankings", [])
            draft_ranks = entry.get("draft_ranks", {})

            # Get current week score if available
            current_score = "--"
            if current_stats:
                current_score = round(current_stats.get("appliedTotal", 0), 1)

            # Get last season average
            last_avg = 0.0
            if last_season_stats:
                last_avg = round(last_season_stats.get("appliedAverage", 0), 1)

            # Extract relevant information to match ESPN's format
            player_info = {
                "SLOT": entry.get("lineup_slot", "Unknown"),
                "Player": player.get("fullName", "Unknown"),
                "action": "MOVE",  # ESPN shows MOVE for all players
                "opp": opponent,  # Now shows actual opponent
                "STATUS": player.get("injuryStatus", "ACTIVE"),
                "This Week Projection": weekly_proj,  # Weekly projection, not season total
                "SCORE": current_score,  # Current week score
                "OPRK": "--",  # Opponent rank (not available)
                "%ST": ownership.get("percentStarted", 0),
                "%ROST": ownership.get("percentOwned", 0),
                "+/-": ownership_change,  # Now shows actual ownership change
                "FPTS": round(current_stats.get("appliedTotal", 0), 1) if current_stats else 0.0,
                "avg": last_avg,  # Last season average
                "LAST": "--",  # Last week's score (not available)
                "Position": player.get("defaultPositionId", "Unknown"),
                "NFL Team": player.get("proTeamId", "Unknown"),
                "Injury Status": player.get("injuryStatus", "Unknown"),
                "Lineup Slot": entry.get("lineup_slot", "Unknown"),
                "Acquisition Type": raw_entry.get("acquisitionType", "Unknown"),
                "Keeper Value": raw_entry.get("playerPoolEntry", {}).get("keeperValue", "N/A"),
                "Percent Owned": player.get("ownership", {}).get("percentOwned", "N/A"),
                "Average Draft Position": player.get("ownership", {}).get("averageDraftPosition", "N/A"),
            }

            # Add detailed stats if available
            if current_stats:
                applied_stats = current_stats.get("appliedStats", {})
                player_info.update({
                    "Fantasy Points": round(current_stats.get("appliedTotal", 0), 2),
                    "Rushing Yards": applied_stats.get("24", 0),  # ESPN stat ID for rushing yards
                    "Rushing TDs": applied_stats.get("25", 0),    # ESPN stat ID for rushing TDs
                    "Receiving Yards": applied_stats.get("42", 0), # ESPN stat ID for receiving yards
                    "Receiving TDs": applied_stats.get("43", 0),  # ESPN stat ID for receiving TDs
                    "Passing Yards": applied_stats.get("3", 0),   # ESPN stat ID for passing yards
                    "Passing TDs": applied_stats.get("4", 0),    # ESPN stat ID for passing TDs
                    "Interceptions": applied_stats.get("20", 0),  # ESPN stat ID for interceptions
                })
            else:
                player_info.update({
                    "Fantasy Points": 0,
                    "Rushing Yards": 0,
                    "Rushing TDs": 0,
                    "Receiving Yards": 0,
                    "Receiving TDs": 0,
                    "Passing Yards": 0,
                    "Passing TDs": 0,
                    "Interceptions": 0,
                })

            processed_data.append(player_info)

        st.write(f"**Debug: Processed data count: {len(processed_data)}**")

        if processed_data:
            # Create DataFrame
            df = pd.DataFrame(processed_data)

            # Debug: Show what columns we actually have
            st.write(f"**Debug: DataFrame columns:** {list(df.columns)}")
            st.write(f"**Debug: DataFrame shape:** {df.shape}")
            st.write(f"**Debug: First few rows:**")
            st.dataframe(df.head())

            # Clean up position and team names
            def get_position_name(pos_id):
                positions = {
                    0: "QB", 1: "RB", 2: "RB", 3: "WR", 4: "WR", 5: "TE", 6: "TE", 7: "FLEX", 
                    8: "K", 9: "DEF", 10: "DEF", 11: "DEF", 12: "DEF", 13: "DEF", 14: "DEF", 
                    15: "DEF", 16: "DEF", 17: "DEF", 18: "DEF", 19: "DEF", 20: "BENCH", 21: "IR"
                }
                return positions.get(pos_id, f"POS{pos_id}")

            def get_nfl_team_name(team_id):
                teams = {
                    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
                    9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
                    17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
                    25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 31: "BAL", 32: "HOU"
                }
                return teams.get(team_id, f"TEAM{team_id}")

            def get_lineup_slot_name(slot_id):
                slots = {
                    0: "QB", 1: "RB", 2: "RB", 3: "WR", 4: "WR", 5: "TE", 6: "TE", 7: "FLEX", 
                    8: "K", 9: "DEF", 10: "DEF", 11: "DEF", 12: "DEF", 13: "DEF", 14: "DEF", 
                    15: "DEF", 16: "DEF", 17: "DEF", 18: "DEF", 19: "DEF", 20: "BENCH", 21: "IR"
                }
                return slots.get(slot_id, f"SLOT{slot_id}")

            # Apply the name mappings
            if "Position" in df.columns:
                df["Position"] = df["Position"].apply(get_position_name)
            if "NFL Team" in df.columns:
                df["NFL Team"] = df["NFL Team"].apply(get_nfl_team_name)
            if "Lineup Slot" in df.columns:
                df["Lineup Slot"] = df["Lineup Slot"].apply(get_lineup_slot_name)
            if "SLOT" in df.columns:
                df["SLOT"] = df["SLOT"].apply(get_lineup_slot_name)

            # Format percentages
            if "%ST" in df.columns:
                df["%ST"] = df["%ST"].apply(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else str(x))
            if "%ROST" in df.columns:
                df["%ROST"] = df["%ROST"].apply(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else str(x))

            # Display team info
            st.header(f"📊 {roster_data.get('team_name', 'Your Team')} - Week {roster_data.get('week', 1)}")

            # Create ESPN-style roster display
            st.subheader("🏈 ESPN-Style Roster View")

            # Separate starters and bench
            starters = df[df["SLOT"].isin(["QB", "RB", "WR", "TE", "FLEX", "K", "DEF"])]
            bench = df[df["SLOT"] == "BENCH"]

            # Display starters
            if not starters.empty:
                st.write("**STARTERS**")
                starters_display = starters[["SLOT", "Player", "opp", "STATUS", "This Week Projection", "OPRK", "%ST", "%ROST", "+/-", "FPTS", "avg", "LAST"]].copy()
                st.dataframe(starters_display, use_container_width=True, hide_index=True)

            # Display bench
            if not bench.empty:
                st.write("**Bench**")
                bench_display = bench[["SLOT", "Player", "opp", "STATUS", "This Week Projection", "OPRK", "%ST", "%ROST", "+/-", "FPTS", "avg", "LAST"]].copy()
                st.dataframe(bench_display, use_container_width=True, hide_index=True)

            # Display the detailed roster dataframe
            st.subheader("📋 Detailed Roster Data")
            detailed_columns = ["Player", "Position", "NFL Team", "Injury Status", "Lineup Slot", "Fantasy Points"]
            available_columns = [col for col in detailed_columns if col in df.columns]
            if available_columns:
                detailed_df = df[available_columns].copy()
                st.dataframe(detailed_df, use_container_width=True)
            else:
                st.error("No detailed columns available")
                st.write("Available columns:", list(df.columns))

            # Add some filters and analysis
            st.subheader("🏈 Roster Analysis")

            # Position breakdown
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Players", len(df))
                st.metric("Active Players", len(df[df["Lineup Slot"] != "BENCH"]))

            with col2:
                position_counts = df["Position"].value_counts()
                st.write("**Position Breakdown:**")
                for pos, count in position_counts.items():
                    st.write(f"{pos}: {count}")

            with col3:
                injury_counts = df["Injury Status"].value_counts()
                st.write("**Injury Status:**")
                for status, count in injury_counts.items():
                    st.write(f"{status}: {count}")

            # Show players by lineup slot - FIXED COLUMN NAME
            st.subheader("👥 Players by Lineup Slot")
            slot_breakdown = df.groupby("Lineup Slot").agg({
                "Player": list,  # Changed from "Player Name" to "Player"
                "Fantasy Points": "sum"
            }).reset_index()
            st.dataframe(slot_breakdown, use_container_width=True)

            # Show top performers
            st.subheader("⭐ Top Performers (Fantasy Points)")
            top_performers = df.nlargest(5, "Fantasy Points")[["Player", "Position", "Fantasy Points"]]
            st.dataframe(top_performers, use_container_width=True)

            # Debug section to see what data we're getting
            st.subheader("🐛 Debug: API Data Analysis")

            # Show sample player data structure
            if roster_data.get("debug_info", {}).get("sample_player_data"):
                st.write("**Sample Player Data Structure:**")
                sample_player = roster_data["debug_info"]["sample_player_data"]
                st.json(sample_player)

            # Show what views we're using
            st.write(f"**API Views Used:** {roster_data.get('debug_info', {}).get('views_used', [])}")

            # Show available data keys
            st.write(f"**Available Data Keys:** {roster_data.get('debug_info', {}).get('available_data_keys', [])}")

            # Show projection data analysis
            st.write("**Projection Data Analysis:**")
            projection_analysis = []
            for entry in roster_entries:
                player_name = entry.get("raw_player", {}).get("fullName", "Unknown")
                weekly_proj = entry.get("weekly_proj_value", 0.0)
                opponent = entry.get("opponent", "TBD")
                ownership_change = entry.get("ownership_change", 0.0)
                draft_ranks = entry.get("draft_ranks", {})

                analysis = {
                    "Player": player_name,
                    "Weekly Projection": weekly_proj,
                    "Opponent": opponent,
                    "Ownership Change": ownership_change,
                    "Has Draft Ranks": "Yes" if draft_ranks else "No",
                    "PPR Rank": draft_ranks.get("PPR", [{}])[0].get("rank", "N/A") if draft_ranks.get("PPR") else "N/A",
                    "Standard Rank": draft_ranks.get("STANDARD", [{}])[0].get("rank", "N/A") if draft_ranks.get("STANDARD") else "N/A"
                }
                projection_analysis.append(analysis)

            projection_df = pd.DataFrame(projection_analysis)
            st.dataframe(projection_df, use_container_width=True)

            # Show matchup information
            if roster_data.get("current_matchup"):
                st.subheader("🏈 Current Week Matchup")
                matchup = roster_data["current_matchup"]
                st.write(f"**Week {matchup.get('matchupPeriodId', 'Unknown')} Matchup**")
                st.json(matchup)

        else:
            st.error("No processed data available")
            st.write("Raw roster entries:", roster_entries)
    else:
        st.error("No roster data found. Please check your ESPN API connection.")
        st.write("Full API response:", roster_data)

except Exception as e:
    st.error(f"Error fetching roster data: {str(e)}")
    st.write("Please make sure your FastAPI server is running and accessible.")

    # Show debug info
    st.subheader("🐛 Debug Information")
    try:
        test_data = espn_get(["mTeam", "mSettings"])
        st.json(test_data)
    except Exception as debug_e:
        st.error(f"Debug error: {str(debug_e)}")

# AI Analysis Section - Now with working functionality!
st.markdown('<div class="ai-analysis-section">', unsafe_allow_html=True)
st.subheader("🤖 AI Team Analysis")

# Check if OpenAI API key is available
if not openai.api_key:
    st.error("⚠️ OpenAI API key not found! Please check your .env file.")
    st.info("Make sure you have OPENAI_API_KEY=your_key_here in your .env file")
else:
    st.success("✅ OpenAI API key found and ready!")

    # AI Analysis Button
    if st.button("🚀 Get AI Team Analysis", key="ai_analysis_button"):
        st.session_state.ai_analysis_done = True

        # Show loading spinner
        with st.spinner("🤖 AI is analyzing your team..."):
            try:
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

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("*Powered by ESPN Fantasy API + OpenAI GPT-4* 🚀")
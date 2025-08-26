import streamlit as st
import requests as req
from api.get_roster import espn_get, get_roster
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Fantasy Football Roster",
    page_icon="🏈",
    layout="wide"
)

# Title
st.title("🏈 Fantasy Football Roster Dashboard")

# Fetch roster data
try:
    roster_data = get_roster()
    
    if roster_data and "roster" in roster_data:
        # Extract roster entries
        roster_entries = roster_data["roster"]
        
        # Create a list to store processed data
        processed_data = []
        
        for entry in roster_entries:
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
        
        # Check if Position column exists before applying function
        if "Position" in df.columns:
            df["Position"] = df["Position"].apply(get_position_name)
        else:
            st.error("Position column not found in DataFrame!")
            st.write("Available columns:", list(df.columns))
        
        if "NFL Team" in df.columns:
            df["NFL Team"] = df["NFL Team"].apply(get_nfl_team_name)
        else:
            st.error("NFL Team column not found in DataFrame!")
        
        if "Lineup Slot" in df.columns:
            df["Lineup Slot"] = df["Lineup Slot"].apply(get_lineup_slot_name)
        else:
            st.error("Lineup Slot column not found in DataFrame!")
        
        if "SLOT" in df.columns:
            df["SLOT"] = df["SLOT"].apply(get_lineup_slot_name)
        else:
            st.error("SLOT column not found in DataFrame!")
        
        # Format percentages
        df["%ST"] = df["%ST"].apply(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else str(x))
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
            starters_display = starters_display.rename(columns={
                "SLOT": "SLOT",
                "Player": "Player",
                "opp": "opp",
                "STATUS": "STATUS",
                "This Week Projection": "This Week Projection",
                "OPRK": "OPRK",
                "%ST": "%ST",
                "%ROST": "%ROST",
                "+/-": "+/-",
                "FPTS": "FPTS",
                "avg": "avg",
                "LAST": "LAST"
            })
            st.dataframe(starters_display, use_container_width=True, hide_index=True)
        
        # Display bench
        if not bench.empty:
            st.write("**Bench**")
            # Fix: Remove the duplicate "proj" column reference
            bench_display = bench[["SLOT", "Player", "opp", "STATUS", "This Week Projection", "OPRK", "%ST", "%ROST", "+/-", "FPTS", "avg", "LAST"]].copy()
            bench_display = bench_display.rename(columns={
                "SLOT": "SLOT",
                "Player": "Player",
                "opp": "opp",
                "STATUS": "STATUS",
                "This Week Projection": "This Week Projection",
                "OPRK": "OPRK",
                "%ST": "%ST",
                "%ROST": "%ROST",
                "+/-": "+/-",
                "FPTS": "FPTS",
                "avg": "avg",
                "LAST": "LAST"
            })
            st.dataframe(bench_display, use_container_width=True, hide_index=True)
        
        # Display the detailed roster dataframe
        st.subheader("📋 Detailed Roster Data")
        detailed_df = df[["Player Name", "Position", "NFL Team", "Injury Status", "Lineup Slot", "Fantasy Points", "Rushing Yards", "Rushing TDs", "Receiving Yards", "Receiving TDs", "Passing Yards", "Passing TDs", "Interceptions", "Percent Owned", "Average Draft Position"]].copy()
        st.dataframe(detailed_df, use_container_width=True)
        
        # Add some filters and analysis
        st.subheader("🔍 Roster Analysis")
        
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
        
        # Show players by lineup slot
        st.subheader("🏃‍♂️ Players by Lineup Slot")
        slot_breakdown = df.groupby("Lineup Slot").agg({
            "Player Name": list,
            "Fantasy Points": "sum"
        }).reset_index()
        st.dataframe(slot_breakdown, use_container_width=True)
        
        # Show top performers
        st.subheader("⭐ Top Performers (Fantasy Points)")
        top_performers = df.nlargest(5, "Fantasy Points")[["Player Name", "Position", "Fantasy Points"]]
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
            st.subheader("🏆 Current Week Matchup")
            matchup = roster_data["current_matchup"]
            st.write(f"**Week {matchup.get('matchupPeriodId', 'Unknown')} Matchup**")
            st.json(matchup)
        
    else:
        st.error("No roster data found. Please check your ESPN API connection.")
        
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
"""
Fantasy Football Dashboard with Team Matchup and AI Chat
"""

import streamlit as st
import requests as req
import pandas as pd
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = "https://ai-fantasy-football.onrender.com"

# Fallback to localhost for development
if not os.getenv("PRODUCTION"):
    API_BASE_URL = "http://localhost:8000"

# Set page config
st.set_page_config(
    page_title="Fantasy Football Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for both interfaces
st.markdown("""
<style>
.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 15px 15px 5px 15px;
    margin: 10px 0;
    margin-left: 20%;
}

.assistant-message {
    background: #f8f9fa;
    color: #333;
    padding: 15px;
    border-radius: 15px 15px 15px 5px;
    margin: 10px 0;
    margin-right: 20%;
    border-left: 4px solid #667eea;
}

.tool-indicator {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    color: white;
    padding: 8px 15px;
    border-radius: 20px;
    margin: 5px 0;
    font-size: 14px;
    font-weight: bold;
    display: inline-block;
}

.streaming-cursor {
    animation: blink 1s infinite;
    color: #667eea;
    font-weight: bold;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

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
</style>
""", unsafe_allow_html=True)

# Sidebar with assistant info and controls
with st.sidebar:
    st.title("🤖 Fantasy AI Assistant")
    
    st.markdown("""
    **Your AI-powered fantasy football expert!**
    
    I can help you with:
    - 🎯 Lineup optimization
    - ⚡ Start/sit decisions  
    - 🔍 Waiver wire analysis
    - 🤝 Trade opportunities
    
    Just ask me anything about your fantasy team!
    """)
    
    # Usage monitoring and rate limiting
    st.markdown("---")
    st.subheader("💰 API Usage Monitor")
    
    # Add refresh button for usage stats
    col1, col2 = st.columns([3, 1])
    with col2:
        refresh_usage = st.button("🔄", help="Refresh usage stats", key="refresh_usage")
    
    with col1:
        st.write("Real-time cost tracking")
    
    try:
        # Only check usage if specifically requested or on initial load
        if refresh_usage or "usage_data" not in st.session_state:
            with st.spinner("Loading usage data..."):
                # Get usage stats from API with longer timeout
                usage_response = req.get(f"{API_BASE_URL}/usage/stats", timeout=15)
                if usage_response.status_code == 200:
                    st.session_state.usage_data = usage_response.json()
                else:
                    st.session_state.usage_data = None
        
        # Display cached usage data
        if "usage_data" in st.session_state and st.session_state.usage_data:
            usage_data = st.session_state.usage_data
            
            if usage_data.get("rate_limiting_enabled"):
                current_usage = usage_data.get("current_hourly_usage", 0)
                hourly_limit = usage_data.get("hourly_limit", 10.0)
                remaining = usage_data.get("remaining_budget", 0)
                percentage = usage_data.get("percentage_used", 0)
                
                # Display usage metrics
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Hourly Usage", f"${current_usage:.3f}")
                with metric_col2:
                    st.metric("Remaining", f"${remaining:.3f}")
                
                # Progress bar
                progress_color = "🟢" if percentage < 50 else "🟡" if percentage < 80 else "🔴"
                st.progress(percentage / 100)
                st.write(f"{progress_color} {percentage:.1f}% of ${hourly_limit} limit used")
                
                # Warning if close to limit
                if percentage > 80:
                    st.warning("⚠️ Approaching usage limit!")
                elif percentage > 95:
                    st.error("🚨 Very close to usage limit!")
                
                st.info("💡 $10/hour limit prevents abuse")
                
            else:
                st.warning("⚠️ Rate limiting not enabled")
        else:
            # Fallback when API is not available
            st.info("💡 Usage tracking: API not available")
            st.write("Rate limiting active in production")
    
    except req.exceptions.Timeout:
        st.warning("⏰ Usage stats loading slowly - trying in background")
        st.info("💡 Rate limiting still active")
    
    except Exception as e:
        st.warning(f"⚠️ Usage monitor temporarily unavailable")
        st.info("💡 Rate limiting still protecting costs")
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_messages = []
        st.session_state.conversation_history = []
        st.rerun()

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

@st.cache_data(ttl=60)
def get_matchup_data():
    """Get matchup data"""
    try:
        response = req.get(f"{API_BASE_URL}/get_matchup", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching matchup: {e}")
    return None

def format_tool_response(tool_name: str, data: dict) -> str:
    """Format tool response data into readable text"""
    
    if tool_name == "lineup_optimization":
        optimal_lineup = data.get("optimal_lineup", {})
        projected_total = data.get("projected_total", 0)
        confidence = data.get("confidence_level", "Unknown")
        
        response = f"**🎯 Optimal Lineup (Projected: {projected_total:.1f} pts, Confidence: {confidence})**\n\n"
        
        for position, player_info in optimal_lineup.items():
            name = player_info.get("name", "Unknown")
            projection = player_info.get("projection", 0)
            reason = player_info.get("reason", "")
            response += f"**{position}:** {name} ({projection:.1f} pts) - {reason}\n"
        
        key_decisions = data.get("key_decisions", [])
        if key_decisions:
            response += "\n**🔑 Key Decisions:**\n"
            for decision in key_decisions:
                response += f"• {decision}\n"
        
        return response
    
    elif tool_name == "waiver_wire":
        top_recs = data.get("top_recommendations", [])
        if not top_recs:
            return "**🔍 No strong waiver wire targets found right now.**"
        
        response = "**🏆 Top Waiver Wire Targets:**\n\n"
        
        for i, rec in enumerate(top_recs[:5]):
            priority = rec.get("priority", "Medium")
            priority_icon = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
            
            name = rec.get("player_name", "Unknown")
            position = rec.get("position", "UNK")
            team = rec.get("nfl_team", "UNK")
            projection = rec.get("projected_value", 0)
            reasoning = rec.get("reasoning", "")
            
            response += f"{priority_icon} **{name}** ({position}) - {team}\n"
            response += f"   📈 Projection: {projection:.1f} pts\n"
            response += f"   💡 {reasoning}\n\n"
        
        return response
    
    elif tool_name == "trade_analysis":
        trade_targets = data.get("trade_targets", [])
        if not trade_targets:
            return "**🤝 No realistic trade opportunities found at this time.**"
        
        response = "**🎯 Recommended Trade Opportunities:**\n\n"
        
        for i, target in enumerate(trade_targets[:3]):
            team_name = target.get("target_team", "Unknown Team")
            proposal = target.get("trade_proposal", {})
            confidence = target.get("confidence", "Unknown")
            reasoning = target.get("trade_reasoning", "")
            
            give = proposal.get("give", [])
            receive = proposal.get("receive", [])
            
            confidence_icon = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
            
            response += f"**Trade {i+1}: {team_name}** {confidence_icon}\n"
            if give and receive:
                response += f"📤 **Give:** {', '.join(give)}\n"
                response += f"📥 **Receive:** {', '.join(receive)}\n"
            response += f"💭 **Reasoning:** {reasoning}\n\n"
        
        return response
    
    elif tool_name == "injury_analysis":
        summary = data.get("summary", {})
        healthy_players = data.get("healthy_players", [])
        questionable_players = data.get("questionable_players", [])
        doubtful_players = data.get("doubtful_players", [])
        out_players = data.get("out_players", [])
        ir_players = data.get("ir_players", [])
        
        response = f"**🏥 Injury Report Summary:**\n\n"
        response += f"📊 **Team Health:** {summary.get('healthy_count', 0)}/{summary.get('total_players', 0)} players healthy ({100 - summary.get('injury_percentage', 0):.0f}%)\n\n"
        
        if questionable_players:
            response += "**🟡 QUESTIONABLE:**\n"
            for player in questionable_players:
                response += f"• {player['name']} ({player['position']}) - {player['nfl_team']}\n"
            response += "\n"
        
        if doubtful_players:
            response += "**🔴 DOUBTFUL:**\n"
            for player in doubtful_players:
                response += f"• {player['name']} ({player['position']}) - {player['nfl_team']}\n"
            response += "\n"
        
        if out_players:
            response += "**❌ OUT:**\n"
            for player in out_players:
                response += f"• {player['name']} ({player['position']}) - {player['nfl_team']}\n"
            response += "\n"
        
        if ir_players:
            response += "**🏥 INJURY RESERVE:**\n"
            for player in ir_players:
                response += f"• {player['name']} ({player['position']}) - {player['nfl_team']}\n"
            response += "\n"
        
        if not questionable_players and not doubtful_players and not out_players and not ir_players:
            response += "✅ **Great news! All your players are currently healthy.**\n\n"
        
        # Show web search results if available
        web_results = data.get("web_search_results", [])
        if web_results:
            response += "**📰 Latest Injury News:**\n"
            for result in web_results:
                response += f"{result.get('results', 'No additional news found')}\n"
        
        return response
    
    return None

def process_user_message(message: str):
    """Process a user message with improved response and timeout handling"""
    # Add user message to chat
    st.session_state.chat_messages.append({"role": "user", "content": message})
    
    try:
        # Check rate limits if enabled
        try:
            from rate_limiter import rate_limiter
            can_proceed, cost, reason = rate_limiter.can_make_request("gpt-4o", 1000, 500)
            if not can_proceed:
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": f"🚫 Rate Limit Exceeded: {reason}"
                })
                st.rerun()
                return
        except ImportError:
            pass  # No rate limiting
        
        # Show progress indicator with specific timeout for different operations
        operation_timeouts = {
            "trade": 180,      # 3 minutes for trade analysis
            "lineup": 120,     # 2 minutes for lineup optimization
            "optimize": 120,   # 2 minutes for lineup optimization
            "waiver": 150,     # 2.5 minutes for waiver analysis
            "injury": 60       # 1 minute for injury reports
        }
        
        # Determine timeout based on message content
        timeout = 180  # Default 3 minutes
        for keyword, specific_timeout in operation_timeouts.items():
            if keyword in message.lower():
                timeout = specific_timeout
                break
        
        with st.spinner(f"🤖 Analyzing your request... (max {timeout//60} min)"):
            # Make API call with appropriate timeout
            response = req.post(
                f"{API_BASE_URL}/chat/enhanced",
                json={
                    "message": message,
                    "conversation_history": st.session_state.conversation_history,
                    "league_context": {
                        "scoring": "0.5 PPR",
                        "league_size": 12,
                        "season": 2025
                    }
                },
                timeout=timeout
            )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                # Add tool indicators and show them being called
                tool_calls = result.get("tool_calls", [])
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "Unknown")
                    
                    # Show which tool is being called
                    tool_display_names = {
                        "optimize_lineup": "🎯 Lineup Optimizer",
                        "compare_players": "⚡ Player Comparison", 
                        "analyze_waiver_wire": "🔍 Waiver Wire Scout",
                        "analyze_trade_opportunities": "🤝 Trade Analyzer"
                    }
                    
                    display_name = tool_display_names.get(tool_name, f"🔧 {tool_name}")
                    st.session_state.chat_messages.append({
                        "role": "tool",
                        "tool": display_name
                    })
                
                # Add AI response
                ai_response = result.get("response", "I couldn't process that request.")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                # Process enhanced data from actual tools
                enhanced_data = result.get("enhanced_data", [])
                for tool_data in enhanced_data:
                    tool_name = tool_data.get("tool")
                    data = tool_data.get("data")
                    error = tool_data.get("error")
                    
                    if error:
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": f"❌ Tool Error ({tool_name}): {error}"
                        })
                    elif data and data.get("status") == "success":
                        formatted_response = format_tool_response(tool_name, data)
                        if formatted_response:
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": formatted_response
                            })
                
                # Update conversation history
                st.session_state.conversation_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ai_response}
                ])
                
            else:
                error_msg = result.get("message", "Unknown error")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {error_msg}"
                })
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"❌ API Error: {response.status_code}"
            })
    
    except req.exceptions.Timeout:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "⏰ Request timed out. The AI analysis is taking too long. Please try a simpler question or try again later."
        })
    
    except Exception as e:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"❌ Connection Error: {str(e)}"
        })
    
    # Rerun to display new messages
    st.rerun()

# Main content starts here
st.title("🏈 Fantasy Football Dashboard")

# Get and display team matchup
matchup_data = get_matchup_data()

if matchup_data:
    my_team = matchup_data["my_team"]
    opponent_team = matchup_data["opponent_team"]
    
    # Calculate projections
    my_projected_total = sum(player["projection"] for player in my_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
    opponent_projected_total = sum(player["projection"] for player in opponent_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
    
    # Display matchup using Streamlit columns (simpler approach)
    st.markdown("### 🏈 Current Matchup")
    
    # Create three columns for the matchup display
    team1_col, vs_col, team2_col = st.columns([2, 1, 2])
    
    with team1_col:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        ">
            <h2 style="margin: 0; color: white;">{my_team["team_name"]}</h2>
            <div style="font-size: 18px; margin: 5px 0;">{my_team["record"]}</div>
            <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">{my_projected_total:.0f}</div>
            <div style="font-size: 14px; opacity: 0.8;">Projected Points</div>
        </div>
        """, unsafe_allow_html=True)
    
    with vs_col:
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 40px 0;
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        ">
            VS
        </div>
        """, unsafe_allow_html=True)
    
    with team2_col:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        ">
            <h2 style="margin: 0; color: white;">{opponent_team["team_name"]}</h2>
            <div style="font-size: 18px; margin: 5px 0;">{opponent_team["record"]}</div>
            <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">{opponent_projected_total:.0f}</div>
            <div style="font-size: 14px; opacity: 0.8;">Projected Points</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display roster tables with position comparisons
    def compare_positions(my_roster, opponent_roster):
        """Compare projected scores by position and return advantages"""
        my_positions = {}
        opp_positions = {}
        
        # Group players by position (only starters)
        for player in my_roster:
            if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23]:  # Starting lineup
                pos = player.get("position", "UNK")
                if pos not in my_positions:
                    my_positions[pos] = []
                my_positions[pos].append(player)
        
        for player in opponent_roster:
            if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23]:  # Starting lineup
                pos = player.get("position", "UNK")
                if pos not in opp_positions:
                    opp_positions[pos] = []
                opp_positions[pos].append(player)
        
        # Calculate position advantages
        position_advantages = {}
        for pos in set(list(my_positions.keys()) + list(opp_positions.keys())):
            my_total = sum(p.get("projection", 0) for p in my_positions.get(pos, []))
            opp_total = sum(p.get("projection", 0) for p in opp_positions.get(pos, []))
            
            if my_total > opp_total:
                position_advantages[pos] = "my_team"
            elif opp_total > my_total:
                position_advantages[pos] = "opponent"
            else:
                position_advantages[pos] = "tie"
        
        return position_advantages
    
    position_advantages = compare_positions(my_team["roster"], opponent_team["roster"])
    
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader(f"🏈 {my_team['team_name']} Roster")
        
        # Process my roster data with checkmarks
        my_roster_df = pd.DataFrame(my_team["roster"])
        if not my_roster_df.empty:
            my_roster_df = my_roster_df.sort_values("lineup_slot")
            
            # Add advantage column with checkmarks
            my_roster_df["Advantage"] = my_roster_df["position"].apply(
                lambda pos: "✅" if position_advantages.get(pos) == "my_team" else ""
            )
            
            # Round projections and format display
            my_roster_df["projection"] = my_roster_df["projection"].apply(lambda x: f"{x:.0f}")
            
            display_columns = ["Advantage", "position", "player_name", "projection"]
            if all(col in my_roster_df.columns for col in display_columns):
                st.dataframe(my_roster_df[display_columns], use_container_width=True, hide_index=True)
            else:
                st.dataframe(my_roster_df, use_container_width=True, hide_index=True)
    
    with right_col:
        st.subheader(f"🏈 {opponent_team['team_name']} Roster")
        
        # Process opponent roster data with checkmarks
        opponent_df = pd.DataFrame(opponent_team["roster"])
        if not opponent_df.empty:
            opponent_df = opponent_df.sort_values("lineup_slot")
            
            # Add advantage column with checkmarks
            opponent_df["Advantage"] = opponent_df["position"].apply(
                lambda pos: "✅" if position_advantages.get(pos) == "opponent" else ""
            )
            
            # Round projections and format display
            opponent_df["projection"] = opponent_df["projection"].apply(lambda x: f"{x:.0f}")
            
            display_columns = ["Advantage", "position", "player_name", "projection"]
            if all(col in opponent_df.columns for col in display_columns):
                st.dataframe(opponent_df[display_columns], use_container_width=True, hide_index=True)
            else:
                st.dataframe(opponent_df, use_container_width=True, hide_index=True)
    


# AI Chat Interface Section
st.markdown("---")

# Check if OpenAI API key is available
if os.getenv("OPENAI_API_KEY"):
    st.success("✅ AI Ready - Chat assistant active")
else:
    st.error("❌ API Key Missing - OpenAI API key not found in .env file")

st.markdown("""
**Your AI-powered fantasy football expert!**

I can help you with:
- 🎯 Lineup optimization
- ⚡ Start/sit decisions  
- 🔍 Waiver wire analysis
- 🤝 Trade opportunities

Just ask me anything about your fantasy team!
""")

# Quick question buttons
st.markdown("### 💬 Quick Questions")
example_cols = st.columns(3)

example_questions = [
    "Optimize my lineup",
    "Find waiver wire pickups", 
    "Check injury reports"
]

for i, question in enumerate(example_questions):
    col_idx = i % 3
    with example_cols[col_idx]:
        if st.button(question, key=f"example_{i}", use_container_width=True):
            process_user_message(question)

# Manual input
st.markdown("### 💭 Ask Your Question")

# Use form for enter key functionality
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Type your fantasy football question and press Enter...",
        placeholder="e.g., 'I want to trade Nick Chubb, who should I target?' or 'Who should I start this week?'",
        key="chat_input_form"
    )
    
    submitted = st.form_submit_button("Send 🚀", use_container_width=True)

# Clear chat button outside the form
if st.button("Clear Chat 🗑️", key="clear_chat", use_container_width=True):
    st.session_state.chat_messages = []
    st.session_state.conversation_history = []
    st.rerun()

# Process the form submission (moved before chat display to prevent duplication)
if submitted and user_input.strip():
    process_user_message(user_input.strip())

# Display chat messages BELOW the input (proper flow)
st.markdown("---")
st.markdown("### 💬 Chat History")

chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "tool":
            st.markdown(f'<div class="tool-indicator">🔧 Using tool: {message.get("tool", "Unknown")}</div>', unsafe_allow_html=True)



# Footer
st.markdown("---")
st.markdown("*Powered by ESPN Fantasy API + OpenAI GPT-4* 🚀")

import streamlit as st
import requests as req
import pandas as pd
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Suppress verbose logging that might show HTML content
logging.getLogger().setLevel(logging.ERROR)

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

# API Configuration - auto-detect environment
if os.getenv("STREAMLIT_CLOUD") or os.getenv("RENDER"):
    # Production environment
    API_BASE_URL = "https://ai-fantasy-football.onrender.com"
else:
    # Local development environment
    API_BASE_URL = "http://localhost:8000"

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

# Set page config
st.set_page_config(
    page_title="Fantasy Football Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling including chat
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
</style>
""", unsafe_allow_html=True)

# Chat helper functions
def process_chat_message(message: str):
    """Process a user message and get AI response"""
    # Add user message to chat
    st.session_state.chat_messages.append({"role": "user", "content": message})
    
    try:
        # Check rate limits if enabled
        if RATE_LIMITING_ENABLED:
            can_proceed, cost, reason = rate_limiter.can_make_request("gpt-4o", 1000, 500)
            if not can_proceed:
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": f"🚫 Rate Limit Exceeded: {reason}"
                })
                st.rerun()
                return
            else:
                st.info(f"💰 Estimated cost: ~${cost:.3f}")
        
        # Make API call to enhanced chat endpoint
        with st.spinner("🤖 AI is thinking..."):
            response = req.post(
                f"{API_BASE_URL}/chat/enhanced",
                json={
                    "message": message,
                    "conversation_history": st.session_state.conversation_history
                },
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                # Add tool indicators
                tool_calls = result.get("tool_calls", [])
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "Unknown")
                    st.session_state.chat_messages.append({
                        "role": "tool",
                        "tool": tool_name
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
                        formatted_response = format_chat_tool_response(tool_name, data)
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
                
                # Record usage if rate limiting enabled
                if RATE_LIMITING_ENABLED and result.get("usage"):
                    rate_limiter.record_usage(result["usage"])
                
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
    
    except Exception as e:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"❌ Connection Error: {str(e)}"
        })
    
    # Rerun to display new messages
    st.rerun()

def format_chat_tool_response(tool_name: str, data: dict) -> str:
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
    
    return None

# Main content
try:
    matchup_data = get_matchup()
    
    if matchup_data:
        my_team = matchup_data["my_team"]
        opponent_team = matchup_data["opponent_team"]
        
        # Calculate projections and stats - include FLEX positions
        my_projected_total = sum(player["projection"] for player in my_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        opponent_projected_total = sum(player["projection"] for player in opponent_team["roster"] if player["lineup_slot"] < 20 or player["lineup_slot"] in [22, 23])
        
        # Enhanced ESPN-style header with dynamic data
        matchup_html = f"""
        <div class="matchup-container">
            <div class="espn-matchup-header">
                <div class="espn-team-left">
                    <div class="espn-team-logo">{my_team["team_name"][:2].upper()}</div>
                    <div class="espn-team-info">
                        <h2>{my_team["team_name"]}</h2>
                        <div class="record">{my_team["record"]}</div>
                        <div class="manager">{my_team.get("manager", "Unknown Manager")}</div>
                    </div>
                </div>
                
                <div class="espn-projected-total">
                    <div class="espn-score-large">{my_projected_total:.1f}</div>
                    <div class="espn-vs">VS</div>
                    <div class="espn-score-large">{opponent_projected_total:.1f}</div>
                    <div class="espn-projected-label">Projected Points</div>
                </div>
                
                <div class="espn-team-right">
                    <div class="espn-team-logo">{opponent_team["team_name"][:2].upper()}</div>
                    <div class="espn-team-info">
                        <h2>{opponent_team["team_name"]}</h2>
                        <div class="record">{opponent_team["record"]}</div>
                        <div class="manager">{opponent_team.get("manager", "Unknown Manager")}</div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Use st.html() for better HTML rendering
        try:
            st.html(matchup_html)
        except AttributeError:
            # Fallback for older Streamlit versions
            st.markdown(matchup_html, unsafe_allow_html=True)
        
        # Display roster tables side by side
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.subheader(f"🏈 {my_team['team_name']} Roster")
            roster_df = pd.DataFrame(my_team["roster"])
            if not roster_df.empty:
                # Sort by lineup slot to show starters first
                roster_df = roster_df.sort_values("lineup_slot")
                display_columns = ["position", "player_name", "nfl_team", "projection", "opponent"]
                if all(col in roster_df.columns for col in display_columns):
                    st.dataframe(roster_df[display_columns], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(roster_df, use_container_width=True, hide_index=True)
        
        with right_col:
            st.subheader(f"🏈 {opponent_team['team_name']} Roster")
            opponent_df = pd.DataFrame(opponent_team["roster"])
            if not opponent_df.empty:
                # Sort by lineup slot to show starters first
                opponent_df = opponent_df.sort_values("lineup_slot")
                display_columns = ["position", "player_name", "nfl_team", "projection", "opponent"]
                if all(col in opponent_df.columns for col in display_columns):
                    st.dataframe(opponent_df[display_columns], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(opponent_df, use_container_width=True, hide_index=True)
        
        # AI Chat Interface Section (REPLACING THE OLD AI TOOLS)
        st.markdown("---")
        
        # Header with API status
        header_col1, header_col2 = st.columns([3, 1])
        
        with header_col1:
            st.header("🤖 Fantasy Football AI Chat")
        
        with header_col2:
            # Check if OpenAI API key is available
            if os.getenv("OPENAI_API_KEY"):
                st.success("✅ AI Ready - Chat assistant active")
            else:
                st.error("❌ API Key Missing - OpenAI API key not found in .env file")
        
        # Add some spacing
        st.write("")
        
        # Chat interface setup
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
        
        # Chat interface description
        st.markdown("""
        **Your AI-powered fantasy football expert!**
        
        I can help you with:
        - 🎯 Lineup optimization
        - ⚡ Start/sit decisions  
        - 🔍 Waiver wire analysis
        - 🤝 Trade opportunities
        
        Just ask me anything about your fantasy team!
        """)
        
        # Display chat messages
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_messages:
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
                elif message["role"] == "assistant":
                    st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
                elif message["role"] == "tool":
                    st.markdown(f'<div class="tool-indicator">🔧 Using tool: {message.get("tool", "Unknown")}</div>', unsafe_allow_html=True)
        
        # Quick question buttons
        st.markdown("### 💬 Quick Questions")
        example_cols = st.columns(3)
        
        example_questions = [
            "Who should I start this week?",
            "Optimize my lineup", 
            "Find waiver wire pickups",
            "What trades should I make?",
            "Compare my players",
            "Analyze my team"
        ]
        
        for i, question in enumerate(example_questions):
            col_idx = i % 3
            with example_cols[col_idx]:
                if st.button(question, key=f"example_{i}", use_container_width=True):
                    process_chat_message(question)
        
        # Manual input
        st.markdown("### 💭 Ask Your Question")
        user_input = st.text_input(
            "Type your fantasy football question...",
            placeholder="e.g., 'Who should I start this week?' or 'Find me some trade targets'",
            key="chat_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Send 🚀", key="send_button") and user_input.strip():
                process_chat_message(user_input.strip())
        
        with col2:
            if st.button("Clear Chat 🗑️", key="clear_chat"):
                st.session_state.chat_messages = []
                st.session_state.conversation_history = []
                st.rerun()
    
    else:
        st.warning("No matchup data available. Showing roster only.")

except Exception as e:
    st.error(f"Error fetching matchup data: {str(e)}")
    st.info("Continuing with roster display...")

# Footer
st.markdown("---")
st.markdown("*Powered by ESPN Fantasy API + OpenAI GPT-4* 🚀")

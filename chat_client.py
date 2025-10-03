"""
Fantasy Football Chat Interface
Streamlit app with chat-based AI assistant
"""

import streamlit as st
import requests as req
import json
import time
from datetime import datetime
from typing import Dict, List, Generator
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

# API Configuration
API_BASE_URL = "https://ai-fantasy-football.onrender.com"

# Fallback to localhost for development
if not os.getenv("PRODUCTION"):
    API_BASE_URL = "http://localhost:8000"

# Set page config
st.set_page_config(
    page_title="Fantasy Football AI Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat interface
st.markdown("""
<style>
.chat-container {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

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
    padding: 10px 15px;
    border-radius: 20px;
    margin: 5px 0;
    font-size: 14px;
    font-weight: bold;
    display: inline-block;
}

.streaming-text {
    border-right: 2px solid #667eea;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { border-color: #667eea; }
    51%, 100% { border-color: transparent; }
}

.chat-input {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 80%;
    max-width: 800px;
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 1000;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

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
    
    # Rate limiting info
    if RATE_LIMITING_ENABLED:
        st.markdown("---")
        st.subheader("💰 Usage Tracking")
        display_usage_dashboard()
        
        with st.expander("💡 Cost Information"):
            show_feature_costs()
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()
    
    # Show example questions
    st.markdown("---")
    st.subheader("💬 Example Questions")
    
    example_questions = [
        "Who should I start this week?",
        "Optimize my lineup",
        "Find me good waiver wire pickups",
        "What trades should I make?",
        "Compare Mahomes vs Allen this week",
        "Who has the best matchup?"
    ]
    
    for question in example_questions:
        if st.button(f"💭 {question}", key=f"example_{question}", use_container_width=True):
            # Add to messages and trigger processing
            st.session_state.messages.append({"role": "user", "content": question})
            st.rerun()

# Main chat interface
st.title("🏈 Fantasy Football AI Chat")

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "tool":
            st.markdown(f'<div class="tool-indicator">🔧 Using tool: {message.get("tool", "Unknown")}</div>', unsafe_allow_html=True)

# Chat input
with st.container():
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    
    # Use columns for input and send button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about your fantasy team...",
            key="chat_input",
            placeholder="e.g., 'Who should I start this week?' or 'Find me some trade targets'",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send 🚀", key="send_button", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Process new message
if send_button and user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Clear input by rerunning
    st.rerun()

def process_chat_message(message: str):
    """Process a chat message with streaming response"""
    
    # Create placeholder for streaming response
    response_placeholder = st.empty()
    tool_placeholder = st.empty()
    
    try:
        # Make request to chat API
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
                # Display the response
                assistant_response = result.get("response", "")
                tool_calls = result.get("tool_calls", [])
                enhanced_data = result.get("enhanced_data", [])
                
                # Add tool indicators if any tools were called
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "Unknown")
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool": tool_name
                    })
                
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": assistant_response
                })
                
                # Display enhanced data from actual tool calls
                if enhanced_data:
                    for tool_data in enhanced_data:
                        tool_name = tool_data.get("tool")
                        data = tool_data.get("data")
                        error = tool_data.get("error")
                        
                        if error:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"❌ Error with {tool_name}: {error}"
                            })
                        elif data and data.get("status") == "success":
                            # Format the enhanced data nicely
                            formatted_response = format_tool_response(tool_name, data)
                            if formatted_response:
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": formatted_response
                                })
                
                # Update conversation history
                st.session_state.conversation_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": assistant_response}
                ])
                
                # Record usage if rate limiting enabled
                if RATE_LIMITING_ENABLED and result.get("usage"):
                    rate_limiter.record_usage(result["usage"])
                
            else:
                error_msg = result.get("message", "Unknown error occurred")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {error_msg}"
                })
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ API Error: {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Connection Error: {str(e)}"
        })
    
    # Rerun to display new messages
    st.rerun()

def format_tool_response(tool_name: str, data: Dict) -> str:
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
            response += f"📤 **Give:** {', '.join(give)}\n"
            response += f"📥 **Receive:** {', '.join(receive)}\n"
            response += f"💭 **Reasoning:** {reasoning}\n\n"
        
        return response
    
    return None

# Handle streaming response for the latest user message
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    latest_message = st.session_state.messages[-1]["content"]
    
    # Check rate limits if enabled
    if RATE_LIMITING_ENABLED:
        can_proceed, cost, reason = rate_limiter.can_make_request("gpt-4o", 1000, 500)
        if not can_proceed:
            st.error(f"🚫 **Rate Limit Exceeded**\n\n{reason}")
            st.info("💡 **Tip:** Try again later or use simpler queries to reduce costs.")
            # Add error message to chat
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Sorry, I've hit the rate limit. {reason}"
            })
        else:
            # Show estimated cost
            st.info(f"💰 Estimated cost: ~${cost:.3f}")
            
            # Process the message
            process_chat_message(latest_message)
    else:
        # No rate limiting, process directly
        process_chat_message(latest_message)

# Auto-scroll to bottom (JavaScript injection)
st.markdown("""
<script>
setTimeout(function() {
    var chatContainer = window.parent.document.querySelector('.main');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}, 100);
</script>
""", unsafe_allow_html=True)

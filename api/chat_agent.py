"""
Fantasy Football Chat Agent
Handles chat-based interactions with tool calling for AI features
"""

import json
import os
from typing import List, Dict, Optional, Generator, Tuple
from openai import OpenAI
from dotenv import load_dotenv

# Import existing AI services
from .ai_services import FantasyAIService

load_dotenv()

class FantasyChatAgent:
    """Chat agent that uses existing AI services as tools via function calling"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        # Initialize the existing AI service
        self.ai_service = FantasyAIService()
        
        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "optimize_lineup",
                    "description": "Analyze roster and suggest optimal starting lineup for the current week with AI analysis of projections, matchups, and current NFL information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_opponent_context": {
                                "type": "boolean",
                                "description": "Whether to include opponent roster context in the analysis",
                                "default": True
                            }
                        }
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "compare_players",
                    "description": "Compare two players and recommend which one to start based on current NFL information, matchups, and projections",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "player1_name": {
                                "type": "string",
                                "description": "Name of the first player to compare"
                            },
                            "player2_name": {
                                "type": "string", 
                                "description": "Name of the second player to compare"
                            }
                        },
                        "required": ["player1_name", "player2_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_waiver_wire", 
                    "description": "Analyze available waiver wire players and recommend the best pickups to improve the team",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_players_per_position": {
                                "type": "integer",
                                "description": "Maximum number of players to analyze per position",
                                "default": 10
                            },
                            "include_league_context": {
                                "type": "boolean",
                                "description": "Whether to include league context in the analysis",
                                "default": True
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_trade_opportunities",
                    "description": "Analyze roster and suggest beneficial trade opportunities with other teams in the league",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "include_league_rosters": {
                                "type": "boolean",
                                "description": "Whether to include other teams' rosters in the analysis",
                                "default": True
                            },
                            "focus_positions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific positions to focus on for trades (e.g., ['RB', 'WR'])",
                            "default": None
                            },
                    "target_player": {
                        "type": "string",
                        "description": "Specific player the user wants to trade (e.g., 'Nick Chubb')",
                        "default": None
                    }
                        }
                    }
                }
            }
        ]
    
    def chat_stream(self, message: str, conversation_history: List[Dict] = None) -> Generator[Tuple[str, Optional[str], Optional[Dict]], None, None]:
        """
        Stream chat responses with tool calling
        
        Args:
            message: User's message
            conversation_history: Previous messages in the conversation
            
        Yields:
            Tuple of (content, tool_name, tool_result)
        """
        if not self.client:
            yield "❌ OpenAI client not available. Please check your API key.", None, None
            return
        
        try:
            # Build messages list
            messages = []
            
            # System message
            messages.append({
                "role": "system", 
                "content": """You are a fantasy football expert assistant with access to advanced AI analysis tools.

LEAGUE CONTEXT (ALWAYS CONSIDER):
- **12-team league** - Higher scarcity, deeper rosters matter more
- **0.5 PPR scoring** - Half-point per reception, favors pass-catching RBs and high-target WRs
- **Current season: 2025** - Use up-to-date player information and projections

ANALYSIS APPROACH:
- Always consider the user's current roster depth when making recommendations
- For trade analysis: Look at their roster to identify surplus positions and needs
- For lineup decisions: Factor in 0.5 PPR scoring when comparing players
- For waiver wire: Prioritize based on roster gaps and bye week coverage
- Consider 12-team league scarcity - even mediocre players have value

You help users with:
- Lineup optimization and start/sit decisions (consider 0.5 PPR scoring)
- Player comparisons and matchup analysis  
- Waiver wire recommendations (factor in 12-team scarcity)
- Trade opportunity analysis (analyze roster depth and needs)

When users ask questions, determine if you need to use any of your tools to provide accurate, data-driven advice. Use the tools to get current analysis rather than making assumptions.

SPECIFIC INSTRUCTIONS:
- For trade questions: ALWAYS extract the specific player name from the user's request
- When user says "I want to trade Nick Chubb", you MUST pass "Nick Chubb" as the target_player parameter
- The trade analysis tool will have access to their full roster and league data automatically
- When analyzing players: Remember 0.5 PPR means pass-catching backs and target-heavy WRs get boost
- Consider positional scarcity in 12-team format when making recommendations
- Be specific about WHY a trade/pickup/start makes sense given their roster construction
- NEVER say you need more information - the tools have access to all roster and league data

Always explain what tool you're using and why. Provide actionable advice based on the tool results."""
            })
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Create streaming chat completion with tools
            stream = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                stream=True,
                temperature=0.3
            )
            
            # Track if we need to call tools
            tool_calls = []
            content_buffer = ""
            
            # Process the stream
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle content
                if delta.content:
                    content_buffer += delta.content
                    yield delta.content, None, None
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        # Extend tool_calls list if needed
                        while len(tool_calls) <= tool_call_delta.index:
                            tool_calls.append({
                                "id": "",
                                "type": "function", 
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        tool_call = tool_calls[tool_call_delta.index]
                        
                        if tool_call_delta.id:
                            tool_call["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_call["function"]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_call["function"]["arguments"] += tool_call_delta.function.arguments
            
            # Execute any tool calls
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call["function"]["name"]:
                        yield f"\n\n🔧 **Using tool: {tool_call['function']['name']}**\n", tool_call["function"]["name"], None
                        
                        try:
                            # Execute the tool
                            result = self._execute_tool(tool_call["function"]["name"], tool_call["function"]["arguments"])
                            yield f"✅ Tool execution completed\n\n", tool_call["function"]["name"], result
                            
                            # Get follow-up response with tool results
                            messages.append({
                                "role": "assistant", 
                                "content": content_buffer,
                                "tool_calls": [tool_call]
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"], 
                                "content": json.dumps(result)
                            })
                            
                            # Stream the follow-up response
                            follow_up_stream = self.client.chat.completions.create(
                                model="gpt-4o",
                                messages=messages,
                                stream=True,
                                temperature=0.3
                            )
                            
                            for chunk in follow_up_stream:
                                if chunk.choices[0].delta.content:
                                    yield chunk.choices[0].delta.content, None, None
                                    
                        except Exception as e:
                            yield f"❌ Error executing tool {tool_call['function']['name']}: {str(e)}\n", tool_call["function"]["name"], None
                            
        except Exception as e:
            yield f"❌ Error in chat: {str(e)}", None, None
    
    def _execute_tool(self, tool_name: str, arguments: str) -> Dict:
        """Execute a tool function and return results"""
        try:
            args = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid tool arguments"}
        
        try:
            if tool_name == "optimize_lineup":
                # This would need roster data - we'll handle this via API endpoints
                return {"status": "success", "message": "Lineup optimization requires roster data - please use via API endpoint"}
                
            elif tool_name == "compare_players":
                player1_name = args.get("player1_name")
                player2_name = args.get("player2_name")
                if not player1_name or not player2_name:
                    return {"status": "error", "message": "Both player names are required"}
                
                # This would need player data - we'll handle this via API endpoints  
                return {"status": "success", "message": f"Player comparison for {player1_name} vs {player2_name} requires roster data - please use via API endpoint"}
                
            elif tool_name == "analyze_waiver_wire":
                # This would need waiver wire data - we'll handle this via API endpoints
                return {"status": "success", "message": "Waiver wire analysis requires league data - please use via API endpoint"}
                
            elif tool_name == "analyze_trade_opportunities":
                # This would need league roster data - we'll handle this via API endpoints
                return {"status": "success", "message": "Trade analysis requires league data - please use via API endpoint"}
                
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Tool execution failed: {str(e)}"}
    
    def chat_complete(self, message: str, conversation_history: List[Dict] = None) -> Tuple[str, List[Dict]]:
        """
        Complete chat interaction (non-streaming) with tool calling
        
        Args:
            message: User's message
            conversation_history: Previous messages in the conversation
            
        Returns:
            Tuple of (response_content, tool_calls_made)
        """
        response_parts = []
        tool_calls_made = []
        
        for content, tool_name, tool_result in self.chat_stream(message, conversation_history):
            if tool_name:
                tool_calls_made.append({"tool": tool_name, "result": tool_result})
            response_parts.append(content)
        
        return "".join(response_parts), tool_calls_made

"""
Configuration management for ESPN Fantasy Football API
Handles environment variables safely for different deployment environments
"""
import os
from urllib.parse import unquote

def get_espn_config():
    """
    Get ESPN configuration from environment variables
    Returns None values if not configured (for Streamlit Cloud compatibility)
    """
    # Get environment variables
    espn_s2_encoded = os.getenv("ESPN_S2_ENCODED")
    espn_auth = os.getenv("ESPN_AUTH")
    swid = os.getenv("SWID")
    
    # Handle ESPN_S2 with fallback to encoded version
    espn_s2 = os.getenv("ESPN_S2")
    if not espn_s2 and espn_s2_encoded:
        try:
            espn_s2 = unquote(espn_s2_encoded)
        except (TypeError, ValueError):
            espn_s2 = None
    
    # League configuration
    league_id = os.getenv("LEAGUE_ID")
    team_id = os.getenv("TEAM_ID")
    season = int(os.getenv("SEASON", 2025))
    
    # OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    return {
        "ESPN_S2": espn_s2,
        "ESPN_S2_ENCODED": espn_s2_encoded,
        "ESPN_AUTH": espn_auth,
        "SWID": swid,
        "LEAGUE_ID": league_id,
        "TEAM_ID": team_id,
        "SEASON": season,
        "OPENAI_API_KEY": openai_api_key,
        "configured": bool(espn_s2 and espn_auth and swid and league_id and team_id)
    }

def check_configuration():
    """
    Check if all required environment variables are configured
    Returns tuple (is_configured, missing_vars)
    """
    config = get_espn_config()
    
    required_vars = ["ESPN_S2", "ESPN_AUTH", "SWID", "LEAGUE_ID", "TEAM_ID"]
    missing = []
    
    for var in required_vars:
        if not config.get(var):
            missing.append(var)
    
    return len(missing) == 0, missing

def get_configuration_message():
    """
    Get a user-friendly message about configuration status
    """
    is_configured, missing = check_configuration()
    
    if is_configured:
        return "✅ All ESPN credentials configured"
    else:
        missing_str = ", ".join(missing)
        return f"⚠️ Missing configuration: {missing_str}. Please set these environment variables."
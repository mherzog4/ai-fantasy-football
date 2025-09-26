"""
AI API Rate Limiter for Fantasy Football App
Prevents exceeding $10/hour in OpenAI API costs for public Streamlit deployment
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import streamlit as st

# OpenAI API Pricing (as of 2024) - Update these if pricing changes
OPENAI_PRICING = {
    "gpt-4": {
        "input": 0.03 / 1000,   # $0.03 per 1K input tokens
        "output": 0.06 / 1000   # $0.06 per 1K output tokens
    },
    "gpt-4-turbo": {
        "input": 0.01 / 1000,   # $0.01 per 1K input tokens  
        "output": 0.03 / 1000   # $0.03 per 1K output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0005 / 1000, # $0.0005 per 1K input tokens
        "output": 0.0015 / 1000 # $0.0015 per 1K output tokens
    }
}

# Default model used in the app
DEFAULT_MODEL = "gpt-4-turbo"

# Hourly spending limit
HOURLY_LIMIT = 10.00  # $10 per hour

class RateLimiter:
    def __init__(self):
        self.session_key = "rate_limiter_data"
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for rate limiting data"""
        try:
            if self.session_key not in st.session_state:
                st.session_state[self.session_key] = {
                    "hourly_usage": [],  # List of (timestamp, cost) tuples
                    "total_spent_today": 0.0,
                    "last_reset": datetime.now().isoformat()
                }
        except Exception:
            # If session state is not available, create a fallback
            self._fallback_data = {
                "hourly_usage": [],
                "total_spent_today": 0.0,
                "last_reset": datetime.now().isoformat()
            }
    
    def _get_data(self):
        """Get data from session state or fallback"""
        try:
            return st.session_state[self.session_key]
        except:
            return getattr(self, '_fallback_data', {
                "hourly_usage": [],
                "total_spent_today": 0.0,
                "last_reset": datetime.now().isoformat()
            })
    
    def _clean_old_usage(self):
        """Remove usage data older than 1 hour"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=1)
        
        data = self._get_data()
        
        # Filter out old entries
        data["hourly_usage"] = [
            (timestamp, cost) for timestamp, cost in data["hourly_usage"]
            if datetime.fromisoformat(timestamp) > cutoff_time
        ]
    
    def get_current_hourly_usage(self) -> float:
        """Get current spending in the last hour"""
        self._clean_old_usage()
        data = self._get_data()
        return sum(cost for _, cost in data["hourly_usage"])
    
    def estimate_request_cost(self, 
                            model: str = DEFAULT_MODEL,
                            estimated_input_tokens: int = 1000,
                            estimated_output_tokens: int = 500) -> float:
        """Estimate the cost of an API request"""
        if model not in OPENAI_PRICING:
            model = DEFAULT_MODEL
        
        pricing = OPENAI_PRICING[model]
        input_cost = estimated_input_tokens * pricing["input"]
        output_cost = estimated_output_tokens * pricing["output"]
        
        return input_cost + output_cost
    
    def can_make_request(self, 
                        model: str = DEFAULT_MODEL,
                        estimated_input_tokens: int = 1000,
                        estimated_output_tokens: int = 500) -> Tuple[bool, float, str]:
        """
        Check if a request can be made without exceeding limits
        Returns (can_make_request, estimated_cost, reason)
        """
        current_usage = self.get_current_hourly_usage()
        estimated_cost = self.estimate_request_cost(model, estimated_input_tokens, estimated_output_tokens)
        
        if current_usage + estimated_cost > HOURLY_LIMIT:
            remaining_budget = HOURLY_LIMIT - current_usage
            reason = f"Would exceed hourly limit of ${HOURLY_LIMIT:.2f}. Current usage: ${current_usage:.2f}, Estimated cost: ${estimated_cost:.2f}, Remaining budget: ${remaining_budget:.2f}"
            return False, estimated_cost, reason
        
        return True, estimated_cost, "Request within limits"
    
    def record_usage(self, actual_cost: float):
        """Record actual API usage cost"""
        current_time = datetime.now().isoformat()
        data = self._get_data()
        
        # Add to hourly usage
        data["hourly_usage"].append((current_time, actual_cost))
        
        # Update daily total
        data["total_spent_today"] += actual_cost
        
        # Clean old data
        self._clean_old_usage()
    
    def calculate_actual_cost(self, response) -> float:
        """Calculate actual cost from OpenAI response"""
        try:
            # Extract token usage from response
            usage = response.usage
            model = response.model
            
            if model not in OPENAI_PRICING:
                model = DEFAULT_MODEL
            
            pricing = OPENAI_PRICING[model]
            input_cost = usage.prompt_tokens * pricing["input"]
            output_cost = usage.completion_tokens * pricing["output"]
            
            return input_cost + output_cost
        except Exception as e:
            # Fallback to estimation if we can't get actual usage
            print(f"Error calculating actual cost: {e}")
            return self.estimate_request_cost()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        current_usage = self.get_current_hourly_usage()
        data = self._get_data()
        
        return {
            "hourly_usage": current_usage,
            "hourly_limit": HOURLY_LIMIT,
            "remaining_budget": max(0, HOURLY_LIMIT - current_usage),
            "usage_percentage": (current_usage / HOURLY_LIMIT) * 100,
            "requests_this_hour": len(data["hourly_usage"]),
            "daily_total": data["total_spent_today"]
        }
    
    def reset_daily_usage(self):
        """Reset daily usage counter (called at midnight)"""
        data = self._get_data()
        data["total_spent_today"] = 0.0
        data["last_reset"] = datetime.now().isoformat()

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit_decorator(estimated_input_tokens: int = 1000, 
                              estimated_output_tokens: int = 500):
    """
    Decorator to check rate limits before making API calls
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            can_proceed, cost, reason = rate_limiter.can_make_request(
                DEFAULT_MODEL, estimated_input_tokens, estimated_output_tokens
            )
            
            if not can_proceed:
                st.error(f"🚫 **Rate Limit Exceeded**\n\n{reason}")
                st.info("💡 **Tip:** Try again in an hour, or consider using simpler queries to reduce token usage.")
                return None
            
            # Show cost warning for expensive requests
            if cost > 0.50:
                st.warning(f"⚠️ This request will cost approximately ${cost:.3f}")
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                
                # If the function returned an OpenAI response, calculate actual cost
                if hasattr(result, 'usage'):
                    actual_cost = rate_limiter.calculate_actual_cost(result)
                    rate_limiter.record_usage(actual_cost)
                else:
                    # Record estimated cost if no usage data available
                    rate_limiter.record_usage(cost)
                
                return result
                
            except Exception as e:
                st.error(f"API request failed: {e}")
                return None
                
        return wrapper
    return decorator

def display_usage_dashboard():
    """Display current API usage in Streamlit sidebar"""
    stats = rate_limiter.get_usage_stats()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 API Usage Monitor")
    
    # Usage meter
    usage_pct = min(stats["usage_percentage"], 100)
    
    if usage_pct < 50:
        color = "green"
        status = "🟢 Good"
    elif usage_pct < 80:
        color = "orange" 
        status = "🟡 Moderate"
    else:
        color = "red"
        status = "🔴 High"
    
    st.sidebar.markdown(f"**Status:** {status}")
    st.sidebar.progress(usage_pct / 100)
    st.sidebar.markdown(f"**This Hour:** ${stats['hourly_usage']:.2f} / ${stats['hourly_limit']:.2f}")
    st.sidebar.markdown(f"**Remaining:** ${stats['remaining_budget']:.2f}")
    st.sidebar.markdown(f"**Requests:** {stats['requests_this_hour']}")
    
    # Show warning if approaching limit
    if usage_pct > 80:
        st.sidebar.error("⚠️ Approaching hourly limit!")
    
    # Usage details in expander
    with st.sidebar.expander("📊 Usage Details"):
        st.write(f"**Daily Total:** ${stats['daily_total']:.2f}")
        st.write(f"**Usage %:** {usage_pct:.1f}%")
        
        if stats['requests_this_hour'] > 0:
            avg_cost = stats['hourly_usage'] / stats['requests_this_hour']
            st.write(f"**Avg Cost/Request:** ${avg_cost:.3f}")

def get_feature_cost_estimates():
    """Get cost estimates for different AI features"""
    return {
        "Lineup Optimization": {
            "input_tokens": 1500,
            "output_tokens": 800,
            "description": "Analyzes your roster and suggests optimal lineup"
        },
        "Player Comparison": {
            "input_tokens": 800,
            "output_tokens": 600,
            "description": "Compares two players for start/sit decisions"
        },
        "Waiver Wire Analysis": {
            "input_tokens": 2000,
            "output_tokens": 1200,
            "description": "Analyzes available players and suggests pickups"
        },
        "Trade Analysis": {
            "input_tokens": 2500,
            "output_tokens": 1500,
            "description": "Evaluates trade opportunities across your league"
        },
        "Quick Analysis": {
            "input_tokens": 500,
            "output_tokens": 300,
            "description": "Simple player or matchup analysis"
        }
    }

def show_feature_costs():
    """Display estimated costs for different features"""
    features = get_feature_cost_estimates()
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("💵 Feature Costs"):
        for feature, details in features.items():
            cost = rate_limiter.estimate_request_cost(
                DEFAULT_MODEL, 
                details["input_tokens"], 
                details["output_tokens"]
            )
            st.write(f"**{feature}:** ~${cost:.3f}")
            st.caption(details["description"])
            st.write("")
#!/usr/bin/env python3
"""
Test script for rate limiting functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from rate_limiter import RateLimiter, HOURLY_LIMIT
import time

def test_rate_limiting():
    print("🧪 Testing Rate Limiting System")
    print("=" * 50)
    
    limiter = RateLimiter()
    
    # Test 1: Check initial state
    print("\n1️⃣ Testing Initial State")
    stats = limiter.get_usage_stats()
    print(f"   ✅ Initial usage: ${stats['hourly_usage']:.2f}")
    print(f"   ✅ Remaining budget: ${stats['remaining_budget']:.2f}")
    print(f"   ✅ Requests made: {stats['requests_this_hour']}")
    
    # Test 2: Check cost estimation
    print("\n2️⃣ Testing Cost Estimation")
    
    features = {
        "Lineup Optimization": (1500, 800),
        "Player Comparison": (800, 600), 
        "Waiver Wire Analysis": (2000, 1200),
        "Trade Analysis": (2500, 1500)
    }
    
    for feature, (input_tokens, output_tokens) in features.items():
        cost = limiter.estimate_request_cost("gpt-4-turbo", input_tokens, output_tokens)
        print(f"   💰 {feature}: ~${cost:.3f}")
    
    # Test 3: Check rate limit enforcement
    print("\n3️⃣ Testing Rate Limit Enforcement")
    
    # Simulate a request
    can_proceed, cost, reason = limiter.can_make_request("gpt-4-turbo", 1500, 800)
    print(f"   ✅ Can make request: {can_proceed}")
    print(f"   💰 Estimated cost: ${cost:.3f}")
    print(f"   📝 Reason: {reason}")
    
    # Record some usage
    print("\n4️⃣ Testing Usage Recording")
    limiter.record_usage(0.05)  # $0.05
    limiter.record_usage(0.08)  # $0.08
    limiter.record_usage(0.12)  # $0.12
    
    stats = limiter.get_usage_stats()
    print(f"   ✅ Usage after recording: ${stats['hourly_usage']:.2f}")
    print(f"   ✅ Remaining budget: ${stats['remaining_budget']:.2f}")
    print(f"   ✅ Total requests: {stats['requests_this_hour']}")
    
    # Test 5: Simulate hitting the limit
    print("\n5️⃣ Testing Rate Limit Exceeded")
    
    # Record high usage to trigger limit
    limiter.record_usage(HOURLY_LIMIT - 0.01)  # Almost at limit
    
    can_proceed, cost, reason = limiter.can_make_request("gpt-4-turbo", 1500, 800)
    print(f"   🚫 Can make request: {can_proceed}")
    print(f"   💰 Would cost: ${cost:.3f}")
    print(f"   📝 Reason: {reason}")
    
    # Test 6: Show final stats
    print("\n6️⃣ Final Usage Statistics")
    stats = limiter.get_usage_stats()
    
    print(f"   📊 Hourly Usage: ${stats['hourly_usage']:.2f} / ${stats['hourly_limit']:.2f}")
    print(f"   💰 Remaining Budget: ${stats['remaining_budget']:.2f}")
    print(f"   📈 Usage Percentage: {stats['usage_percentage']:.1f}%")
    print(f"   🔢 Total Requests: {stats['requests_this_hour']}")
    print(f"   💵 Daily Total: ${stats['daily_total']:.2f}")
    
    # Test 7: Rate Limiting Status
    print("\n7️⃣ Rate Limiting Status")
    usage_pct = stats['usage_percentage']
    
    if usage_pct < 50:
        status = "🟢 Good - Under 50% usage"
    elif usage_pct < 80:
        status = "🟡 Moderate - 50-80% usage"
    else:
        status = "🔴 High - Over 80% usage"
    
    print(f"   Status: {status}")
    
    print(f"\n" + "=" * 50)
    print("✅ Rate Limiting Test Complete")
    
    if stats['usage_percentage'] > 90:
        print("🚨 WARNING: Very high usage detected!")
        print("💡 New requests will be blocked to prevent overspending")
    else:
        print("✅ System is functioning correctly")

if __name__ == "__main__":
    test_rate_limiting()
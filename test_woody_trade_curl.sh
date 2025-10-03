#!/bin/bash

echo "Testing Woody Marks trade analysis..."

curl -X POST "http://localhost:8000/ai/trade_analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "target_player": "Woody Marks",
    "include_league_rosters": true
  }' | python3 -m json.tool

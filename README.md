# AI Fantasy Football Dashboard

> Reverse Engineering ESPN's Fantasy Football functionality through their undocumented API

An intelligent fantasy football assistant that combines ESPN's undocumented API with OpenAI's GPT-4 to provide AI-powered lineup optimization, trade analysis, and waiver wire recommendations.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [System Diagrams](#system-diagrams)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Development](#development)

## 🎯 Overview

This application is a comprehensive fantasy football management tool that:

- **Connects to ESPN's Private API** - Authenticates with your ESPN account to access real-time roster, matchup, and player data
- **AI-Powered Analysis** - Uses OpenAI GPT-4 to provide intelligent recommendations for lineups, trades, and waiver pickups
- **Rate-Limited for Cost Control** - Implements $10/hour spending cap to prevent excessive OpenAI API costs
- **Interactive Dashboard** - Streamlit-based UI for easy interaction with all features
- **RESTful API** - FastAPI backend for programmatic access to all functionality

### What Problems Does It Solve?

1. **Hidden API Access** - ESPN's fantasy API is undocumented and requires authentication - this app handles all the complexity
2. **Data-Driven Decisions** - Combines real-time projections, matchup data, and historical stats with AI analysis
3. **Time Savings** - Automated lineup optimization and trade analysis saves hours of manual research
4. **Cost Protection** - Built-in rate limiting ensures AI features don't exceed budget when deployed publicly
5. **League Context** - Analyzes your entire league to identify realistic trade targets and available waiver pickups

## 🏗️ Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Streamlit Dashboard (client.py) - Port 8501                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • Matchup Display                                       │  │
│  │  • Roster View                                           │  │
│  │  • AI Chat Interface                                     │  │
│  │  • Quick Action Buttons (Optimize, Trade, Waiver)       │  │
│  │  • Usage/Cost Dashboard                                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FastAPI Server (api/main.py) - Port 8000                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  REST Endpoints:                                         │  │
│  │    • GET  /get_roster                                    │  │
│  │    • GET  /get_matchup                                   │  │
│  │    • POST /ai/optimize_lineup                            │  │
│  │    • POST /ai/compare_players                            │  │
│  │    • POST /ai/trade_analysis                             │  │
│  │    • POST /ai/waiver_wire                                │  │
│  │    • POST /chat/enhanced                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└──────────┬───────────────────────────────┬──────────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│   ESPN API INTEGRATION   │   │   AI SERVICES LAYER          │
├──────────────────────────┤   ├──────────────────────────────┤
│                          │   │                              │
│  espn_api.py             │   │  ai_services.py              │
│  ┌────────────────────┐  │   │  ┌────────────────────────┐ │
│  │ • espn_get()       │  │   │  │ FantasyAIService       │ │
│  │ • get_current_week │  │   │  │  • optimize_lineup()   │ │
│  │ • Position maps    │  │   │  │  • analyze_trade()     │ │
│  │ • Team mappings    │  │   │  │  • waiver_targets()    │ │
│  └────────────────────┘  │   │  │  • compare_players()   │ │
│                          │   │  └────────────────────────┘ │
│  Authenticated Requests  │   │                              │
│  with ESPN_S2, SWID      │   │  Rate Limiter (🚦)          │
│                          │   │  ┌────────────────────────┐ │
└──────────┬───────────────┘   │  │ • $10/hour cap         │ │
           │                   │  │ • Token tracking       │ │
           ▼                   │  │ • Cost estimation      │ │
┌──────────────────────────┐   │  └────────────────────────┘ │
│   ESPN Fantasy API       │   │                              │
│   (Undocumented)         │   └──────────┬───────────────────┘
│                          │              │
│  fantasy.espn.com/       │              ▼
│  lm-api-reads.fantasy    │   ┌──────────────────────────────┐
│  .espn.com/apis/v3       │   │   OpenAI GPT-4 API           │
└──────────────────────────┘   │   (AI Analysis Engine)       │
                               └──────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      TYPICAL USER REQUEST                        │
│              "Who should I start this week?"                     │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Streamlit UI    │
         │ Parses intent   │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────────────────────────┐
         │ POST /chat/enhanced                 │
         │ Request body: { message: "..." }    │
         └────────┬────────────────────────────┘
                  │
                  ▼
         ┌─────────────────────────────────────┐
         │ Rate Limiter Check                  │
         │ • Verify < $10/hour spent           │
         │ • Estimate request cost (~$0.05)    │
         └────────┬────────────────────────────┘
                  │ ✅ Approved
                  ▼
      ┌──────────────────────────────────────────────┐
      │ Intent Detection & Tool Selection            │
      │ Keywords: "start" → Lineup Optimization      │
      └──────────┬───────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ Data Collection Phase                        │
      │ ┌─────────────────────────────────────────┐ │
      │ │ 1. ESPN API: Get Current Week           │ │
      │ │    espn_get(["mMatchupScoreLite"])      │ │
      │ │                                          │ │
      │ │ 2. ESPN API: Fetch My Roster            │ │
      │ │    espn_get(["mTeam", "mRoster",        │ │
      │ │               "mPlayer", "mSchedule"])   │ │
      │ │                                          │ │
      │ │ 3. ESPN API: Get Opponent Roster        │ │
      │ │    Find matchup by matchupPeriodId      │ │
      │ └─────────────────────────────────────────┘ │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ Data Processing                              │
      │ • Extract player projections                 │
      │ • Calculate current scores                   │
      │ • Determine injury statuses                  │
      │ • Identify opponent matchups                 │
      │ • Map positions (QB, RB, WR, TE, FLEX, etc) │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ AI Analysis (OpenAI GPT-4)                   │
      │ ┌─────────────────────────────────────────┐ │
      │ │ System Prompt:                          │ │
      │ │ "You are a fantasy football expert..."  │ │
      │ │                                          │ │
      │ │ Context Provided:                        │ │
      │ │ • All roster players with projections   │ │
      │ │ • Injury statuses                        │ │
      │ │ • Opponent lineup & projections         │ │
      │ │ • Current matchup score                  │ │
      │ │ • Bye weeks                              │ │
      │ │                                          │ │
      │ │ Request:                                 │ │
      │ │ "Optimize lineup for maximum points"    │ │
      │ └─────────────────────────────────────────┘ │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ AI Response Processing                       │
      │ {                                            │
      │   "optimal_lineup": {                        │
      │     "QB": {                                  │
      │       "name": "Josh Allen",                  │
      │       "projection": 22.5,                    │
      │       "reason": "Elite matchup vs DEF..."    │
      │     },                                       │
      │     "RB1": {...}, "RB2": {...},             │
      │     "WR1": {...}, "WR2": {...},             │
      │     "TE": {...}, "FLEX": {...}              │
      │   },                                         │
      │   "projected_total": 125.8,                  │
      │   "confidence_level": "High",                │
      │   "key_decisions": [...]                     │
      │ }                                            │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ Rate Limiter: Record Usage                   │
      │ • Actual tokens: 1850 input + 620 output    │
      │ • Cost: $0.048                               │
      │ • Update hourly total                        │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
      ┌─────────────────────────────────────────────┐
      │ Response Formatting                          │
      │ Convert AI JSON to user-friendly display:    │
      │                                              │
      │ "🎯 Optimal Lineup (Projected: 125.8 pts)   │
      │  Confidence: High                            │
      │                                              │
      │  QB: Josh Allen (22.5 pts)                   │
      │      Elite matchup vs weak pass defense      │
      │                                              │
      │  RB1: Saquon Barkley (18.2 pts)             │
      │       High volume, favorable game script     │
      │  ..."                                        │
      └──────────┬──────────────────────────────────┘
                 │
                 ▼
         ┌───────────────────┐
         │ Streamlit Display │
         │ Renders formatted │
         │ response in chat  │
         └───────────────────┘
```

### Component Interaction Map

```
┌───────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTIONS                      │
└───────────────────────────────────────────────────────────────┘

 1. AUTHENTICATION & DATA RETRIEVAL
    ┌──────────┐      ┌─────────────┐      ┌──────────────┐
    │ .env     │─────▶│ config.py   │─────▶│ espn_api.py  │
    │ ESPN_S2  │      │ Load & decode│      │ Authenticate │
    │ SWID     │      │ cookies      │      │ HTTP requests│
    │ LEAGUE_ID│      └─────────────┘      └──────┬───────┘
    └──────────┘                                   │
                                                   │
                        ┌──────────────────────────┘
                        ▼
                 ┌──────────────┐
                 │ ESPN API     │
                 │ Returns JSON │
                 │ with views:  │
                 │ • mRoster    │
                 │ • mMatchup   │
                 │ • mPlayer    │
                 └──────┬───────┘
                        │
    ┌───────────────────┴────────────────────┐
    │                                         │
    ▼                                         ▼
┌─────────────┐                      ┌─────────────┐
│ get_roster  │                      │ get_matchup │
│ Endpoint    │                      │ Endpoint    │
└─────────────┘                      └─────────────┘


 2. AI SERVICE INTEGRATION
    ┌──────────────────┐      ┌─────────────────┐
    │ API Endpoint     │─────▶│ Rate Limiter    │
    │ (receives req)   │      │ Check budget    │
    └──────┬───────────┘      └────────┬────────┘
           │                           │ ✅
           ▼                           ▼
    ┌──────────────────┐      ┌─────────────────┐
    │ ai_services.py   │      │ OpenAI Client   │
    │ FantasyAIService │─────▶│ GPT-4 Request   │
    │ • Prepare prompt │      └────────┬────────┘
    │ • Format context │               │
    └──────────────────┘               │
                                       ▼
                            ┌──────────────────┐
                            │ OpenAI Response  │
                            └────────┬─────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │ Rate Limiter     │
                            │ Record actual $$ │
                            └──────────────────┘


 3. STREAMLIT CLIENT FLOW
    ┌──────────────────┐
    │ User opens app   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐      ┌─────────────────┐
    │ client.py loads  │─────▶│ GET /get_matchup│
    │ Page config      │      │ Fetch data      │
    └──────────────────┘      └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Display matchup │
                              │ Show rosters    │
                              └────────┬────────┘
                                       │
             ┌─────────────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ User clicks      │
    │ "Optimize lineup"│
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────┐      ┌─────────────────────┐
    │ process_chat_message │─────▶│ POST /chat/enhanced │
    │ Sends to backend     │      │ AI processing       │
    └──────────────────────┘      └────────┬────────────┘
                                           │
                                           ▼
                                  ┌─────────────────────┐
                                  │ Stream response     │
                                  │ Display results     │
                                  │ Update UI           │
                                  └─────────────────────┘
```

## ✨ Features

### 🎯 Lineup Optimization
- **AI-Powered Decisions** - Analyzes projections, matchups, injuries, and opponent context
- **Position-Specific Logic** - Handles QB, RB, WR, TE, FLEX, K, and DEF positions
- **Real-Time Data** - Uses current week projections and injury reports
- **Confidence Ratings** - Provides high/medium/low confidence on recommendations

### 🤝 Trade Analysis
- **League-Wide Scanning** - Analyzes all teams to identify realistic trade partners
- **Need-Based Matching** - Identifies teams with complementary roster needs
- **Multi-Player Proposals** - Generates balanced 1-for-1, 2-for-1, or 2-for-2 trades
- **Trade Value Context** - Considers team records, playoff positioning, and roster depth

### 🔍 Waiver Wire Recommendations
- **Filtered Availability** - Only shows players not currently rostered in your league
- **Priority Rankings** - High/Medium/Low priority based on upside and need
- **Position Targeting** - Focuses on your team's weak positions
- **Ownership Trends** - Shows ownership percentage and rising/falling trends

### 📊 Player Comparisons
- **Head-to-Head Analysis** - Compare any two players for start/sit decisions
- **Matchup Context** - Considers opponent defenses and game scripts
- **Statistical Trends** - Analyzes recent performance and season averages
- **Expert Reasoning** - AI explains the "why" behind each recommendation

### 🏥 Injury Monitoring
- **Real-Time Status** - Shows current injury designations (Q, D, O, IR)
- **Practice Reports** - Includes practice participation when available
- **Timeline Estimates** - Projects expected return dates for injured players
- **Roster Impact** - Identifies which lineup spots are affected

### 💬 Interactive Chat Interface
- **Natural Language** - Ask questions in plain English
- **Context Awareness** - Remembers conversation history
- **Multi-Tool Integration** - Seamlessly switches between different analysis types
- **Quick Actions** - Pre-built buttons for common requests

### 💰 Cost Management
- **Rate Limiting** - Automatic $10/hour spending cap for OpenAI API
- **Usage Dashboard** - Real-time tracking of API costs and token usage
- **Cost Estimation** - Shows estimated cost before making each request
- **Per-Feature Tracking** - Separate cost tracking for each AI feature

## 📐 System Diagrams

### ESPN API Authentication Flow

```
┌──────────────┐
│ User's       │
│ Browser      │
│ (ESPN.com)   │
└──────┬───────┘
       │ 1. Login to ESPN Fantasy
       │
       ▼
┌─────────────────────────────────────┐
│ ESPN Sets Cookies:                  │
│ • espn_s2 (session token)          │
│ • SWID (user ID)                    │
│ • espnAuth (auth token)             │
└──────┬──────────────────────────────┘
       │ 2. Extract from browser DevTools
       │    Application → Cookies
       ▼
┌──────────────┐
│ .env file    │
│ ESPN_S2=...  │
│ SWID=...     │
│ ESPN_AUTH=...│
└──────┬───────┘
       │ 3. App reads at startup
       ▼
┌──────────────────────────────┐
│ espn_get() function          │
│ Attaches cookies to request  │
│ Headers:                     │
│  - User-Agent                │
│  - Accept: application/json  │
│  - Referer: fantasy.espn.com │
└──────┬───────────────────────┘
       │ 4. Authenticated request
       ▼
┌──────────────────────────────┐
│ ESPN API                     │
│ lm-api-reads.fantasy.espn.com│
│ /apis/v3/games/ffl/          │
│ seasons/2025/leagues/{id}    │
│                              │
│ ?view=mRoster                │
│ &view=mMatchupScore          │
└──────┬───────────────────────┘
       │ 5. JSON response with private data
       ▼
┌──────────────────────────────┐
│ Application processes        │
│ Player stats, rosters,       │
│ matchups, projections        │
└──────────────────────────────┘
```

### Rate Limiting State Machine

```
                    ┌─────────────────┐
                    │  Request comes  │
                    │  in from user   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Rate Limiter    │
                    │ can_make_request│
                    └────────┬────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌────────────────┐                      ┌─────────────────┐
│ Check current  │                      │ Estimate cost   │
│ hourly spending│                      │ for this request│
│ from session   │                      │ (input + output │
│ state          │                      │ tokens × price) │
└────────┬───────┘                      └────────┬────────┘
         │                                       │
         └───────────────┬───────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ current + estimated  │
              │ < $10.00/hour ?      │
              └──────┬───────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
  ┌─────────┐              ┌──────────┐
  │   NO    │              │   YES    │
  │ ❌ 429  │              │ ✅ Allow │
  │ Error   │              │ Request  │
  └─────────┘              └────┬─────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │ Execute AI request   │
                    │ to OpenAI API        │
                    └────────┬─────────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │ record_usage()       │
                    │ Log actual tokens    │
                    │ and real cost        │
                    └────────┬─────────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │ Store in session     │
                    │ state with timestamp │
                    │ for 1-hour window    │
                    └──────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+ (recommended) or 3.11+
- `uv` package manager (or pip)
- ESPN Fantasy account with an active league
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hidden-espn-api-project
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section)
   ```

4. **Run the dashboard**
   ```bash
   python start_dashboard.py
   # or
   uv run python start_dashboard.py
   ```

5. **Access the application**
   - **Streamlit Dashboard**: http://localhost:8501
   - **FastAPI Backend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## ⚙️ Configuration

### Required Environment Variables

Create a `.env` file with the following:

```bash
# ESPN Authentication (get from browser cookies after logging in)
ESPN_S2=your_espn_s2_cookie_value
ESPN_S2_ENCODED=url_encoded_version_if_needed
ESPN_AUTH=your_espn_auth_json
SWID=your_swid_cookie

# League Configuration
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
SEASON=2025

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

### How to Get ESPN Cookies

1. Log in to your ESPN Fantasy league at https://fantasy.espn.com
2. Open browser DevTools (F12)
3. Go to Application → Cookies → https://fantasy.espn.com
4. Copy the values for:
   - `espn_s2`
   - `SWID`
   - `espnAuth` (if present)

### Finding Your League and Team IDs

- **League ID**: Look in the URL when viewing your league: `...leagueId=1866946053`
- **Team ID**: View your team page and check the URL: `...teamId=8`

## 📚 API Documentation

### Core Endpoints

#### `GET /get_roster`
Fetch your team's roster with projections and stats.

**Response:**
```json
{
  "team_name": "My Team",
  "week": 4,
  "roster": [
    {
      "player": "Josh Allen",
      "position": 1,
      "lineup_slot": 0,
      "nfl_team": 2,
      "weekly_proj_value": 22.5,
      "injury_status": "ACTIVE",
      "opponent": "MIA"
    }
  ]
}
```

#### `POST /ai/optimize_lineup`
Get AI-powered lineup recommendations.

**Request:**
```json
{
  "include_opponent_context": true
}
```

**Response:**
```json
{
  "optimal_lineup": {
    "QB": {
      "name": "Josh Allen",
      "projection": 22.5,
      "reason": "Elite matchup against weak secondary"
    }
  },
  "projected_total": 125.8,
  "confidence_level": "High"
}
```

#### `POST /ai/trade_analysis`
Analyze trade opportunities with league context.

**Request:**
```json
{
  "include_league_rosters": true,
  "target_player": "A.J. Brown"
}
```

#### `POST /ai/waiver_wire`
Get waiver wire pickup recommendations.

**Request:**
```json
{
  "include_league_context": true,
  "max_players_per_position": 5
}
```

### Chat Interface

#### `POST /chat/enhanced`
Natural language interface for all features.

**Request:**
```json
{
  "message": "Who should I start this week?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "status": "success",
  "response": "I optimized your lineup...",
  "tool_calls": [{"tool": "optimize_lineup"}],
  "enhanced_data": [...]
}
```

## 🛠️ Development

### Project Structure

```
.
├── api/
│   ├── main.py              # FastAPI app & endpoints
│   ├── ai_services.py       # OpenAI integration
│   ├── chat_agent.py        # Chat interface logic
│   ├── get_roster.py        # Roster data retrieval
│   └── get_matchup.py       # Matchup data retrieval
├── client.py                # Streamlit dashboard
├── espn_api.py              # Core ESPN API wrapper
├── config.py                # Configuration management
├── rate_limiter.py          # Cost control system
├── start_dashboard.py       # Unified startup script
├── requirements.txt         # Python dependencies
├── pyproject.toml           # uv project config
├── .env.example             # Environment template
└── README.md                # This file
```

### Running Individual Components

```bash
# FastAPI only
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Streamlit only
streamlit run client.py --server.port 8501

# Test ESPN API connection
python espn_api.py
```

### Running Tests

```bash
# Rate limiting tests
python test_rate_limiting.py

# Trade analysis tests
python test_trade_analyzer.py

# Waiver wire tests
python test_waiver_filter.py
```

### Key Development Notes

1. **ESPN API is Undocumented** - The API structure can change without notice. The app uses multiple "views" to fetch different data:
   - `mRoster` - Team rosters
   - `mMatchupScore` - Current matchups
   - `mPlayer` - Player pool data
   - `mSchedule` - League schedule

2. **Rate Limiting is Critical** - Always test with rate limiting enabled to avoid unexpected OpenAI costs:
   ```python
   from rate_limiter import check_rate_limit_decorator

   @check_rate_limit_decorator
   def my_ai_function():
       # Your AI logic here
       pass
   ```

3. **Streamlit Session State** - The app uses Streamlit session state to persist chat history and usage data across interactions.

4. **DevContainer Support** - The project includes `.devcontainer/` configuration for GitHub Codespaces and VS Code Remote Containers.

## 📝 License

This project is for educational purposes. ESPN's API is undocumented and may have terms of service restrictions. Use responsibly.

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub issues.

---

**Made with 🏈 for fantasy football enthusiasts**

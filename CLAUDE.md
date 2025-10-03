# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ESPN Fantasy Football API reverse engineering project that provides AI-powered fantasy football analysis. The application consists of:
- **FastAPI backend** (`api/`) - Wraps ESPN's undocumented API with structured endpoints
- **Streamlit frontend** (`client.py`) - Interactive dashboard for lineup optimization, trade analysis, and player comparisons
- **Rate limiting system** (`rate_limiter.py`) - Prevents exceeding $10/hour OpenAI API costs for public deployment

## Environment Setup

### Required Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# ESPN Authentication (from browser cookies after logging into fantasy.espn.com)
ESPN_S2=your_espn_s2_cookie
ESPN_S2_ENCODED=url_encoded_version_of_espn_s2
ESPN_AUTH=your_espn_auth_json
SWID=your_swid_cookie

# League Configuration
LEAGUE_ID=your_league_id
TEAM_ID=your_team_id
SEASON=2025

# OpenAI for AI features
OPENAI_API_KEY=your_openai_key
```

### Python Environment

The project uses `uv` for Python package management (Python 3.13+):

```bash
# Install dependencies
uv sync

# Or use traditional pip
pip install -r requirements.txt
```

## Common Commands

### Running the Application

```bash
# Start both FastAPI and Streamlit (recommended)
python start_dashboard.py
# or
uv run python start_dashboard.py

# Streamlit dashboard: http://localhost:8501
# FastAPI server: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Running Individual Services

```bash
# FastAPI server only
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Streamlit dashboard only
streamlit run client.py --server.port 8501
```

### Running Tests

```bash
# Individual test files
python test_rate_limiting.py
python test_trade_analyzer.py
python test_waiver_filter.py
python test_improved_trades.py

# Or with uv
uv run python test_rate_limiting.py
```

### Standalone Scripts

```bash
# Test ESPN API connection and fetch roster
python espn_api.py

# Direct API access
python main.py
```

## Architecture

### ESPN API Integration (`espn_api.py`, `api/get_roster.py`, `api/get_matchup.py`)

The core ESPN API wrapper uses authenticated requests with cookies to access private league data. Key functions:

- `espn_get(views, extra_params)` - Generic GET helper for ESPN endpoints
- `get_current_week()` - Auto-detects current NFL week from ESPN data
- `build_maps_from_settings()` - Creates lookup dictionaries for player positions, teams, and slots

ESPN requires specific headers and cookies (`ESPN_S2`, `SWID`, `espnAuth`) for authenticated access. The API is heavily view-based, using query parameters like `view=mRoster`, `view=mMatchupScore`, etc.

### AI Services (`api/ai_services.py`)

`FantasyAIService` class provides OpenAI-powered analysis:

- **Lineup optimization** - Analyzes projections, matchups, injuries, and opponent context
- **Player comparisons** - Head-to-head analysis considering schedules and trends
- **Trade analysis** - Evaluates proposed trades with league roster context
- **Waiver wire recommendations** - Identifies valuable available players

All AI methods are decorated with `@check_rate_limit_decorator` to prevent excessive costs.

### Rate Limiting (`rate_limiter.py`)

The `RateLimiter` class tracks OpenAI API usage in Streamlit session state:

- Hourly spending limit: $10/hour (configurable via `HOURLY_LIMIT`)
- Tracks token usage and costs per model (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
- `can_make_request()` checks before API calls
- `record_usage()` logs actual costs after completion
- `display_usage_dashboard()` shows current usage in Streamlit UI

### Configuration (`config.py`)

Centralized configuration management with URL decoding for ESPN cookies and safe fallbacks for missing environment variables. Used throughout the application for consistent config access.

### FastAPI Backend (`api/main.py`)

REST endpoints for:
- `GET /get_roster` - Fetch team roster with projections
- `GET /get_matchup` - Current week matchup data
- `POST /ai/optimize_lineup` - AI lineup recommendations
- `POST /ai/compare_players` - Compare two players
- `POST /ai/analyze_trade` - Trade evaluation
- `POST /ai/waiver_wire` - Waiver wire suggestions

### Streamlit Frontend (`client.py`)

Multi-page dashboard with:
- Roster view with projections
- Matchup analysis
- AI-powered lineup optimizer
- Player comparison tool
- Trade analyzer
- Waiver wire recommendations
- Usage/cost tracking dashboard

## Development Notes

### ESPN API Considerations

- The API is undocumented and subject to change
- Requires valid authenticated session cookies from a logged-in browser
- Week auto-detection uses `status.currentMatchupPeriod` or falls back to scoring period ID
- Different views return different data structures - combine views for comprehensive data
- Rate limiting is not enforced by ESPN but be respectful

### OpenAI Cost Management

The rate limiter is critical for public deployment:
- Default model is `gpt-4-turbo` (balance of performance and cost)
- Each feature estimates token usage before execution
- Streamlit displays real-time cost tracking
- Session state persists usage across page reloads within same session

### Deployment

DevContainer configuration exists in `.devcontainer/` for Codespaces/VSCode:
- Uses Python 3.11 base image
- Auto-installs dependencies on container creation
- Auto-starts Streamlit on port 8501
- Configured for GitHub Codespaces with preview support

### Testing

Test files (`test_*.py`) are standalone scripts that test specific functionality:
- `test_rate_limiting.py` - Rate limiter functionality
- `test_trade_analyzer.py` - Trade analysis AI logic
- `test_waiver_filter.py` - Waiver wire filtering
- `test_improved_trades.py` - Enhanced trade analysis

Run these directly with Python to verify specific features.

## File Structure

```
.
├── api/                      # FastAPI backend
│   ├── main.py              # API endpoints
│   ├── ai_services.py       # OpenAI integration
│   ├── get_roster.py        # Roster data fetching
│   └── get_matchup.py       # Matchup data fetching
├── client.py                # Streamlit frontend
├── espn_api.py              # Core ESPN API wrapper
├── config.py                # Configuration management
├── rate_limiter.py          # OpenAI cost control
├── start_dashboard.py       # Unified startup script
├── start_api.py             # API-only startup
├── test_*.py                # Test scripts
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── pyproject.toml           # uv project configuration
```

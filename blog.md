# Reverse Engineering ESPN's Fantasy Football API: A Complete Technical Deep Dive

## Introduction

Have you ever wanted to build custom tools for your fantasy football league but felt limited by the lack of official APIs? I recently reverse-engineered ESPN's undocumented Fantasy Football API to build an AI-powered fantasy assistant, and I'm going to show you exactly how I did it.

This isn't just another "how to scrape data" tutorial. This is a comprehensive guide to **identifying, understanding, and responsibly interfacing with undocumented APIs**—skills that are applicable to virtually any web application you want to extract data from.

By the end of this article, you'll understand:
- How to identify API endpoints using browser developer tools
- How to replicate authenticated requests programmatically
- Best practices for working with undocumented APIs
- How to build production-ready wrappers around reverse-engineered endpoints

## The Problem: No Official ESPN Fantasy API

ESPN doesn't provide a public API for fantasy football data. Their official stance is to use their web interface only. But as developers, we know that their web interface *must* be calling APIs to fetch data—we just need to find them.

## Step 1: Opening the Network Tab

The first step in any API reverse engineering project is to observe what the browser is actually doing. Modern web applications are client-heavy, meaning the browser fetches data via JavaScript after the page loads.

### What to Look For

Open your browser's Developer Tools (F12 or Cmd+Option+I) and navigate to the **Network** tab. Here's my methodology:

1. **Clear existing requests**: Click the "Clear" button to start fresh
2. **Filter to XHR/Fetch**: These are AJAX requests—exactly what we're looking for
3. **Navigate to the page**: Load your fantasy football team page
4. **Watch for API calls**: Look for requests to domains like `api.espn.com` or similar

### The Discovery

When I loaded my ESPN Fantasy Football team page, I immediately saw requests to:

```
https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/{LEAGUE_ID}
```

**This was the goldmine.** A dedicated API subdomain (`lm-api-reads`) with a clear RESTful structure.

### Analyzing the Request

Clicking on this request revealed critical information:

**Request Headers:**
```
Accept: application/json
Referer: https://fantasy.espn.com/
Origin: https://fantasy.espn.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...
x-fantasy-filter: {"players":{}}
x-fantasy-platform: kona-PROD-1eb11d9ef8e2d38718627f7aae409e9065630000
x-fantasy-source: kona
```

**Query Parameters:**
```
view=mRoster
view=mTeam
view=mSettings
scoringPeriodId=4
```

**Cookies (Authentication):**
```
ESPN_S2: AEBa...very_long_token...xyz
SWID: {12345678-ABCD-EFGH-IJKL-123456789012}
espnAuth: {...JSON authentication object...}
```

This told me everything I needed to know:
1. **Authentication is cookie-based** (ESPN_S2 and SWID)
2. **The API uses a "view" system** to request different data types
3. **Custom headers are required** (x-fantasy-*)
4. **The API returns JSON**

## Step 2: Extracting Authentication Cookies

ESPN's API uses session-based authentication. You need to be logged in to access your private league data.

### How to Get Your Cookies

1. Log in to [fantasy.espn.com](https://fantasy.espn.com)
2. Open Developer Tools → Application → Cookies → `https://fantasy.espn.com`
3. Copy these cookie values:
   - `ESPN_S2` (very long token)
   - `SWID` (UUID format like `{xxx-xxx-xxx}`)
   - `espnAuth` (JSON object)

**⚠️ Security Warning**: These cookies are equivalent to your ESPN password. Never commit them to public repositories or share them. Always use environment variables.

### Proper Cookie Management

Here's how I safely handle authentication in my project:

```python
import os
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()

# Get cookies from environment variables (never hardcode!)
ESPN_S2_ENCODED = os.getenv("ESPN_S2_ENCODED")
ESPN_AUTH = os.getenv("ESPN_AUTH")
ESPN_S2 = os.getenv("ESPN_S2") or (unquote(ESPN_S2_ENCODED) if ESPN_S2_ENCODED else None)
SWID = os.getenv("SWID")

# League configuration
LEAGUE_ID = os.getenv("LEAGUE_ID")
TEAM_ID = os.getenv("TEAM_ID")
SEASON = 2025
```

Create a `.env` file (and add it to `.gitignore`!):

```bash
# .env
ESPN_S2=your_espn_s2_cookie_here
ESPN_S2_ENCODED=url_encoded_version_if_needed
ESPN_AUTH=your_espn_auth_json_here
SWID=your_swid_cookie_here
LEAGUE_ID=1234567890
TEAM_ID=8
SEASON=2025
```

## Step 3: Replicating the Request in Python

Now that we understand the request structure, let's replicate it programmatically.

### Building the Base Request Function

```python
import requests

BASE_URL = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

def espn_get(views, extra_params=None):
    """
    GET helper for ESPN league endpoints with one or more views.

    Args:
        views: list[str] like ["mRoster", "mSettings"]
        extra_params: dict of additional query params

    Returns:
        dict: JSON response from ESPN API
    """
    # Build query parameters
    params = []
    for v in views:
        params.append(("view", v))

    if extra_params:
        for k, v in extra_params.items():
            params.append((k, str(v)))

    with requests.Session() as s:
        # Set authentication cookies
        auth_cookies = {
            "ESPN_S2": ESPN_S2,
            "SWID": SWID,
            "espn_s2": ESPN_S2_ENCODED,
            "espnAuth": ESPN_AUTH,
        }
        s.cookies.update(auth_cookies)

        # Add required headers (matching the browser request)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://fantasy.espn.com/',
            'Origin': 'https://fantasy.espn.com',
            'x-fantasy-filter': '{"players":{}}',
            'x-fantasy-platform': 'kona-PROD-1eb11d9ef8e2d38718627f7aae409e9065630000',
            'x-fantasy-source': 'kona'
        }

        r = s.get(BASE_URL, params=params, headers=headers, timeout=20)

        # Handle errors gracefully
        if r.status_code >= 400:
            snippet = r.text[:500].replace("\n", " ")
            raise RuntimeError(f"HTTP {r.status_code} error: {snippet}")

        return r.json()
```

### Key Implementation Details

1. **Session Management**: Using `requests.Session()` maintains cookies across requests
2. **Multiple Views**: ESPN's API supports multiple `view` parameters to fetch different data types in one request
3. **Header Matching**: The `x-fantasy-*` headers are crucial—omitting them may cause authentication failures
4. **Error Handling**: ESPN sometimes returns HTML error pages instead of JSON, so we check status codes

## Step 4: Understanding ESPN's "View" System

This was the most interesting discovery. ESPN's API uses a **view-based architecture** where you specify what data you want via query parameters.

### Common Views

Through experimentation and network analysis, I identified these useful views:

| View | Data Returned |
|------|---------------|
| `mSettings` | League settings, scoring rules, current week |
| `mRoster` | Team rosters with player details |
| `mTeam` | Team metadata, records, standings |
| `mMatchupScore` | Current matchup scores and projections |
| `mSchedule` | Full season schedule |
| `mPlayer` | Detailed player information |
| `mLiveScoring` | Live scoring data during games |
| `mProjections` | Weekly player projections |
| `mDraftDetail` | Draft history and results |
| `mPendingTransactions` | Waiver wire and trade status |

### Combining Views for Efficiency

You can request multiple views in a single API call:

```python
# Get roster + settings + matchup data in one request
data = espn_get(["mRoster", "mSettings", "mMatchupScore"])

# Access different parts of the response
settings = data.get("settings", {})
teams = data.get("teams", [])
schedule = data.get("schedule", [])
```

This is **much more efficient** than making separate requests for each data type.

## Step 5: Decoding the Response Structure

ESPN's JSON responses are deeply nested and use numeric IDs that need to be mapped to human-readable values.

### Example: Fetching Team Roster

```python
def get_team_roster(league_id, team_id, week=None):
    """
    Fetch roster for a specific team and week.

    Args:
        league_id: ESPN league ID
        team_id: Team ID within the league
        week: NFL week number (None for current week)

    Returns:
        tuple: (team_name, roster_rows)
    """
    # Build parameters
    params = {"rosterForTeamId": team_id}
    if week:
        params["scoringPeriodId"] = week

    # Request multiple views for comprehensive data
    views = ["mRoster", "mSettings", "mTeam", "mProjections"]
    data = espn_get(views, extra_params=params)

    # Extract data
    settings = data.get("settings", {})
    teams = data.get("teams", [])

    # Find specific team
    team_obj = next((t for t in teams if t.get("id") == team_id), None)
    if not team_obj:
        raise ValueError(f"Team {team_id} not found")

    # Process roster entries
    roster_entries = team_obj.get("roster", {}).get("entries", [])

    roster = []
    for entry in roster_entries:
        player = entry.get("playerPoolEntry", {}).get("player", {})

        roster.append({
            "player_name": player.get("fullName", "Unknown"),
            "position": get_position_name(player.get("defaultPositionId")),
            "nfl_team": get_nfl_team(player.get("proTeamId")),
            "lineup_slot": entry.get("lineupSlotId"),
            "injury_status": player.get("injuryStatus", "ACTIVE"),
            "projected_points": get_projection(player, week)
        })

    team_name = f"{team_obj.get('location', '')} {team_obj.get('nickname', '')}".strip()
    return team_name, roster
```

### Mapping Numeric IDs to Names

ESPN uses numeric IDs for positions, teams, and lineup slots. You need to create mapping dictionaries:

```python
def build_maps_from_settings(settings_obj):
    """
    Create mapping dicts from mSettings view.

    Returns:
        tuple: (slot_map, position_map, team_map)
    """
    slot_id_to_name = {}
    pos_id_to_name = {}

    # Parse slot categories
    for slot_cat in settings_obj.get("slotCategoryInfo", []):
        slot_id = slot_cat.get("id")
        name = slot_cat.get("name")
        if slot_id is not None and name:
            slot_id_to_name[slot_id] = name

    # Parse position IDs
    for slot_cat in settings_obj.get("slotCategoryInfo", []):
        for pos_id in slot_cat.get("positionIds", []):
            pos_id_to_name[pos_id] = slot_cat.get("name")

    # Parse NFL team names
    pro_team_map = {}
    for team in settings_obj.get("proTeams", []):
        team_id = team.get("id")
        location = team.get("location", "")
        name = team.get("name", "")
        abbrev = team.get("abbrev", "")

        if team_id:
            full_name = f"{location} {name}".strip() or abbrev
            pro_team_map[team_id] = {"full": full_name, "abbrev": abbrev}

    return slot_id_to_name, pos_id_to_name, pro_team_map
```

### Pro Tip: Hardcode Common Mappings

The NFL team IDs rarely change, so you can hardcode them for faster lookups:

```python
NFL_TEAMS = {
    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
    9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
    17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
    25: "SF", 26: "SEA", 27: "TB", 28: "WSH", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU"
}
```

## Step 6: Auto-Detecting the Current Week

One challenge was figuring out which week of the NFL season we're currently in. ESPN provides this in their API response:

```python
def get_current_week():
    """
    Auto-detect current NFL week from ESPN's API.

    Returns:
        int: Current NFL week number
    """
    try:
        # Get league settings
        data = espn_get(["mSettings"])
        settings = data.get("settings", {})

        # ESPN provides the current scoring period
        current_week = settings.get("scoringPeriodId")
        if current_week:
            return current_week

        # Fallback: Get from status endpoint
        data = espn_get(["mMatchupScore"])
        status = data.get("status", {})
        current_week = status.get("currentMatchupPeriod")
        if current_week:
            return current_week

        return 1  # Safe default
    except Exception as e:
        print(f"Warning: Could not auto-detect week: {e}")
        return 1
```

## Step 7: Building a Production-Ready Wrapper

Now let's wrap everything into a clean FastAPI service that others can use:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="ESPN Fantasy Football API")

class Player(BaseModel):
    name: str
    position: str
    nfl_team: str
    injury_status: str
    projection: float
    current_score: float

class RosterResponse(BaseModel):
    team_name: str
    week: int
    roster: List[Player]

@app.get("/roster/{team_id}", response_model=RosterResponse)
async def get_roster(team_id: int, week: Optional[int] = None):
    """
    Get roster for a specific team.

    Args:
        team_id: ESPN team ID
        week: NFL week (defaults to current week)

    Returns:
        RosterResponse with team name and player list
    """
    try:
        if week is None:
            week = get_current_week()

        team_name, roster_data = get_team_roster(LEAGUE_ID, team_id, week)

        players = [
            Player(
                name=p["player_name"],
                position=p["position"],
                nfl_team=p["nfl_team"],
                injury_status=p["injury_status"],
                projection=p["projected_points"],
                current_score=p.get("current_score", 0)
            )
            for p in roster_data
        ]

        return RosterResponse(
            team_name=team_name,
            week=week,
            roster=players
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Testing Your API

```bash
# Start the server
uvicorn api.main:app --reload --port 8000

# Test the endpoint
curl http://localhost:8000/roster/8?week=4
```

## Step 8: Advanced Use Cases

### Getting Matchup Data

```python
@app.get("/matchup/{team_id}")
async def get_matchup(team_id: int, week: Optional[int] = None):
    """
    Get current week matchup for a team.

    Returns both teams' rosters and projected scores.
    """
    if week is None:
        week = get_current_week()

    # Get schedule to find opponent
    data = espn_get(["mSchedule", "mTeam", "mRoster"], {"scoringPeriodId": week})
    schedule = data.get("schedule", [])

    # Find matchup containing this team
    matchup = None
    for match in schedule:
        if match.get("matchupPeriodId") == week:
            team_ids = [t.get("id") for t in match.get("teams", [])]
            if team_id in team_ids:
                matchup = match
                break

    if not matchup:
        raise HTTPException(status_code=404, detail="Matchup not found")

    # Get both teams' data
    teams_data = matchup.get("teams", [])
    my_team = next(t for t in teams_data if t.get("id") == team_id)
    opponent = next(t for t in teams_data if t.get("id") != team_id)

    return {
        "week": week,
        "my_team": process_team_data(my_team),
        "opponent": process_team_data(opponent),
        "my_win_probability": calculate_win_prob(my_team, opponent)
    }
```

### Fetching Available Players (Waiver Wire)

```python
@app.get("/available-players")
async def get_available_players(position: Optional[str] = None, limit: int = 50):
    """
    Get available players on waiver wire.

    Args:
        position: Filter by position (QB, RB, WR, TE, etc.)
        limit: Max players to return
    """
    # Use kona_player_info view for player pool
    views = ["kona_player_info", "mSettings"]

    # Build filter for available players only
    player_filter = {
        "players": {
            "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
            "limit": limit,
            "sortPercOwned": {"sortPriority": 1, "sortAsc": False}
        }
    }

    # Add position filter if specified
    if position:
        pos_id = POSITION_MAP.get(position.upper())
        if pos_id:
            player_filter["players"]["filterSlotIds"] = {"value": [pos_id]}

    # Make request with custom filter header
    headers = {'x-fantasy-filter': json.dumps(player_filter)}
    data = espn_get(views)

    players = data.get("players", [])

    return {
        "count": len(players),
        "players": [format_player(p) for p in players[:limit]]
    }
```

## Best Practices for Working with Undocumented APIs

### 1. **Respect Rate Limits**

Even though ESPN doesn't publish rate limits, you should implement your own:

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=30):
    """Decorator to rate limit API calls."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def espn_get(views, extra_params=None):
    # ... existing code ...
```

### 2. **Implement Caching**

Don't hammer the API for data that rarely changes:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache settings for 1 hour
@lru_cache(maxsize=1)
def get_league_settings_cached():
    cache_time = datetime.now()
    settings = espn_get(["mSettings"])
    return settings, cache_time

def get_league_settings():
    settings, cache_time = get_league_settings_cached()

    # Refresh if older than 1 hour
    if datetime.now() - cache_time > timedelta(hours=1):
        get_league_settings_cached.cache_clear()
        return get_league_settings()

    return settings
```

### 3. **Handle Errors Gracefully**

Undocumented APIs can change without notice:

```python
def safe_espn_get(views, extra_params=None, retries=3):
    """
    Wrapper with retry logic and error handling.
    """
    for attempt in range(retries):
        try:
            return espn_get(views, extra_params)
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            print(f"Request failed (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
```

### 4. **Never Share Authentication Credentials**

Use environment variables and `.env` files:

```python
# .gitignore
.env
.env.local
*.env

# Always load from environment
from dotenv import load_dotenv
load_dotenv()

# Never hardcode
ESPN_S2 = os.getenv("ESPN_S2")  # ✅ Good
ESPN_S2 = "AEBa..."              # ❌ Bad
```

### 5. **Document Your Findings**

Create a comprehensive map of available endpoints and views:

```python
"""
ESPN Fantasy Football API Documentation
Discovered through reverse engineering

Base URL: https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}

Available Views:
- mSettings: League configuration, scoring settings
- mRoster: Team rosters with player details
- mTeam: Team records and metadata
- mMatchupScore: Live matchup scoring
- mSchedule: Full season schedule
- mPlayer: Player information
- mLiveScoring: Live game updates
- mProjections: Player projections
- mDraftDetail: Draft results
- mPendingTransactions: Waivers and trades

Authentication:
- Cookie: ESPN_S2 (session token)
- Cookie: SWID (user ID)
- Cookie: espnAuth (auth JSON)

Required Headers:
- Accept: application/json
- Referer: https://fantasy.espn.com/
- x-fantasy-source: kona
"""
```

### 6. **Monitor for Changes**

APIs can change. Implement logging to detect issues:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def espn_get(views, extra_params=None):
    logger.info(f"ESPN API request: views={views}, params={extra_params}")

    try:
        response = # ... make request ...
        logger.info(f"ESPN API success: status={response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"ESPN API error: {str(e)}")
        raise
```

### 7. **Use Responsibly**

- Don't abuse the API with excessive requests
- Cache aggressively
- Respect the service's infrastructure
- Use for personal projects, not commercial applications
- Don't share others' private league data

## Real-World Application: AI Fantasy Assistant

With the API reverse-engineered, I built an AI-powered fantasy football assistant that:

1. **Analyzes lineup decisions** using OpenAI GPT-4
2. **Compares players** with real-time data
3. **Recommends waiver pickups** based on projections
4. **Evaluates trade offers** considering team needs

### Example: AI Lineup Optimizer

```python
from openai import OpenAI

def optimize_lineup_with_ai(team_id, week=None):
    """Use AI to suggest optimal lineup changes."""

    # Get roster data
    team_name, roster = get_team_roster(LEAGUE_ID, team_id, week)

    # Get opponent data
    matchup = get_matchup(team_id, week)

    # Format for AI
    prompt = f"""
    Analyze this fantasy football lineup and suggest optimizations:

    Team: {team_name}
    Week: {week}

    Current Lineup:
    {format_roster_for_prompt(roster)}

    Opponent Lineup:
    {format_roster_for_prompt(matchup['opponent']['roster'])}

    Consider:
    1. Projected points
    2. Injury status
    3. Matchup difficulty
    4. Recent performance trends

    Provide specific start/sit recommendations.
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

## Conclusion

Reverse engineering undocumented APIs is a valuable skill that opens up possibilities for custom integrations and tools. The key steps are:

1. **Use browser DevTools** to observe network requests
2. **Identify API endpoints** by filtering XHR/Fetch requests
3. **Extract authentication** credentials (cookies, tokens, API keys)
4. **Replicate requests** programmatically with proper headers
5. **Decode response structures** through experimentation
6. **Build robust wrappers** with error handling and caching
7. **Follow best practices** for rate limiting and responsible usage

The ESPN Fantasy Football API is just one example. These techniques apply to virtually any web application:
- Social media platforms
- E-commerce sites
- Financial services
- SaaS applications
- Internal company tools

### Complete Working Example

You can find the full implementation on GitHub: [ESPN Fantasy Football API Project](https://github.com/yourusername/espn-fantasy-api)

The repository includes:
- Complete API wrapper (`espn_api.py`)
- FastAPI REST service (`api/main.py`)
- Streamlit dashboard (`client.py`)
- AI integration (`api/ai_services.py`)
- Rate limiting system (`rate_limiter.py`)

### Try It Yourself

```bash
# Clone the repository
git clone https://github.com/yourusername/espn-fantasy-api
cd espn-fantasy-api

# Set up environment
cp .env.example .env
# Edit .env with your ESPN cookies

# Install dependencies
pip install -r requirements.txt

# Run the application
python start_dashboard.py

# Visit http://localhost:8501 for the dashboard
# Visit http://localhost:8000/docs for API documentation
```

## What Will You Reverse Engineer?

Now that you understand the process, what undocumented API will you tackle next? The same techniques work for:
- **DoorDash** (track orders programmatically)
- **Spotify** (advanced playlist analytics)
- **LinkedIn** (automated job search)
- **Instagram** (content analytics)
- **Netflix** (viewing history analysis)

Remember: Use these powers responsibly. Respect rate limits, never share private data, and always comply with terms of service.

---

**Questions or comments?** Drop them below! I'd love to hear about your API reverse engineering projects.

**Found this helpful?** Star the repository and share with fellow developers!

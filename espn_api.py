import os
import json
import requests
from urllib.parse import unquote

# --- CONFIG ---
LEAGUE_ID = 1866946053
TEAM_ID = 8           # <-- your team
SEASON = 2025
WEEK = 1              # change to desired week; omit to use current week

# Prefer env vars for cookies (safer). Fallback to literals if needed.
# Use the URL-encoded values from the browser and decode them
_ESPN_S2_ENCODED = "AEA%2F1l1nOxcw2G%2BAFY%2FPQW35gBxjiCemfHjo3oE7yccHUobHWV%2BJi5zCLfX4ArOBa49hslhbBupC3O%2B6EPWAdLQC9kUSA2oOccGrDUs2OskTlo6BnzdzkBTGYYn8UqOnukhk23gkNJlLcJEXestGFCF%2BdmzlPWi8QWIt5am7C2vMX6re8EjPhhtUPgA4sDwEZVyhrwzifVdKuF55Oggsw0tJGYfJjm2WF8tQeOob74QApFopqrWSmGnsaE2nfhNFaMw1Fg03Nfa8UB4tswyl0R6nb7%2FYA2D%2F0g5Zg04E%2BWCNLA%3D%3D"

ESPN_S2 = os.getenv("ESPN_S2") or unquote(_ESPN_S2_ENCODED)
SWID = os.getenv("SWID") or "{279F73E6-179A-40C3-80F2-889F8B9E968A}"

BASE = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"

def espn_get(views, extra_params=None):
    """
    GET helper for ESPN league endpoints with one or more views.
    views: list[str] like ["mRoster", "mSettings"]
    extra_params: dict of additional query params
    """
    params = []
    for v in views:
        params.append(("view", v))
    if extra_params:
        for k, v in extra_params.items():
            params.append((k, str(v)))

    with requests.Session() as s:
        # Set all the authentication cookies from the working request
        auth_cookies = {
            "ESPN_S2": ESPN_S2, 
            "SWID": SWID,
            "espn_s2": unquote("AEA%2F1l1nOxcw2G%2BAFY%2FPQW35gBxjiCemfHjo3oE7yccHUobHWV%2BJi5zCLfX4ArOBa49hslhbBupC3O%2B6EPWAdLQC9kUSA2oOccGrDUs2OskTlo6BnzdzkBTGYYn8UqOnukhk23gkNJlLcJEXestGFCF%2BdmzlPWi8QWIt5am7C2vMX6re8EjPhhtUPgA4sDwEZVyhrwzifVdKuF55Oggsw0tJGYfJjm2WF8tQeOob74QApFopqrWSmGnsaE2nfhNFaMw1Fg03Nfa8UB4tswyl0R6nb7%2FYA2D%2F0g5Zg04E%2BWCNLA%3D%3D"),
            "espnAuth": '{"swid":"{279F73E6-179A-40C3-80F2-889F8B9E968A}"}',
            "ESPN-ONESITE.WEB-PROD.api": "3eRWcGGEEQuUs6fkP4ojUKC2ZiTtCJMwaC1YQSB0IguvDUP6LgcIaGJTcBj+A2MoJsR6VBiSRqrbdUQRE2rrquVVTXSB"
        }
        s.cookies.update(auth_cookies)
        
        # Add headers that ESPN requires (matching the working request)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://fantasy.espn.com/',
            'Origin': 'https://fantasy.espn.com',
            'x-fantasy-filter': '{"players":{}}',
            'x-fantasy-platform': 'kona-PROD-1eb11d9ef8e2d38718627f7aae409e9065630000',
            'x-fantasy-source': 'kona'
        }
        
        r = s.get(BASE, params=params, headers=headers, timeout=20)
        
        # ESPN sometimes returns HTML error pages; show a snippet if error
        if r.status_code >= 400:
            snippet = r.text[:500].replace("\n", " ")
            raise RuntimeError(f"HTTP {r.status_code} error: {snippet}")
        return r.json()

def build_maps_from_settings(settings_obj):
    """
    Create mapping dicts from mSettings:
      - slot_id_to_name: lineup slotId -> human name (e.g., 0 -> 'QB', 2 -> 'RB')
      - pos_id_to_name: defaultPositionId -> human name (QB/RB/WR/TE/...)
      - pro_id_to_name: proTeamId -> 'City Team' (e.g., 'Kansas City Chiefs')
      - pro_id_to_abbrev: proTeamId -> 'KC', 'BUF', etc.
    """
    slot_id_to_name = {}
    pos_id_to_name = {}
    for sc in settings_obj.get("slotCategoryInfo", []):
        sid = sc.get("id")
        nm = sc.get("name")
        if sid is not None and nm:
            slot_id_to_name[sid] = nm
        # Some slotCategoryInfo include "positionIds" (e.g., RB has [2])
        for pid in sc.get("positionIds", []):
            pos_id_to_name[pid] = sc.get("name")

    pro_id_to_name = {}
    pro_id_to_abbrev = {}
    for team in settings_obj.get("proTeams", []):
        tid = team.get("id")
        loc = team.get("location", "")
        nm = team.get("name", "")
        ab = team.get("abbrev", "")
        if tid is not None:
            full = (loc + " " + nm).strip() if (loc or nm) else ab or f"ProTeam {tid}"
            pro_id_to_name[tid] = full
            pro_id_to_abbrev[tid] = ab or full

    return slot_id_to_name, pos_id_to_name, pro_id_to_name, pro_id_to_abbrev

def get_team_roster(league_id, team_id, week=None):
    """
    Fetch roster + settings, return a list of rows with resolved names.
    """
    # Pull roster + settings together so we can resolve IDs to names
    # Use the exact parameter format from the working browser request
    params = {"rosterForTeamId": team_id}
    if week is not None:
        params["scoringPeriodId"] = week

    # Use the exact views from the working request, plus player stats
    views = ["mDraftDetail", "mLiveScoring", "mMatchupScore", "mPendingTransactions", 
             "mPositionalRatings", "mRoster", "mSettings", "mTeam", "modular", "mNav",
             "kona_player_info", "player_wl", "mProjections"]
    
    data = espn_get(views, extra_params=params)

    settings = data.get("settings", {})
    teams = data.get("teams", [])

    if not teams:
        raise ValueError("No teams returned. Check league/team/cookies/permissions.")

    # Find the specific team object (mRoster with teamId usually returns one team)
    team_obj = None
    for t in teams:
        if t.get("id") == team_id:
            team_obj = t
            break
    if team_obj is None:
        # fallback: use first (in case API filtered already)
        team_obj = teams[0]

    slot_id_to_name, pos_id_to_name, pro_id_to_name, pro_id_to_abbrev = build_maps_from_settings(settings)
    
    # If no pro team data in settings, use hardcoded mapping
    if not pro_id_to_name:
        pro_id_to_name = {
            1: "Atlanta Falcons", 2: "Buffalo Bills", 3: "Chicago Bears", 4: "Cincinnati Bengals",
            5: "Cleveland Browns", 6: "Dallas Cowboys", 7: "Denver Broncos", 8: "Detroit Lions",
            9: "Green Bay Packers", 10: "Tennessee Titans", 11: "Indianapolis Colts", 12: "Kansas City Chiefs",
            13: "Las Vegas Raiders", 14: "Los Angeles Rams", 15: "Miami Dolphins", 16: "Minnesota Vikings",
            17: "New England Patriots", 18: "New Orleans Saints", 19: "New York Giants", 20: "New York Jets",
            21: "Philadelphia Eagles", 22: "Arizona Cardinals", 23: "Pittsburgh Steelers", 24: "Los Angeles Chargers",
            25: "San Francisco 49ers", 26: "Seattle Seahawks", 27: "Tampa Bay Buccaneers", 28: "Washington Commanders",
            29: "Carolina Panthers", 30: "Jacksonville Jaguars", 33: "Baltimore Ravens", 34: "Houston Texans"
        }
        pro_id_to_abbrev = {
            1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
            9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
            17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
            25: "SF", 26: "SEA", 27: "TB", 28: "WSH", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU"
        }

    roster = team_obj.get("roster", {})
    entries = roster.get("entries", [])

    # Some nice-to-have info for printing
    team_name = f"{team_obj.get('location','').strip()} {team_obj.get('nickname','').strip()}".strip()
    if not team_name.strip():
        team_name = f"Team {team_id}"

    rows = []
    for e in entries:
        player = (e.get("playerPoolEntry") or {}).get("player") or {}
        full_name = player.get("fullName", "Unknown")
        default_pos_id = player.get("defaultPositionId")
        pro_team_id = player.get("proTeamId")
        injury_status = player.get("injuryStatus") or ""
        lineup_slot_id = e.get("lineupSlotId")
        
        # Get projected stats for current week
        projected_points = 0
        stats = player.get("stats", [])
        for stat in stats:
            if stat.get("statSourceId") == 1 and stat.get("scoringPeriodId") == week:  # Projected stats
                projected_points = stat.get("appliedTotal", 0)
                break
        
        # If no weekly projection found, try season projection
        if projected_points == 0:
            for stat in stats:
                if stat.get("statSourceId") == 1:  # Projected stats
                    projected_points = stat.get("appliedTotal", 0) / 17  # Rough weekly average
                    break

        rows.append({
            "Lineup Slot": slot_id_to_name.get(lineup_slot_id, str(lineup_slot_id)),
            "Player": full_name,
            "Pos": pos_id_to_name.get(default_pos_id, str(default_pos_id)),
            "NFL Team": pro_id_to_name.get(pro_team_id, f"ProTeam {pro_team_id}"),
            "NFL": pro_id_to_abbrev.get(pro_team_id, ""),
            "Proj": f"{projected_points:.1f}",
            "Injury": injury_status,
        })

    # Sort by lineup slot name (benches at the bottom typically have 'Bench' or slotId 20)
    rows.sort(key=lambda r: (r["Lineup Slot"], r["Player"]))
    return team_name, rows

def print_roster_table(team_name, rows, week=None):
    title = f"{team_name} — Roster"
    if week is not None:
        title += f" (Week {week})"
    print("\n" + title)
    print("-" * len(title))

    # Compute column widths
    cols = ["Lineup Slot", "Player", "Pos", "NFL Team", "NFL", "Proj", "Injury"]
    widths = {c: len(c) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row[c])))

    # Header
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))

    # Rows
    for row in rows:
        line = " | ".join(str(row[c]).ljust(widths[c]) for c in cols)
        print(line)

if __name__ == "__main__":
    # Safety check: nudge if cookies look unset
    if not ESPN_S2 or "PUT_YOUR_ESPN_S2_HERE" in ESPN_S2:
        print("⚠️  ESPN_S2 not set. Set ESPN_S2 env var or update the literal.")
    if not SWID or "PUT-YOUR-SWID-HERE" in SWID:
        print("⚠️  SWID not set. Set SWID env var or update the literal.")


    team_name, roster_rows = get_team_roster(LEAGUE_ID, TEAM_ID, week=WEEK)
    print_roster_table(team_name, roster_rows, week=WEEK)
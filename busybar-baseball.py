#!/usr/bin/env python3
import time
import requests
from busylib import BusyBar, types
from busylib.exceptions import BusyBarRequestError

BUSYBAR_IP = "add IP here"
CHECK_INTERVAL_LIVE = 30    # Poll every 30 seconds during live games
CHECK_INTERVAL_IDLE = 300   # Poll every 5 minutes when no game is on
ESPN_MLB_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

bb = BusyBar(BUSYBAR_IP, timeout=10.0)

def get_jays_game_status():
    """Queries ESPN MLB API for live Blue Jays game status."""
    try:
        res = requests.get(ESPN_MLB_URL, timeout=5)
        if res.status_code != 200:
            return None
        
        data = res.json()
        events = data.get("events", [])
        
        for event in events:
            short_name = event.get("shortName", "")
            if "TOR" not in short_name:
                continue

            competition = event.get("competitions", [])[0]
            status = event.get("status", {})
            state = status.get("type", {}).get("state")  # 'pre', 'in', or 'post'

            # Only process and return data if the game is LIVE ('in')
            if state == "in":
                competitors = competition.get("competitors", [])
                jays = next(c for c in competitors if c["team"]["abbreviation"] == "TOR")
                opponent = next(c for c in competitors if c["team"]["abbreviation"] != "TOR")

                jays_score = str(jays.get("score", "0"))
                opp_score = str(opponent.get("score", "0"))
                opp_abbr = opponent["team"]["abbreviation"]

                # Remove space around dash on double digits to tighten width
                if len(jays_score) > 1 or len(opp_score) > 1:
                    return f"TOR {jays_score}-{opp_score} {opp_abbr}"
                else:
                    return f"TOR {jays_score}-{opp_score} {opp_abbr}"
    except Exception as e:
        print(f"Error fetching ESPN status: {e}")

    return None

def update_display(score_text):
    if score_text:
        is_long = len(score_text) > 11
        
        # Switch to condensed font if score length pushes screen boundary
        font_style = "condensed" if is_long else "bold"

        score_el = types.TextElement(
            id="jays_score",
            type="text",
            x=1,
            y=2,
            text=score_text,
            color="#0066CC",  # Blue Jays Royal Blue
            font=font_style,
            display=types.DisplayName.FRONT
        )
        display_data = types.DisplayElements(
            application_name="jays_tracker",
            elements=[score_el]
        )
        try:
            res = bb.display_draw(display_data)
            print(f"Jays Live -> {score_text} ({res})")
        except (BusyBarRequestError, Exception) as e:
            print(f"Draw notice: {e}")
    else:
        try:
            res = bb.display_clear()
            print("No live Jays game. Display cleared.")
        except (BusyBarRequestError, Exception) as e:
            print(f"Clear notice: {e}")

def main():
    currently_showing = False
    print("Starting Blue Jays Score Tracker...")

    while True:
        score_text = get_jays_game_status()

        if score_text:
            update_display(score_text)
            currently_showing = True
            time.sleep(CHECK_INTERVAL_LIVE)
        else:
            if currently_showing:
                update_display(None)  # Clear screen once when live game ends
                currently_showing = False
            time.sleep(CHECK_INTERVAL_IDLE)

if __name__ == "__main__":
    main()

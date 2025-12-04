#!/usr/bin/env python3
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ============================================================
# Load environment variables
# ============================================================
load_dotenv()

KENPOM_USERNAME = os.getenv("KENPOM_USERNAME")
KENPOM_PASSWORD = os.getenv("KENPOM_PASSWORD")

OX_HOST = os.getenv("OX_HOST", "pr.oxylabs.io")
OX_PORT = os.getenv("OX_PORT", "7777")
OX_USER = os.getenv("OX_USER")
OX_PASS = os.getenv("OX_PASS")

if not KENPOM_USERNAME or not KENPOM_PASSWORD:
    print("❌ Missing KenPom credentials.")
    sys.exit(1)

if not OX_USER or not OX_PASS:
    print("❌ Missing Oxylabs proxy credentials.")
    sys.exit(1)

PROXY_SERVER = f"http://{OX_HOST}:{OX_PORT}"

# ============================================================
# Helpers
# ============================================================
def clean_team_name(text: str) -> str:
    return re.sub(r"^\s*\d+\s+", "", text).strip()

def extract_teams(matchup_text: str):
    parts = re.split(r"\s+at\s+", matchup_text, flags=re.IGNORECASE)
    if len(parts) == 2:
        return clean_team_name(parts[0]), clean_team_name(parts[1])
    return matchup_text.strip(), ""

def parse_prediction(pred: str, team1: str, team2: str):
    parsed = {
        "team1_score": "",
        "team2_score": "",
        "predicted_winner": "",
        "win_probability": "",
        "tempo": "",
    }

    pattern = r"(.+?)\s+(\d+)-(\d+)\s+\((\d+)%\)\s+\[(\d+)\]"
    m = re.match(pattern, pred)
    if not m:
        return parsed

    winner, sw, sl, pct, tempo = m.groups()
    parsed["predicted_winner"] = winner.strip()
    parsed["win_probability"] = pct
    parsed["tempo"] = tempo

    wl = winner.lower().strip()
    t1 = team1.lower().strip()
    t2 = team2.lower().strip()

    if wl == t1:
        parsed["team1_score"] = sw
        parsed["team2_score"] = sl
    elif wl == t2:
        parsed["team1_score"] = sl
        parsed["team2_score"] = sw

    return parsed

# ============================================================
# Main scraper using correct FANMATCH URL
# ============================================================
def main():
    # KenPom uses ET — not UTC — for daily matchups
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    target_url = f"https://kenpom.com/fanmatch.php?d={today}"

    print(f"🗓 Using US date: {today}")
    print(f"📊 Scraping URL: {target_url}")

    with sync_playwright() as p:

        print("🚀 Launching Chrome with Oxylabs proxy...")

        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            proxy={
                "server": PROXY_SERVER,
                "username": OX_USER,
                "password": OX_PASS,
            },
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        # --------------------------
        # LOGIN SEQUENCE
        # --------------------------
        print("🔍 Loading login page...")
        page.goto("https://kenpom.com", wait_until="networkidle", timeout=60000)

        print("🔐 Logging in...")
        page.fill("input[name=email]", KENPOM_USERNAME)
        page.fill("input[name=password]", KENPOM_PASSWORD)
        page.click("input[type=submit]")

        page.wait_for_load_state("networkidle", timeout=60000)

        # --------------------------
        # LOAD FANMATCH PAGE
        # --------------------------
        print("📊 Navigating to FANMATCH page...")
        page.goto(target_url, wait_until="networkidle", timeout=60000)

        html = page.content().lower()

        # Cloudflare detection
        if "cloudflare" in html or "attention required" in html:
            print("⚠️ Cloudflare challenge detected! Saving screenshot + HTML...")
            page.screenshot(path="error_screenshot.png", full_page=True)
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            sys.exit(1)

        print("🕐 Waiting for FANMATCH table...")

        try:
            table = page.locator("table.fanmatch-table")
            table.wait_for(timeout=15000)
        except PlaywrightTimeoutError:
            print("❌ FANMATCH table NOT FOUND — saving screenshot + page HTML...")
            page.screenshot(path="error_screenshot.png", full_page=True)
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            sys.exit(1)

        print("📈 Extracting rows...")

        rows = table.locator("tr")
        row_count = rows.count()
        print(f"🔢 Found {row_count-1} matchup rows.")

        matchups = []

        for i in range(1, row_count):
            cells = rows.nth(i).locator("td")
            if cells.count() < 4:
                continue

            matchup = cells.nth(0).inner_text().strip()
            pred = cells.nth(3).inner_text().strip()

            team1, team2 = extract_teams(matchup)
            parsed = parse_prediction(pred, team1, team2)

            matchups.append({
                "Date": today,
                "Team1": team1,
                "Team2": team2,
                "Team1_Predicted_Score": parsed["team1_score"],
                "Team2_Predicted_Score": parsed["team2_score"],
                "Predicted_Winner": parsed["predicted_winner"],
                "Win_Probability": parsed["win_probability"],
                "Tempo": parsed["tempo"],
                "Full_Prediction": pred,
            })

        # --------------------------
        # WRITE CSV
        # --------------------------
        out = "daily_matchups.csv"
        print(f"💾 Saving {len(matchups)} matchups → {out}")

        with open(out, "w", encoding="utf-8") as f:
            f.write(
                "Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,"
                "Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n"
            )
            for m in matchups:
                f.write(
                    f'{m["Date"]},"{m["Team1"]}","{m["Team2"]}",'
                    f'{m["Team1_Predicted_Score"]},{m["Team2_Predicted_Score"]},'
                    f'"{m["Predicted_Winner"]}",{m["Win_Probability"]},'
                    f'{m["Tempo"]},"{m["Full_Prediction"]}"\n'
                )

        print("✅ DONE — FANMATCH successfully scraped.")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()

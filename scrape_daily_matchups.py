#!/usr/bin/env python3
import os
import re
import sys
from datetime import datetime
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
OX_USER = os.getenv("OX_USER")  # set in GitHub secrets
OX_PASS = os.getenv("OX_PASS")  # set in GitHub secrets

if not KENPOM_USERNAME or not KENPOM_PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD")
    sys.exit(1)

if not OX_USER or not OX_PASS:
    print("❌ Missing OX_USER or OX_PASS for Oxylabs proxy")
    sys.exit(1)

PROXY_SERVER = f"http://{OX_HOST}:{OX_PORT}"

# ============================================================
# Helper functions
# ============================================================
def clean_team_name(text: str) -> str:
    """Remove seed numbers and clean whitespace."""
    return re.sub(r"^\s*\d+\s+", "", text).strip()

def extract_teams_from_matchup(matchup_text: str):
    """Extract Team1 and Team2 from 'X Team at Y Team'."""
    parts = re.split(r"\s+at\s+", matchup_text, flags=re.IGNORECASE)
    if len(parts) == 2:
        return clean_team_name(parts[0]), clean_team_name(parts[1])
    return matchup_text.strip(), ""

def parse_prediction(pred_text: str, team1: str, team2: str):
    """
    Parse prediction like: 'Louisville 84-81 (61%) [73]'
    Return dict with scores, winner, win_probability, tempo.
    """
    parsed = {
        "team1_score": "",
        "team2_score": "",
        "predicted_winner": "",
        "win_probability": "",
        "tempo": ""
    }

    if not pred_text:
        return parsed

    pattern = r"(.+?)\s+(\d+)-(\d+)\s+\((\d+)%\)\s+\[(\d+)\]"
    m = re.match(pattern, pred_text)
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
# Main scraping logic using Playwright
# ============================================================
def main():
    today = datetime.now().strftime("%Y-%m-%d")
    target_url = f"https://kenpom.com/gameplan.php?d={today}"
    print(f"🗓 Target date: {today}")
    print(f"📊 Target URL: {target_url}")

    with sync_playwright() as p:
        # Launch Chrome via Playwright with Oxylabs proxy
        print("🚀 Launching Playwright Chromium (Chrome channel) with Oxylabs proxy...")
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",  # use system Chrome installed by `playwright install chrome`
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
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # ---------------------------
            # Login
            # ---------------------------
            print("🔍 Navigating to KenPom login page...")
            page.goto("https://kenpom.com", wait_until="networkidle", timeout=60000)

            # Quick Cloudflare sanity check
            content_lower = page.content().lower()
            if "cloudflare" in content_lower and "attention required" in content_lower:
                print("⚠️ Cloudflare 'Attention Required' detected on initial load.")
                page.screenshot(path="error_screenshot.png", full_page=True)
                raise SystemExit(1)

            print("🔐 Filling login form...")
            page.fill('input[name="email"]', KENPOM_USERNAME)
            page.fill('input[name="password"]', KENPOM_PASSWORD)
            page.click('input[type="submit"]')

            page.wait_for_load_state("networkidle", timeout=60000)

            # ---------------------------
            # Navigate to Gameplan
            # ---------------------------
            print("📊 Navigating to daily Gameplan page...")
            page.goto(target_url, wait_until="networkidle", timeout=60000)

            # Another Cloudflare check
            content_lower = page.content().lower()
            if "cloudflare" in content_lower and "attention required" in content_lower:
                print("⚠️ Cloudflare challenge detected on Gameplan page.")
                page.screenshot(path="error_screenshot.png", full_page=True)
                raise SystemExit(1)

            # Wait for table
            print("🕐 Waiting for matchup table...")
            try:
                table_locator = page.locator(".gameplan")
                table_locator.wait_for(timeout=15000)
            except PlaywrightTimeoutError:
                print("❌ Matchup table not found within timeout. Saving screenshot...")
                page.screenshot(path="error_screenshot.png", full_page=True)
                raise SystemExit(1)

            # ---------------------------
            # Extract rows
            # ---------------------------
            print("📈 Extracting matchup rows...")
            rows = page.locator(".gameplan tr")
            row_count = rows.count()

            print(f"🔢 Found {row_count-1} data rows (excluding header).")

            matchups = []

            for i in range(1, row_count):  # skip header (row 0)
                row = rows.nth(i)
                cells = row.locator("td")
                if cells.count() < 4:
                    continue

                matchup_text = cells.nth(0).inner_text().strip()
                pred_text = cells.nth(3).inner_text().strip()

                team1, team2 = extract_teams_from_matchup(matchup_text)
                parsed = parse_prediction(pred_text, team1, team2)

                matchups.append({
                    "Date": today,
                    "Team1": team1,
                    "Team2": team2,
                    "Team1_Predicted_Score": parsed["team1_score"],
                    "Team2_Predicted_Score": parsed["team2_score"],
                    "Predicted_Winner": parsed["predicted_winner"],
                    "Win_Probability": parsed["win_probability"],
                    "Tempo": parsed["tempo"],
                    "Full_Prediction": pred_text,
                })

            # ---------------------------
            # Save CSV
            # ---------------------------
            output_path = "daily_matchups.csv"
            print(f"💾 Saving {len(matchups)} matchups to {output_path}...")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n")
                for m in matchups:
                    f.write(
                        f'{m["Date"]},"{m["Team1"]}","{m["Team2"]}",'
                        f'{m["Team1_Predicted_Score"]},{m["Team2_Predicted_Score"]},'
                        f'"{m["Predicted_Winner"]}",{m["Win_Probability"]},{m["Tempo"]},"{m["Full_Prediction"]}"\n'
                    )

            print("✅ Done.")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()

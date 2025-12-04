#!/usr/bin/env python3
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD.")
    sys.exit(1)

# ----------------------------
# Helper functions
# ----------------------------
def clean_team_name(text):
    """Remove seed numbers from team name."""
    return re.sub(r'^\s*\d+\s+', '', text).strip()

def extract_teams_from_matchup(matchup_text):
    """Split 'Team1 at Team2'."""
    parts = re.split(r"\s+at\s+", matchup_text, flags=re.IGNORECASE)
    return (clean_team_name(parts[0]), clean_team_name(parts[1])) if len(parts) == 2 else (matchup_text, "")

def parse_prediction(pred_text, team1, team2):
    """Parse prediction like: Louisville 84-81 (61%) [73]"""
    parsed = {
        "team1_score": "",
        "team2_score": "",
        "predicted_winner": "",
        "win_probability": "",
        "tempo": ""
    }

    if not pred_text:
        return parsed

    pattern = r'(.+?)\s+(\d+)-(\d+)\s+\((\d+)%\)\s+\[(\d+)\]'
    m = re.match(pattern, pred_text)
    if not m:
        return parsed

    winner, score_w, score_l, winpct, tempo = m.groups()
    parsed["predicted_winner"] = winner.strip()
    parsed["win_probability"] = winpct
    parsed["tempo"] = tempo

    w = winner.lower().strip()
    t1 = team1.lower().strip()
    t2 = team2.lower().strip()

    if w == t1:
        parsed["team1_score"] = score_w
        parsed["team2_score"] = score_l
    elif w == t2:
        parsed["team1_score"] = score_l
        parsed["team2_score"] = score_w

    return parsed

# ----------------------------
# Start Stealth Browser
# ----------------------------
print("🚀 Launching undetected Chrome...")

driver = uc.Chrome(
    headless=False,   # MUST be false for Cloudflare
    use_subprocess=True
)
wait = WebDriverWait(driver, 20)

# ----------------------------
# LOGIN
# ----------------------------
print("🔍 Navigating to KenPom login page...")
driver.get("https://kenpom.com/")

# Wait for login fields
username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
password_field = driver.find_element(By.NAME, "password")

print("🔐 Logging in...")
username_field.send_keys(USERNAME)
password_field.send_keys(PASSWORD)

driver.find_element(By.XPATH, '//input[@type="submit"]').click()
time.sleep(3)

# ----------------------------
# NAVIGATE TO DAILY MATCHUPS
# ----------------------------
today = datetime.now().strftime("%Y-%m-%d")
url = f"https://kenpom.com/gameplan.php?d={today}"

print(f"📊 Navigating to daily matchups: {url}")
driver.get(url)
time.sleep(2)

# Wait for table
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gameplan")))

rows = driver.find_elements(By.CSS_SELECTOR, ".gameplan tr")
matchups = []

print("📈 Scraping matchups...")

for row in rows[1:]:
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) < 4:
        continue

    matchup_text = cells[0].text.strip()
    pred_text = cells[3].text.strip()

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
        "Full_Prediction": pred_text
    })

# ----------------------------
# SAVE CSV
# ----------------------------
output = "daily_matchups.csv"
print(f"💾 Saving to {output} ...")

with open(output, "w", encoding="utf-8") as f:
    f.write("Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n")
    for m in matchups:
        f.write(
            f'{m["Date"]},"{m["Team1"]}","{m["Team2"]}",'
            f'{m["Team1_Predicted_Score"]},{m["Team2_Predicted_Score"]},'
            f'"{m["Predicted_Winner"]}",{m["Win_Probability"]},{m["Tempo"]},"{m["Full_Prediction"]}"\n'
        )

driver.quit()
print(f"✅ Scraped {len(matchups)} matchups successfully!")

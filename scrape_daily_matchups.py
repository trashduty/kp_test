#!/usr/bin/env python3
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc


# ============================================
# Load credentials + proxy
# ============================================
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

# --- Oxylabs residential proxy ---
PROXY_HOST = "pr.oxylabs.io"
PROXY_PORT = "7777"
PROXY_USER = "customer-bullytheboard_OnFjP-cc-US"
PROXY_PASS = "Btb_analytics1"

PROXY_STRING = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

if not USERNAME or not PASSWORD:
    print("❌ Missing KenPom credentials.")
    sys.exit(1)


# ============================================
# Helper Functions
# ============================================
def clean_team_name(text):
    return re.sub(r'^\s*\d+\s+', '', text).strip()

def extract_teams_from_matchup(matchup_text):
    parts = re.split(r"\s+at\s+", matchup_text, flags=re.IGNORECASE)
    if len(parts) == 2:
        return clean_team_name(parts[0]), clean_team_name(parts[1])
    return matchup_text, ""

def parse_prediction(pred_text, team1, team2):
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


# ============================================
# Launch undetected Chrome WITH PROXY
# ============================================
print("🚀 Launching Chrome with Oxylabs proxy...")

chrome_options = uc.ChromeOptions()
chrome_options.binary_location = "/usr/bin/google-chrome"

# Proxy injected here:
chrome_options.add_argument(f"--proxy-server={PROXY_STRING}")

# Container-safe flags:
flags = [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-breakpad",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--disable-features=AutomationControlled",
    "--disable-client-side-phishing-detection",
    "--disable-default-apps",
    "--mute-audio",
    "--no-first-run",
    "--no-zygote",
    "--window-size=1920,1080",
]
for f in flags:
    chrome_options.add_argument(f)

# CRITICAL: Force Chromedriver 142 to match Linux Chrome
driver = uc.Chrome(
    options=chrome_options,
    use_subprocess=True,
    version_main=142
)

wait = WebDriverWait(driver, 20)


# ============================================
# LOGIN FLOW
# ============================================
print("🔍 Navigating to KenPom login...")
driver.get("https://kenpom.com/")
time.sleep(2)

try:
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_field = driver.find_element(By.NAME, "password")
except Exception:
    print("❌ Login form not detected (Cloudflare still active). Saving screenshot...")
    driver.save_screenshot("error_screenshot.png")
    driver.quit()
    sys.exit(1)

print("🔐 Logging in...")
username_field.send_keys(USERNAME)
password_field.send_keys(PASSWORD)
driver.find_element(By.XPATH, "//input[@type='submit']").click()
time.sleep(3)


# ============================================
# LOAD MATCHUPS PAGE
# ============================================
today = datetime.now().strftime("%Y-%m-%d")
url = f"https://kenpom.com/gameplan.php?d={today}"

print(f"📊 Navigating to: {url}")
driver.get(url)
time.sleep(3)

try:
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gameplan")))
except Exception:
    print("❌ Matchup table not found. Saving screenshot...")
    driver.save_screenshot("error_screenshot.png")
    driver.quit()
    sys.exit(1)


# ============================================
# SCRAPE TABLE
# ============================================
print("📈 Scraping matchups...")

rows = driver.find_elements(By.CSS_SELECTOR, ".gameplan tr")
matchups = []

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


# ============================================
# SAVE CSV
# ============================================
output = "daily_matchups.csv"
print(f"💾 Saving: {output}")

with open(output, "w", encoding="utf-8") as f:
    f.write("Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n")
    for m in matchups:
        f.write(
            f'{m["Date"]},"{m["Team1"]}","{m["Team2"]}",'
            f'{m["Team1_Predicted_Score"]},{m["Team2_Predicted_Score"]},'
            f'"{m["Predicted_Winner"]}",{m["Win_Probability"]},{m["Tempo"]},"{m["Full_Prediction"]}"\n'
        )

print(f"✅ Successfully scraped {len(matchups)} matchups!")
driver.quit()
print("🏁 Done.")

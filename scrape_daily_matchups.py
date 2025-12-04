#!/usr/bin/env python3
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Selenium imports
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Undetected ChromeDriver
import undetected_chromedriver as uc

# ============================================
# Load credentials
# ============================================
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ ERROR: Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment.")
    sys.exit(1)

# ============================================
# Helper Functions
# ============================================
def clean_team_name(text):
    """Removes seed numbers from team names."""
    return re.sub(r'^\s*\d+\s+', '', text).strip()

def extract_teams_from_matchup(matchup_text):
    """Extracts Team1 and Team2 from a string like '9 Louisville at 37 Arkansas'."""
    parts = re.split(r"\s+at\s+", matchup_text, flags=re.IGNORECASE)
    if len(parts) == 2:
        return clean_team_name(parts[0]), clean_team_name(parts[1])
    return matchup_text, ""

def parse_prediction(pred_text, team1, team2):
    """
    Parses prediction text: 'Louisville 84-81 (61%) [73]'
    Returns structured information.
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

    pattern = r'(.+?)\s+(\d+)-(\d+)\s+\((\d+)%\)\s+\[(\d+)\]'
    match = re.match(pattern, pred_text)
    if not match:
        return parsed

    winner, score_w, score_l, winpct, tempo = match.groups()
    parsed["predicted_winner"] = winner.strip()
    parsed["win_probability"] = winpct
    parsed["tempo"] = tempo

    winner_l = winner.lower().strip()
    t1_l = team1.lower().strip()
    t2_l = team2.lower().strip()

    # Winner = Team1
    if winner_l == t1_l:
        parsed["team1_score"] = score_w
        parsed["team2_score"] = score_l

    # Winner = Team2
    elif winner_l == t2_l:
        parsed["team1_score"] = score_l
        parsed["team2_score"] = score_w

    return parsed

# ============================================
# Launch Cloudflare-Safe Undetected Chrome
# ============================================
print("🚀 Launching undetected Chrome...")

chrome_options = uc.ChromeOptions()
chrome_options.binary_location = "/usr/bin/google-chrome"

# Required GitHub Actions flags
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

driver = uc.Chrome(
    options=chrome_options,
    use_subprocess=True
)

wait = WebDriverWait(driver, 20)

# ============================================
# LOGIN
# ============================================
print("🔍 Navigating to KenPom login page...")
driver.get("https://kenpom.com/")

try:
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
except:
    print("❌ Could not load login form. Cloudflare may still be blocking.")
    driver.quit()
    sys.exit(1)

password_field = driver.find_element(By.NAME, "password")

print("🔐 Logging in...")
username_field.send_keys(USERNAME)
password_field.send_keys(PASSWORD)

driver.find_element(By.XPATH, '//input[@type="submit"]').click()
time.sleep(3)

# ============================================
# Navigate to Daily Matchups
# ============================================
today = datetime.now().strftime("%Y-%m-%d")
url = f"https://kenpom.com/gameplan.php?d={today}"

print(f"📊 Navigating to Gameplan page: {url}")
driver.get(url)
time.sleep(2)

try:
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gameplan")))
except:
    print("❌ Matchup table failed to load.")
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
output_path = "daily_matchups.csv"
print(f"💾 Saving to {output_path}...")

with open(output_path, "w", encoding="utf-8") as f:
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

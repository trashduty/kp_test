import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load login credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Configure headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Initialize WebDriver
# Try to use chromedriver from environment or common locations
chromedriver_path = os.getenv("CHROMEDRIVER_BIN")
if not chromedriver_path:
    # Try common paths for chromedriver
    common_paths = ["/usr/bin/chromedriver", "/usr/local/bin/chromedriver"]
    for path in common_paths:
        if os.path.exists(path):
            chromedriver_path = path
            break

if chromedriver_path:
    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"Using chromedriver at: {chromedriver_path}")
    except Exception as e:
        # Fallback to default behavior if service initialization fails
        print(f"Warning: Could not initialize with service at {chromedriver_path}, trying default: {e}")
        driver = webdriver.Chrome(options=chrome_options)
else:
    # Let selenium find chromedriver automatically
    driver = webdriver.Chrome(options=chrome_options)

# Prevent Selenium detection
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("[1/5] Logging into KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    print("[2/5] ✅ Login successful")

    print("[3/5] Navigating to FanMatch page...")
    driver.get("https://kenpom.com/fanmatch.php")
    time.sleep(4)

    # Extract the date being shown
    date_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "lh12")))
    date_text = date_div.text
    print(f"[4/5] Found matchups: {date_text}")

    # Find the FanMatch table
    fanmatch_table = wait.until(EC.presence_of_element_located((By.ID, "fanmatch-table")))
    table_html = fanmatch_table.get_attribute("outerHTML")

    print("[4/5] Reading matchup table into pandas...")
    tables = pd.read_html(StringIO(table_html))
    
    if len(tables) == 0:
        print("❌ No tables found in FanMatch page")
        sys.exit(1)
    
    df = tables[0]
    
    # The FanMatch table typically has columns like: Matchup, Time, Network, etc.
    # We need to extract team names from the matchup column
    print(f"[5/5] Found {len(df)} matchups")
    print(f"Columns: {df.columns.tolist()}")
    
    # Parse matchups - typically in format "Team1 vs Team2" or "Team1 @ Team2"
    matchups = []
    
    # Check what column contains the matchup information
    matchup_col = None
    for col in df.columns:
        if 'matchup' in col.lower():
            matchup_col = col
            break
    
    if matchup_col is None:
        matchup_col = df.columns[0]  # Default to first column
    
    print(f"Using column '{matchup_col}' for matchup data")
    
    # Validate that the column contains matchup-like data
    sample_value = str(df[matchup_col].iloc[0]) if len(df) > 0 else ""
    if not any(delimiter in sample_value for delimiter in [' vs ', ' @ ', ' vs. ', ' at ']):
        print(f"Warning: First value in '{matchup_col}' doesn't appear to contain matchup data: {sample_value}")
    
    for idx, row in df.iterrows():
        matchup_text = str(row[matchup_col])
        
        # Skip header rows or invalid entries using proper pandas methods
        if pd.isna(row[matchup_col]) or matchup_text == '' or 'Matchup' in matchup_text:
            continue
        
        # Parse team names from matchup text
        # Common formats: "Team1 vs Team2", "Team1 @ Team2", "Team1 vs. Team2"
        teams = []
        if ' vs. ' in matchup_text:
            teams = matchup_text.split(' vs. ')
        elif ' vs ' in matchup_text:
            teams = matchup_text.split(' vs ')
        elif ' @ ' in matchup_text:
            teams = matchup_text.split(' @ ')
        elif ' at ' in matchup_text:
            teams = matchup_text.split(' at ')
        
        if len(teams) >= 2:
            matchups.append({
                'team1': teams[0].strip(),
                'team2': teams[1].strip(),
                'matchup': matchup_text
            })
        else:
            # If no delimiter found, try to use the whole text as a single team
            # This might happen if table structure is different
            if matchup_text.strip():
                print(f"Warning: Could not parse matchup format: {matchup_text}")
                matchups.append({
                    'team1': matchup_text.strip(),
                    'team2': '',
                    'matchup': matchup_text
                })
    
    # Create DataFrame with matchups
    matchups_df = pd.DataFrame(matchups)
    
    # Get all unique teams playing
    all_teams = []
    if len(matchups_df) > 0:
        all_teams = pd.concat([matchups_df['team1'], matchups_df['team2']]).unique().tolist()
        all_teams = [t for t in all_teams if t and t != '']
    
    print(f"\nExtracted {len(all_teams)} unique teams from {len(matchups_df)} matchups")
    
    # Create a simple CSV with teams playing tomorrow
    teams_df = pd.DataFrame({'Team': all_teams})
    
    # Save to CSV (even if empty, so the R script doesn't error)
    final_path = os.path.abspath("daily_matchups.csv")
    teams_df.to_csv(final_path, index=False)
    print(f"[5/5] ✅ Daily matchups saved: {final_path} ({len(teams_df)} teams)")
    
    # Also save the full matchup details
    matchups_path = os.path.abspath("daily_matchups_full.csv")
    matchups_df.to_csv(matchups_path, index=False)
    print(f"[5/5] ✅ Full matchup details saved: {matchups_path} ({len(matchups_df)} matchups)")
    
    if len(teams_df) == 0:
        print("\n⚠️ Warning: No teams found in matchups. This might indicate the page structure has changed.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()

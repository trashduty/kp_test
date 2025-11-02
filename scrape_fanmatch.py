import os
import sys
import time
import re
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
driver = webdriver.Chrome(options=chrome_options)

# Prevent Selenium detection
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("[1/7] Logging into KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    print("[2/7] ✅ Login successful")

    # Get tomorrow's date for the FanMatch URL
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    
    print(f"[3/7] Navigating to FanMatch page for {tomorrow_str}...")
    driver.get(f"https://kenpom.com/fanmatch.php?d={tomorrow_str}")
    time.sleep(4)

    # Create kenpom-data directory if it doesn't exist
    os.makedirs("kenpom-data", exist_ok=True)

    print("[4/7] Extracting FanMatch data...")
    fanmatch_table = wait.until(EC.presence_of_element_located((By.ID, "fanmatch-table")))
    
    # Save the raw HTML
    html_path = os.path.join("kenpom-data", f"fanmatch-{tomorrow_str}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"[5/7] ✅ Raw HTML saved: {html_path}")

    # Extract table data
    table_html = fanmatch_table.get_attribute("outerHTML")
    df = pd.read_html(StringIO(table_html))[0]

    # Clean up the table
    print("[6/7] Processing FanMatch data...")
    
    # Remove any header-like rows and reset index
    if len(df.columns) > 0:
        df_cleaned = df.dropna(how='all').copy()
        df_cleaned.reset_index(drop=True, inplace=True)
    else:
        raise ValueError("❌ Could not find any columns in the FanMatch table.")

    # Save processed version
    final_path = os.path.join("kenpom-data", f"fanmatch-{tomorrow_str}.csv")
    df_cleaned.to_csv(final_path, index=False)
    print(f"[7/7] ✅ Cleaned CSV saved: {final_path} (Rows: {len(df_cleaned)})")

    # Extract team names from Game column for daily matchups
    print("\n[8/9] Extracting team names from Game column...")
    teams = []
    
    if 'Game' in df_cleaned.columns:
        for game in df_cleaned['Game']:
            if pd.isna(game):
                continue
            
            # Split by "vs." or "at" to get both teams
            if ' vs. ' in game:
                parts = game.split(' vs. ')
            elif ' at ' in game:
                parts = game.split(' at ')
            else:
                continue
            
            for part in parts:
                # Remove rankings (numbers or "NR") at the beginning using regex
                # Pattern: ^(NR|\d+)\s+ means start with NR or digits followed by spaces
                part = part.strip()
                part = re.sub(r'^(NR|\d+)\s+', '', part)
                part = part.strip()
                if part:
                    teams.append(part)
    
    # Create DataFrame with unique teams
    if teams:
        matchups_df = pd.DataFrame({'Team': sorted(set(teams))})
        matchups_path = "daily_matchups.csv"
        matchups_df.to_csv(matchups_path, index=False)
        print(f"[9/9] ✅ Daily matchups saved: {matchups_path} (Teams: {len(matchups_df)})")
        print(f"\nExtracted teams: {', '.join(matchups_df['Team'].head(10).tolist())}...")
    else:
        print("[9/9] ⚠️ No teams extracted from Game column")

    # Print preview of games
    print("\nTomorrow's Games Preview:")
    print(df_cleaned.head())

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

finally:
    driver.quit()

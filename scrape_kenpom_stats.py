import os
import sys
import time
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load credentials from .env or GitHub secrets
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment.")
    sys.exit(1)

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-blink-features')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('user-agent=Mozilla/5.0')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)

# Hide Selenium signature
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("[1/5] Navigating to KenPom login page...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    # Login form
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(3)
    print("[2/5] Logged in successfully")

    # Go to stats table
    stats_url = "https://kenpom.com/stats.php"
    driver.get(stats_url)
    print(f"[3/5] Navigated to {stats_url}")
    time.sleep(5)

    # Get table HTML
    stats_table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))
    table_html = stats_table.get_attribute("outerHTML")

    print("[4/5] Reading HTML table into pandas (multi-level headers)...")
    df = pd.read_html(StringIO(table_html), header=[0, 1])[0]

    # Flatten multi-level columns
    df.columns = [' '.join(col).strip() for col in df.columns.values]

    # Detect the 'Team' column (which includes rank)
    team_col = next((col for col in df.columns if "Team" in str(col)), None)

    if not team_col:
        print("❌ Could not detect 'Team' column.")
        print("Columns:", df.columns.tolist())
        sys.exit(1)

    print(f"✅ Detected team column as: {team_col}")

    # Drop rows where team_col equals "Team" (duplicate headers)
    df = df[df[team_col] != "Team"].copy()

    # Clean team names: remove leading rank numbers like "1 Purdue"
    df[team_col] = df[team_col].str.replace(r"^\d+\s+", "", regex=True)

    # Rename for consistency
    df.rename(columns={team_col: "Team"}, inplace=True)

    # Save cleaned CSV
    output_path = os.path.abspath("kenpom_stats.csv")
    df.to_csv(output_path, index=False)
    print(f"[5/5] ✅ Saved cleaned CSV to: {output_path}")
    print(f"📊 Total rows saved: {len(df)}")

except Exception as e:
    print(f"❌ Error occurred: {e}")
    sys.exit(1)

finally:
    driver.quit()

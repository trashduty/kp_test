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

# Load credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD")
    sys.exit(1)

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=chrome_options)

# Hide automation footprint
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("[1/5] Logging in to KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    print("[2/5] ✅ Logged in")

    print("[3/5] Navigating to stats page...")
    driver.get("https://kenpom.com/stats.php")
    time.sleep(4)

    stats_table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))
    table_html = stats_table.get_attribute("outerHTML")

    print("[4/5] Reading table into pandas...")
    df = pd.read_html(StringIO(table_html), header=[0, 1])[0]

    # Flatten header: ("Offense", "eFG%") → "Offense eFG%"
    df.columns = [' '.join(col).strip() if not col[0].startswith("Unnamed") else col[1]
                  for col in df.columns.values]

    # Identify team column
    team_col = next((c for c in df.columns if "Team" in c), None)
    if not team_col:
        print("❌ 'Team' column not found")
        sys.exit(1)

    # Rename team column for consistency
    df.rename(columns={team_col: "Team"}, inplace=True)

    # Remove ranking prefix (e.g. "1 Purdue" → "Purdue")
    df["Team"] = df["Team"].astype(str).str.replace(r"^\d+\s+", "", regex=True)

    # Save raw CSV
    output_path = os.path.abspath("kenpom_stats.csv")
    df.to_csv(output_path, index=False)
    print(f"[5/5] ✅ Raw CSV saved to {output_path}")

    # Reload and drop rows where 'Team' is empty or NaN
    df_cleaned = pd.read_csv(output_path)
    df_cleaned = df_cleaned[df_cleaned["Team"].notna() & df_cleaned["Team"].str.strip().ne("")]
    df_cleaned.to_csv(output_path, index=False)

    print(f"✅ Cleaned CSV written to same file. Final rows: {len(df_cleaned)}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

finally:
    driver.quit()

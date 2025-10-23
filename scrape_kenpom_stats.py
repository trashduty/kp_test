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
    print("[1/6] Logging into KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    print("[2/6] ✅ Login successful")

    print("[3/6] Navigating to stats page...")
    driver.get("https://kenpom.com/index.php")
    time.sleep(4)

    stats_table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))
    table_html = stats_table.get_attribute("outerHTML")

    print("[4/6] Reading table into pandas...")
    df = pd.read_html(StringIO(table_html), header=[0, 1])[0]

    # Flatten multi-level headers
    df.columns = [
        ' '.join(col).strip() if not col[0].startswith("Unnamed") else col[1]
        for col in df.columns.values
    ]

    # Save raw version (optional)
    raw_path = os.path.abspath("kenpom_stats_raw.csv")
    df.to_csv(raw_path, index=False)
    print(f"[5/6] Raw table saved: {raw_path}")

    # ✅ Remove all header-like rows: where Team == "Team" or is blank
    if "Team" in df.columns:
        df_cleaned = df[df["Team"].notna() & (df["Team"] != "Team")].copy()
        df_cleaned.reset_index(drop=True, inplace=True)
    else:
        raise ValueError("❌ Could not find a 'Team' column.")

    # Save cleaned version
    final_path = os.path.abspath("kenpom_stats.csv")
    df_cleaned.to_csv(final_path, index=False)
    print(f"[6/6] ✅ Cleaned CSV saved: {final_path} (Rows: {len(df_cleaned)})")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

finally:
    driver.quit()

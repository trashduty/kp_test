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
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment.")
    sys.exit(1)

# Setup headless browser
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

# Hide webdriver signature
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

try:
    print("[1/5] Navigating to KenPom login page...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 20)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")

    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(3)
    print("[2/5] Logged in successfully")

    stats_url = "https://kenpom.com/stats.php"
    driver.get(stats_url)
    print(f"[3/5] Navigated to {stats_url}")
    time.sleep(5)

    stats_table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))
    table_html = stats_table.get_attribute("outerHTML")

    print("[4/5] Reading HTML table into pandas...")
    df = pd.read_html(StringIO(table_html))[0]

    df["Team"] = df["Team"].str.replace(r"^\d+\s+", "", regex=True)

    if df.empty:
        print("⚠️ Warning: Extracted table is empty. No file will be saved.")
    else:
        output_path = os.path.abspath("kenpom_stats.csv")
        df.to_csv(output_path, index=False)
        print(f"[5/5] ✅ Saved CSV to: {output_path}")
        print("✅ Rows extracted:", len(df))

except Exception as e:
    print(f"❌ Error occurred: {e}")
    sys.exit(1)
finally:
    driver.quit()

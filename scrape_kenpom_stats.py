import os
import sys
import time
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load login credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize driver
try:
    driver = webdriver.Chrome(options=chrome_options)
    print("✅ Successfully initialized Chrome")
except Exception as e:
    print(f"❌ Failed to initialize Chrome: {e}")
    sys.exit(1)

try:
    # Navigate to login page
    print("🔍 Navigating to KenPom login...")
    driver.get("https://kenpom.com")
    time.sleep(2)

    # Find and fill the login form
    print("🔐 Logging in...")
    username_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    
    # Submit the form
    login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
    login_button.click()
    time.sleep(3)

    # Navigate to the stats page
    print("📊 Navigating to stats page...")
    driver.get("https://kenpom.com")
    time.sleep(2)

    # Wait for table to load
    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))

    # Get the page source and parse with pandas
    print("📈 Extracting data...")
    page_source = driver.page_source
    
    # Parse HTML tables
    tables = pd.read_html(StringIO(page_source))
    
    # The main table is usually the first one with the right structure
    df = None
    for table in tables:
        if len(table.columns) > 10:  # KenPom table has many columns
            df = table
            break
    
    if df is not None:
        # Save to CSV
        output_file = "kenpom_stats.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Successfully saved {len(df)} teams to {output_file}")
    else:
        print("❌ Could not find the stats table")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("🏁 Browser closed")

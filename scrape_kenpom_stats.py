import os
import sys
import time
import random
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load login credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Minimal, stable Chrome options for GitHub Actions
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Configure proxy with selenium-wire if enabled
proxy_enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
seleniumwire_options = {}

if proxy_enabled:
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    if proxy_server and proxy_username and proxy_password:
        proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_server}"
        seleniumwire_options = {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
        print(f"✅ Proxy enabled: Using Oxylabs ({proxy_server})")
    else:
        print("⚠️  Proxy enabled but credentials incomplete, running without proxy")
else:
    print("ℹ️  Proxy disabled, running with direct connection")

# Initialize driver with selenium-wire
try:
    if proxy_enabled and seleniumwire_options:
        # Use selenium-wire for proxy support
        from seleniumwire import webdriver
        
        # Create driver with selenium-wire options
        driver = uc.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options,
            version_main=None,
            use_subprocess=True
        )
    else:
        # Use regular undetected_chromedriver without proxy
        driver = uc.Chrome(
            options=chrome_options,
            version_main=None,
            use_subprocess=True
        )
    
    print("✅ Successfully initialized Chrome")
    
except Exception as e:
    print(f"❌ Failed to initialize Chrome: {e}")
    print("Attempting fallback to regular ChromeDriver...")
    
    try:
        if proxy_enabled and seleniumwire_options:
            from seleniumwire import webdriver
            driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
        else:
            from selenium import webdriver
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Successfully initialized Chrome with fallback")
    except Exception as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        sys.exit(1)

def random_delay(min_seconds=2, max_seconds=4):
    """Add random delay to simulate human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def scroll_page(driver):
    """Scroll the page to simulate human behavior"""
    try:
        # Scroll down slowly
        for i in range(3):
            scroll_amount = random.randint(300, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.3, 0.7))
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.5, 1.0))
    except Exception as e:
        print(f"⚠️ Could not scroll page: {e}")

def random_mouse_movement(driver):
    """Move mouse randomly to simulate human behavior"""
    try:
        action = ActionChains(driver)
        body = driver.find_element(By.TAG_NAME, "body")
        # Move to a random position
        action.move_to_element_with_offset(body, random.randint(100, 500), random.randint(100, 500)).perform()
        time.sleep(random.uniform(0.1, 0.3))
    except Exception as e:
        print(f"⚠️ Could not move mouse: {e}")

try:
    print("[1/6] Logging into KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 30)

    # Add random delay and mouse movement after page load
    random_delay(2, 3)
    random_mouse_movement(driver)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    
    # Type credentials with slight delays to simulate human typing
    for char in USERNAME:
        email_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    random_delay(0.5, 1)
    
    for char in PASSWORD:
        password_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    random_delay(0.5, 1)
    password_input.send_keys(Keys.RETURN)
    
    # Wait with random delay after login
    random_delay(3, 5)
    print("[2/6] ✅ Login successful")

    print("[3/6] Navigating to stats page...")
    
    # Add mouse movement before navigation
    random_mouse_movement(driver)
    random_delay(1, 2)
    
    try:
        driver.get("https://kenpom.com/index.php")
        time.sleep(5)  # Give more time for page to fully load
    except Exception as e:
        print(f"Navigation error: {e}")
        # Try to continue anyway
    
    # Wait and simulate human behavior after page load
    random_delay(3, 4)
    scroll_page(driver)
    random_delay(2, 3)

    stats_table = wait.until(EC.presence_of_element_located((By.ID, "ratings-table")))
    table_html = stats_table.get_attribute("outerHTML")

    print("[4/6] Reading table into pandas...")
    df = pd.read_html(StringIO(table_html), header=[0, 1])[0]

    # Flatten multi-level headers
    df.columns = [
        ' '.join(col).strip() if not col[0].startswith("Unnamed") else col[1]
        for col in df.columns.values
    ]

    # Rename duplicated or ambiguous columns
    rename_map = {
        "ORtg": "ORtg",
        "ORtg.1": "ORtg Rank",
        "DRtg": "DRtg",
        "DRtg.1": "DRtg Rank",
        "AdjT": "AdjT",
        "AdjT.1": "AdjT Rank",
        "Luck": "Luck",
        "Luck.1": "Luck Rank",
        "Strength of Schedule NetRtg": "SOS NetRtg",
        "Strength of Schedule NetRtg.1": "SOS NetRtg Rank",
        "Strength of Schedule ORtg": "SOS ORtg",
        "Strength of Schedule ORtg.1": "SOS ORtg Rank",
        "Strength of Schedule DRtg": "SOS DRtg",
        "Strength of Schedule DRtg.1": "SOS DRtg Rank",
        "NCSOS NetRtg": "NCSOS NetRtg",
        "NCSOS NetRtg.1": "NCSOS NetRtg Rank",
    }
    df.rename(columns=rename_map, inplace=True)

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
    # Take a screenshot for debugging
    try:
        screenshot_path = os.path.abspath("error_screenshot.png")
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved to: {screenshot_path}")
    except Exception as screenshot_error:
        print(f"⚠️ Could not save screenshot: {screenshot_error}")
    sys.exit(1)

finally:
    driver.quit()

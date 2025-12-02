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
from human_behavior import (
    random_delay,
    add_human_behavior_to_login,
    add_human_behavior_to_navigation,
    wait_for_page_load,
    simulate_reading
)

# Load login credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Enhanced Chrome options for better stealth and anti-detection
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")

# More realistic user agent
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Additional stealth options
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Disable automation flags
prefs = {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2,
}
chrome_options.add_experimental_option("prefs", prefs)

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
        
        # Note: When using proxy, we use selenium-wire's Chrome driver
        # This provides proxy authentication but without undetected-chromedriver features
        driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
    else:
        # Use regular undetected_chromedriver without proxy
        driver = uc.Chrome(
            options=chrome_options,
            version_main=None,
            use_subprocess=True
        )
    
    print("✅ Successfully initialized Chrome")
    
    # Inject stealth JavaScript to mask automation
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
            '''
        })
        print("✅ Stealth JavaScript injected")
    except Exception as e:
        print(f"⚠️  Could not inject stealth JavaScript: {e}")
    
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
        
        # Inject stealth JavaScript for fallback driver too
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
            print("✅ Stealth JavaScript injected (fallback)")
        except Exception as e:
            print(f"⚠️  Could not inject stealth JavaScript (fallback): {e}")
            
    except Exception as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        sys.exit(1)

try:
    print("[1/6] Logging into KenPom...")
    driver.get("https://kenpom.com/")
    wait = WebDriverWait(driver, 30)

    # Wait for page to load with human-like behavior
    wait_for_page_load(driver)
    random_delay(2, 4)  # Simulate looking at the page

    # Wait for login form elements
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_input = driver.find_element(By.NAME, "password")
    submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
    
    # Login with human-like behavior
    add_human_behavior_to_login(driver, email_input, password_input, submit_button, USERNAME, PASSWORD)
    
    # Wait for login to complete
    wait_for_page_load(driver)
    random_delay(2, 3)
    
    print("[2/6] ✅ Login successful")

    print("[3/6] Navigating to stats page...")
    
    # Add human behavior before navigating to stats page
    add_human_behavior_to_navigation(driver)
    
    try:
        driver.get("https://kenpom.com/index.php")
        time.sleep(5)  # Give more time for page to fully load
    except Exception as e:
        print(f"Navigation error: {e}")
        # Try to continue anyway
    
    # Wait and simulate human behavior after page load
    wait_for_page_load(driver)
    simulate_reading(driver, min_seconds=3, max_seconds=5)
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

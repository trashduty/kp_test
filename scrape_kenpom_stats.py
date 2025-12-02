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
    simulate_reading,
    inject_stealth_javascript
)

# Load login credentials and proxy configuration
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Proxy configuration
PROXY_USE_SELENIUM_WIRE = os.getenv('PROXY_USE_SELENIUM_WIRE', 'false').lower() == 'true'
OXY_USERNAME = os.getenv('OXY_USERNAME')
OXY_PASSWORD = os.getenv('OXY_PASSWORD')
OXY_HOST = os.getenv('OXY_HOST', 'pr.oxylabs.io')
OXY_PORT = os.getenv('OXY_PORT', '7777')
OXY_STICKY = os.getenv('OXY_STICKY', '')  # Optional sticky session ID

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
# PROXY_USE_SELENIUM_WIRE should be set to 'true' to use selenium-wire with proxy authentication
# This is needed to bypass Cloudflare and other bot detection systems
seleniumwire_options = {}

if PROXY_USE_SELENIUM_WIRE:
    if OXY_USERNAME and OXY_PASSWORD:
        # Build username with optional sticky session
        # Sticky sessions maintain the same IP for the entire scraping session
        # Format: username-session-<SESSION_ID>
        # Example: customer-user123-session-sticky1
        if OXY_STICKY:
            proxy_username = f"{OXY_USERNAME}-session-{OXY_STICKY}"
            print(f"✅ Using Oxylabs proxy with sticky session: {OXY_STICKY}")
        else:
            proxy_username = OXY_USERNAME
            print("⚠️  Using Oxylabs proxy without sticky session (IP may rotate)")
        
        proxy_url = f"http://{proxy_username}:{OXY_PASSWORD}@{OXY_HOST}:{OXY_PORT}"
        seleniumwire_options = {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
        print(f"✅ Proxy enabled: Using Oxylabs ({OXY_HOST}:{OXY_PORT})")
    else:
        print("⚠️  PROXY_USE_SELENIUM_WIRE enabled but OXY_USERNAME/OXY_PASSWORD missing")
        print("     Running without proxy - may be blocked by Cloudflare")
else:
    print("ℹ️  Selenium-wire proxy disabled (set PROXY_USE_SELENIUM_WIRE=true to enable)")
    print("     Running with direct connection")

# Initialize driver with selenium-wire
try:
    if PROXY_USE_SELENIUM_WIRE and seleniumwire_options:
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
    inject_stealth_javascript(driver)
    
except Exception as e:
    print(f"❌ Failed to initialize Chrome: {e}")
    print("Attempting fallback to regular ChromeDriver...")
    
    try:
        if PROXY_USE_SELENIUM_WIRE and seleniumwire_options:
            from seleniumwire import webdriver
            driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
        else:
            from selenium import webdriver
            driver = webdriver.Chrome(options=chrome_options)
        
        print("✅ Successfully initialized Chrome with fallback")
        
        # Inject stealth JavaScript for fallback driver too
        inject_stealth_javascript(driver)
            
    except Exception as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        sys.exit(1)

try:
    # Diagnostic: Check proxy IP and headers before logging in
    # This verifies the proxy is working correctly and helps debug Cloudflare issues
    if PROXY_USE_SELENIUM_WIRE and seleniumwire_options:
        print("\n[Diagnostic] Verifying proxy IP and headers...")
        try:
            # Check IP address
            driver.get("https://httpbin.org/ip")
            wait_for_page_load(driver)
            ip_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"   ✅ Proxy IP check: {ip_text[:100]}")
            
            # Check headers
            driver.get("https://httpbin.org/headers")
            wait_for_page_load(driver)
            headers_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"   ✅ Headers check: User-Agent present")
            
            # Small delay before proceeding
            random_delay(2, 3)
        except Exception as diag_error:
            print(f"   ⚠️  Diagnostic check failed (non-fatal): {diag_error}")
    
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
        
        # ==================== TURNSTILE SOLVER INTEGRATION POINT ====================
        # If Cloudflare Turnstile challenge appears, integrate a solver here.
        # 
        # Common Turnstile solving services:
        # - 2Captcha: https://2captcha.com/2captcha-api#turnstile
        # - Anti-Captcha: https://anti-captcha.com/apidoc/task-types/TurnstileTask
        # - CapSolver: https://www.capsolver.com/products/cloudflare-turnstile
        #
        # Integration example (pseudo-code):
        # 
        # if turnstile_detected(driver):
        #     sitekey = get_turnstile_sitekey(driver)
        #     page_url = driver.current_url
        #     
        #     # Submit to solver service (use environment variable for API key)
        #     solver_api_key = os.getenv('TURNSTILE_SOLVER_API_KEY')
        #     if solver_api_key:
        #         response = solve_turnstile(
        #             api_key=solver_api_key,
        #             sitekey=sitekey,
        #             page_url=page_url
        #         )
        #         inject_turnstile_response(driver, response)
        #         time.sleep(2)  # Wait for validation
        #     else:
        #         print("⚠️  Turnstile detected but no solver API key configured")
        #         print("     Set TURNSTILE_SOLVER_API_KEY to enable automatic solving")
        #
        # DO NOT commit API keys to the repository!
        # Always use environment variables for sensitive credentials.
        # ============================================================================
        
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

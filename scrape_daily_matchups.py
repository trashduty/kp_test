import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
from dotenv import load_dotenv
import undetected_chromedriver as uc
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
    try:
        driver.get(f"https://kenpom.com/fanmatch.php?d={tomorrow_str}")
        time.sleep(5)  # Give more time for page to fully load
    except Exception as e:
        print(f"Navigation error: {e}")
        # Try to continue anyway

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

    # Print preview of games
    print("\nTomorrow's Games Preview:")
    print(df_cleaned.head())

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

finally:
    driver.quit()

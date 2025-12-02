import os
import sys
import time
import random
import re
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
from dotenv import load_dotenv
import undetected_chromedriver as uc
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

# Configure headless Chrome with realistic settings
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless=new")  # Use new headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-setuid-sandbox")
chrome_options.add_argument("--single-process")  # Important for stability in containers
chrome_options.add_argument("--no-zygote")
chrome_options.add_argument("--disable-dev-tools")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--disable-crash-reporter")

# Use a realistic, full Chrome user agent string (Linux for GitHub Actions)
chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Add experimental options to avoid detection
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Initialize WebDriver with undetected-chromedriver and fallback
try:
    driver = uc.Chrome(
        options=chrome_options,
        version_main=None,
        use_subprocess=True,
        driver_executable_path=None
    )
except Exception as e:
    print(f"Failed to initialize Chrome with undetected_chromedriver: {e}")
    print("Attempting fallback to regular ChromeDriver...")
    try:
        from selenium import webdriver
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as fallback_error:
        print(f"❌ Fallback to regular ChromeDriver also failed: {fallback_error}")
        print("Both undetected_chromedriver and regular ChromeDriver failed to initialize.")
        raise

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
    print("[1/7] Logging into KenPom...")
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
    print("[2/7] ✅ Login successful")

    # Get tomorrow's date for the FanMatch URL
    # This will scrape the next day's games
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    
    print(f"[3/7] Navigating to FanMatch page for {tomorrow_str}...")
    
    # Add mouse movement before navigation
    random_mouse_movement(driver)
    random_delay(1, 2)
    
    driver.get(f"https://kenpom.com/fanmatch.php?d={tomorrow_str}")
    
    # Wait and simulate human behavior after page load
    random_delay(4, 6)
    scroll_page(driver)
    random_delay(2, 3)

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

    # Extract team matchups from Game column for daily matchups
    print("\n[8/9] Extracting team matchups from Game column...")
    matchups = []
    
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
            
            if len(parts) == 2:
                team1 = parts[0].strip()
                team2 = parts[1].strip()
                
                # Remove rankings (numbers or "NR") at the beginning using regex
                # Pattern: ^(NR|\d+)\s+ matches 'NR' or one or more digits at the start
                # of the string followed by one or more whitespace characters, then removes them
                team1 = re.sub(r'^(NR|\d+)\s+', '', team1).strip()
                team2 = re.sub(r'^(NR|\d+)\s+', '', team2).strip()
                
                if team1 and team2:
                    matchups.append({'Team1': team1, 'Team2': team2})
    
    # Create DataFrame with team matchups
    if matchups:
        matchups_df = pd.DataFrame(matchups)
        matchups_path = "daily_matchups.csv"
        matchups_df.to_csv(matchups_path, index=False)
        print(f"[9/9] ✅ Daily matchups saved: {matchups_path} (Matchups: {len(matchups_df)})")
        print(f"\nExtracted matchups (first 5):")
        print(matchups_df.head())
    else:
        print("[9/9] ⚠️ No matchups extracted from Game column")

    # Print preview of games
    print("\ntomorrow's Games Preview:")
    print(df_cleaned.head())

except Exception as e:
    print(f"❌ Error: {e}")
    # Take a screenshot for debugging
    try:
        screenshot_path = os.path.abspath("error_fanmatch_screenshot.png")
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved to: {screenshot_path}")
    except Exception as screenshot_error:
        print(f"⚠️ Could not save screenshot: {screenshot_error}")
    sys.exit(1)

finally:
    driver.quit()

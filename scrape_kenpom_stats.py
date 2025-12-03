import os
import sys
import time
import pandas as pd
from io import StringIO
from collections import Counter
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from captcha_solver import CaptchaSolver

# Load login credentials and API keys
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")
TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Initialize CAPTCHA solver
captcha_solver = CaptchaSolver(api_key=TWOCAPTCHA_API_KEY)

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--window-size=1920,1080")
# Add realistic user agent to avoid bot detection
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

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
    
    # Check for CAPTCHA after initial page load
    captcha_solver.detect_and_solve(driver, driver.current_url)

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
    
    # Check for CAPTCHA after login submission
    captcha_solver.detect_and_solve(driver, driver.current_url)

    # Navigate to the stats page
    print("📊 Navigating to stats page...")
    driver.get("https://kenpom.com")
    time.sleep(2)
    
    # Check for CAPTCHA before scraping data
    captcha_solver.detect_and_solve(driver, driver.current_url)

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
        # Handle multi-level column headers
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten the multi-level columns
            # KenPom structure: level 0 has category names, level 1 has actual metric names
            # Some columns appear twice (value and rank)
            
            # Get level 1 column names (the actual metric names)
            level_1_names = [col[1] if len(col) > 1 else col[0] for col in df.columns]
            
            # Count occurrences of each column name to identify pairs
            col_counts = Counter(level_1_names)
            col_occurrence = {}
            
            new_columns = []
            for col_name in level_1_names:
                if col_name not in col_occurrence:
                    col_occurrence[col_name] = 0
                else:
                    col_occurrence[col_name] += 1
                
                occurrence = col_occurrence[col_name]
                
                # If this column appears more than once, add suffix
                if col_counts[col_name] > 1:
                    if occurrence == 0:
                        new_columns.append(f"{col_name}_value")
                    else:
                        new_columns.append(f"{col_name}_rank")
                else:
                    # Single occurrence columns get no suffix
                    new_columns.append(col_name)
            
            df.columns = new_columns
        
        # Remove header rows that appear in the data
        # First row might be a duplicate header
        if df.iloc[0, 0] == 'Rk' or str(df.iloc[0, 0]).strip() == 'Rk':
            df = df.iloc[1:]
        
        # Remove any other rows where Rk column contains 'Rk'
        if 'Rk' in df.columns:
            df = df[df['Rk'] != 'Rk']
            df = df[df['Rk'].notna()]
        
        # Force W-L to be string to prevent date conversion
        if 'W-L' in df.columns:
            df['W-L'] = df['W-L'].astype(str)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Save to CSV
        output_file = "kenpom_stats.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Successfully saved {len(df)} teams to {output_file}")
        
        # Debug: Print first few column names
        print(f"📋 Column names: {list(df.columns[:10])}")
    else:
        print("❌ Could not find the stats table")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Take screenshot for debugging
    try:
        screenshot_path = "error_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Error screenshot saved to {screenshot_path}")
    except Exception as screenshot_error:
        print(f"⚠️  Could not save screenshot: {screenshot_error}")
    
    sys.exit(1)

finally:
    driver.quit()
    print("🏁 Browser closed")

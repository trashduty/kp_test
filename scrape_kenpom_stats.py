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
        # Handle multi-level column headers OR duplicate column names
        # First, check if we have multi-level columns
        if isinstance(df.columns, pd.MultiIndex):
            print("📋 Flattening multi-level column headers...")
            # Flatten the multi-level columns
            # KenPom tables have pairs of (value, rank) for each metric
            # Basic columns like Rk, Team, Conf, W-L don't have ranks
            basic_columns = ['Rk', 'Team', 'Conf', 'W-L']
            
            new_columns = []
            for col in df.columns:
                if isinstance(col, tuple):
                    # Get the metric name from the first level
                    metric = col[0]
                    # Check if second level indicates it's a rank column
                    if col[1] and str(col[1]).strip() and str(col[1]) != metric:
                        # This is a rank column
                        new_columns.append(f"{metric}_rank")
                    else:
                        # This is a value column (or a basic column)
                        if metric in basic_columns:
                            new_columns.append(metric)
                        else:
                            new_columns.append(f"{metric}_value")
                else:
                    # Single-level column, keep as-is
                    new_columns.append(col)
            
            # Apply new column names
            df.columns = new_columns
        
        # Handle duplicate column names (whether from multi-level or directly from HTML)
        # For KenPom, first occurrence is value, second is rank
        print("📋 Handling duplicate column names...")
        basic_columns = ['Rk', 'Team', 'Conf', 'W-L']
        seen = {}
        final_columns = []
        
        for col in df.columns:
            col_str = str(col)
            if col_str in seen:
                # This is a duplicate
                seen[col_str] += 1
                if seen[col_str] == 2:
                    # Second occurrence is the rank
                    base_name = col_str.replace('_value', '').replace('_rank', '')
                    final_columns.append(f"{base_name}_rank")
                else:
                    # Third+ occurrence (shouldn't happen, but handle it)
                    final_columns.append(f"{col_str}_{seen[col_str]}")
            else:
                # First occurrence
                seen[col_str] = 1
                if col_str in basic_columns or col_str.endswith('_value') or col_str.endswith('_rank'):
                    # Already properly named or is a basic column
                    final_columns.append(col_str)
                else:
                    # This is a value column that needs the suffix
                    final_columns.append(f"{col_str}_value")
        
        df.columns = final_columns
        print(f"📊 Final columns: {list(df.columns[:15])}...")  # Show first 15 columns
        
        # Remove any rows that are duplicate headers (sometimes happens with multi-level tables)
        # Check if any row has the same values as the column names
        if len(df) > 0:
            # Remove rows where the first column matches common header values
            first_col = df.columns[0]
            df = df[~df[first_col].isin(['Rk', 'Team', first_col])]
            print(f"📊 Data rows after removing duplicate headers: {len(df)}")
        
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

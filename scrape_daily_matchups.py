import os
import sys
import time
from datetime import datetime
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
# Add realistic user agent to avoid bot detection
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Initialize driver
driver = webdriver.Chrome(options=chrome_options)

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

    # Navigate to matchups page
    print("📊 Navigating to daily matchups...")
    today = datetime.now().strftime("%Y-%m-%d")
    driver.get(f"https://kenpom.com/gameplan.php?d={today}")
    time.sleep(2)
    
    # Check for CAPTCHA before scraping data
    captcha_solver.detect_and_solve(driver, driver.current_url)

    # Wait for table to load
    wait = WebDriverWait(driver, 10)
    table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gameplan")))

    # Extract matchup data
    print("📈 Extracting matchups...")
    matchups = []
    rows = driver.find_elements(By.CSS_SELECTOR, ".gameplan tr")
    
    for row in rows[1:]:  # Skip header
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 4:
            matchups.append({
                'Date': today,
                'Team1': cells[0].text.strip(),
                'Team2': cells[2].text.strip(),
                'Prediction': cells[3].text.strip()
            })
    
    # Save to CSV
    with open('daily_matchups.csv', 'w') as f:
        f.write('Date,Team1,Team2,Prediction\n')
        for m in matchups:
            f.write(f"{m['Date']},{m['Team1']},{m['Team2']},{m['Prediction']}\n")
    
    print(f"✅ Successfully saved {len(matchups)} matchups to daily_matchups.csv")

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

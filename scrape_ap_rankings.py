import os
import sys
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
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
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

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

    # Navigate to AP Rankings page
    print("📊 Navigating to AP Rankings...")
    driver.get("https://kenpom.com/aprankings.php")
    time.sleep(2)
    
    # Check for CAPTCHA before scraping data
    captcha_solver.detect_and_solve(driver, driver.current_url)

    # Get the page source
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find the rankings table
    table = soup.find('table', {'id': 'rankings-table'})
    
    if table:
        # Extract data
        teams = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 2:
                rank = cells[0].text.strip()
                team = cells[1].text.strip()
                teams.append({'Rank': rank, 'Team': team})
        
        # Save to CSV
        with open('ap_top25.csv', 'w') as f:
            f.write('Rank,Team\n')
            for team in teams[:25]:  # Top 25
                f.write(f"{team['Rank']},{team['Team']}\n")
        
        print(f"✅ Successfully saved {len(teams[:25])} teams to ap_top25.csv")
    else:
        print("❌ Could not find the rankings table")
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

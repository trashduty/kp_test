import os
import sys
import time
import csv
from datetime import datetime
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

    # Navigate to fanmatch page
    print("📊 Navigating to Fanmatch page...")
    today = datetime.now().strftime("%Y-%m-%d")
    driver.get(f"https://kenpom.com/fanmatch.php?d={today}")
    time.sleep(2)
    
    # Check for CAPTCHA before scraping data
    captcha_solver.detect_and_solve(driver, driver.current_url)

    # Get the page source
    page_source = driver.page_source
    
    # Save HTML for debugging
    html_file = f"kenpom-data/fanmatch-{today}.html"
    os.makedirs("kenpom-data", exist_ok=True)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(page_source)
    print(f"📄 Saved HTML to {html_file}")

    # Parse the HTML
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find the fanmatch table
    games = []
    table = soup.find('table', {'id': 'fanmatch-table'})
    
    if table:
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if len(cells) >= 5:
                games.append({
                    'Date': today,
                    'Team1': cells[0].text.strip(),
                    'Team2': cells[2].text.strip(),
                    'Prediction': cells[3].text.strip(),
                    'Spread': cells[4].text.strip()
                })
    
    # Save to CSV
    csv_file = f"kenpom-data/fanmatch-{today}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Team1', 'Team2', 'Prediction', 'Spread'])
        writer.writeheader()
        writer.writerows(games)
    
    print(f"✅ Successfully saved {len(games)} games to {csv_file}")

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

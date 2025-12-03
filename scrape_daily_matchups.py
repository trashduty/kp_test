#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Use undetected-chromedriver for stealth
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Optional: keep your captcha solver if you want to attempt automated solves
try:
    from captcha_solver import CaptchaSolver
    HAS_CAPTCHA_SOLVER = True
except Exception:
    HAS_CAPTCHA_SOLVER = False

# Load login credentials and API keys
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")
TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY")
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Initialize CAPTCHA solver if available
captcha_solver = None
if HAS_CAPTCHA_SOLVER and TWOCAPTCHA_API_KEY:
    captcha_solver = CaptchaSolver(api_key=TWOCAPTCHA_API_KEY)
    print("✅ 2captcha solver initialized successfully")
else:
    if HAS_CAPTCHA_SOLVER:
        print("⚠️ captcha_solver available but TWOCAPTCHA_API_KEY not set")
    else:
        print("⚠️ captcha_solver package not available; continuing without automated captcha solving")

def save_page_source(driver, path="page_source.html"):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"💾 Page source saved to {path}")
    except Exception as e:
        print(f"⚠️ Could not save page source: {e}")

def is_cloudflare_challenge(driver):
    src = driver.page_source.lower()
    checks = [
        "turnstile",
        "cf-chl-",
        "please enable javascript",
        "attention required",
        "are you human"
    ]
    return any(c in src for c in checks)

def try_solve_captcha(driver, current_url):
    if not captcha_solver:
        print("⚠️ No captcha solver configured; skipping automated solve.")
        return False
    try:
        # The solver implementation depends on your captcha_solver library.
        # We attempt a generic detect_and_solve if it exists.
        if hasattr(captcha_solver, "detect_and_solve"):
            print("🔎 Attempting to auto-solve captcha via captcha_solver.detect_and_solve...")
            return captcha_solver.detect_and_solve(driver, current_url)
        else:
            print("⚠️ captcha_solver has no detect_and_solve method; skipping.")
            return False
    except Exception as e:
        print(f"⚠️ Captcha solving attempt failed: {e}")
        return False

# Configure undetected-chromedriver options
options = uc.ChromeOptions()
if HEADLESS:
    options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
# Stealth options
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Create driver
driver = None
try:
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)  # increased timeout

    print("🔍 Navigating to KenPom login...")
    driver.get("https://kenpom.com")
    time.sleep(2)

    # If cloudflare challenge is present, try to detect and optionally attempt solve
    if is_cloudflare_challenge(driver):
        print("🔍 Detected possible Cloudflare Turnstile or bot challenge on initial page")
        solved = try_solve_captcha(driver, driver.current_url)
        if not solved:
            print("⚠️  Cannot solve turnstile: missing sitekey or solver unavailable")
            save_page_source(driver, "page_source_initial.html")
            driver.save_screenshot("error_screenshot.png")
            print("📸 Error screenshot saved to error_screenshot.png")
            sys.exit(2)

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

    # Check for captcha after login submission
    if is_cloudflare_challenge(driver):
        print("🔍 Detected possible Cloudflare Turnstile after login")
        solved = try_solve_captcha(driver, driver.current_url)
        if not solved:
            print("⚠️  Cannot solve turnstile: missing sitekey or solver unavailable")
            save_page_source(driver, "page_source_after_login.html")
            driver.save_screenshot("error_screenshot.png")
            print("📸 Error screenshot saved to error_screenshot.png")
            sys.exit(2)

    # Navigate to matchups page
    print("📊 Navigating to daily matchups...")
    today = datetime.now().strftime("%Y-%m-%d")
    driver.get(f"https://kenpom.com/gameplan.php?d={today}")
    time.sleep(2)

    # Check for Cloudflare challenge on target page
    if is_cloudflare_challenge(driver):
        print("🔍 Detected possible Cloudflare Turnstile on gameplan page")
        solved = try_solve_captcha(driver, driver.current_url)
        if not solved:
            print("⚠️  Cannot solve turnstile: missing sitekey or solver unavailable")
            save_page_source(driver, "page_source_gameplan.html")
            driver.save_screenshot("error_screenshot.png")
            print("📸 Error screenshot saved to error_screenshot.png")
            sys.exit(2)

    # Wait for table to load
    print("🕐 Waiting for the matchup table to appear...")
    try:
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gameplan")))
    except Exception as e:
        print(f"❌ Timeout waiting for matchup table: {e}")
        # Save diagnostics
        save_page_source(driver, "page_source_timeout.html")
        try:
            driver.save_screenshot("error_screenshot.png")
            print("📸 Error screenshot saved to error_screenshot.png")
        except Exception as se:
            print(f"⚠️ Could not save screenshot: {se}")
        raise

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
    with open('daily_matchups.csv', 'w', encoding="utf-8") as f:
        f.write('Date,Team1,Team2,Prediction\n')
        for m in matchups:
            # Escape commas in team names if needed
            team1 = '"' + m['Team1'].replace('"', '""') + '"'
            team2 = '"' + m['Team2'].replace('"', '""') + '"'
            prediction = '"' + m['Prediction'].replace('"', '""') + '"'
            f.write(f"{m['Date']},{team1},{team2},{prediction}\n")

    print(f"✅ Successfully saved {len(matchups)} matchups to daily_matchups.csv")

except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
    try:
        if driver:
            driver.save_screenshot("error_screenshot.png")
            print("📸 Error screenshot saved to error_screenshot.png")
            save_page_source(driver, "page_source_exception.html")
    except Exception as screenshot_error:
        print(f"⚠️  Could not save screenshot: {screenshot_error}")
    sys.exit(1)

finally:
    if driver:
        driver.quit()
    print("🏁 Browser closed")

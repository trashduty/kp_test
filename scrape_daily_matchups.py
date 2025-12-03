#!/usr/bin/env python3
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import traceback

# Use regular Selenium with system-installed Chrome and ChromeDriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Optional: 2captcha solver for automated CAPTCHA solving
try:
    from twocaptcha import TwoCaptcha
    HAS_CAPTCHA_SOLVER = True
except (ImportError, ModuleNotFoundError):
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

# Helper functions for parsing matchup data
def clean_team_name(text):
    """
    Clean team name by removing seed numbers and extra whitespace.
    Example: "9 Louisville" -> "Louisville"
    """
    # Remove seed numbers (numbers at the start)
    text = re.sub(r'^\s*\d+\s+', '', text)
    return text.strip()

def extract_teams_from_matchup(matchup_text):
    """
    Extract Team1 and Team2 from matchup cell text.
    Example: "9 Louisville at 37 Arkansas" -> ("Louisville", "Arkansas")
    """
    # Split by "at" (case insensitive)
    parts = re.split(r'\s+at\s+', matchup_text, flags=re.IGNORECASE)
    
    if len(parts) == 2:
        team1 = clean_team_name(parts[0])
        team2 = clean_team_name(parts[1])
        return team1, team2
    
    # Fallback: return cleaned text as is
    return matchup_text.strip(), ""

def parse_prediction(prediction_text, team1, team2):
    """
    Parse prediction text to extract winner, scores, win probability, and tempo.
    Format: "{Winner} {WinnerScore}-{LoserScore} ({WinProbability}%) [{Tempo}]"
    Example: "Louisville 84-81 (61%) [73]"
    
    Returns: dict with team1_score, team2_score, predicted_winner, win_probability, tempo
    """
    result = {
        'team1_score': '',
        'team2_score': '',
        'predicted_winner': '',
        'win_probability': '',
        'tempo': ''
    }
    
    if not prediction_text:
        return result
    
    # Parse format: "Winner Score1-Score2 (WinPct%) [Tempo]"
    # Example: "Louisville 84-81 (61%) [73]"
    pattern = r'([A-Za-z\s\.&\'\-]+?)\s+(\d+)-(\d+)\s+\((\d+)%\)\s+\[(\d+)\]'
    match = re.match(pattern, prediction_text)
    
    if match:
        winner_name = match.group(1).strip()
        winner_score = match.group(2)
        loser_score = match.group(3)
        win_prob = match.group(4)
        tempo = match.group(5)
        
        result['win_probability'] = win_prob
        result['tempo'] = tempo
        result['predicted_winner'] = winner_name
        
        # Determine which team is Team1 and which is Team2
        # Use more precise matching - check if names match exactly (case-insensitive)
        team1_lower = team1.lower().strip()
        team2_lower = team2.lower().strip()
        winner_lower = winner_name.lower().strip()
        
        if team1_lower == winner_lower:
            # Team1 is the winner
            result['team1_score'] = winner_score
            result['team2_score'] = loser_score
        elif team2_lower == winner_lower:
            # Team2 is the winner
            result['team1_score'] = loser_score
            result['team2_score'] = winner_score
        else:
            # Fallback: try partial matching as a last resort
            # Check if winner name is a substring of team name or vice versa
            if team1_lower in winner_lower or winner_lower in team1_lower:
                # Team1 is likely the winner
                result['team1_score'] = winner_score
                result['team2_score'] = loser_score
            elif team2_lower in winner_lower or winner_lower in team2_lower:
                # Team2 is likely the winner
                result['team1_score'] = loser_score
                result['team2_score'] = winner_score
            else:
                # Cannot determine, leave scores empty to indicate parsing issue
                result['team1_score'] = ''
                result['team2_score'] = ''
                # Keep the winner name for reference
                result['predicted_winner'] = winner_name
    
    return result

# Initialize 2captcha solver if available
solver = None
if HAS_CAPTCHA_SOLVER and TWOCAPTCHA_API_KEY:
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
    print("✅ 2captcha solver initialized successfully")
else:
    if HAS_CAPTCHA_SOLVER:
        print("⚠️ 2captcha-python available but TWOCAPTCHA_API_KEY not set")
    else:
        print("⚠️ 2captcha-python not installed; continuing without automated captcha solving")

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
    """
    Attempt to solve Cloudflare Turnstile CAPTCHA using 2captcha service.
    Returns True if solved successfully, False otherwise.
    """
    if not solver:
        print("⚠️ No captcha solver configured; skipping automated solve.")
        return False
    
    try:
        print("🔎 Attempting to detect and solve Cloudflare Turnstile CAPTCHA...")
        
        # Try to find the Turnstile sitekey in the page source
        page_source = driver.page_source
        
        # Look for Turnstile sitekey patterns
        import re
        sitekey_pattern = r'data-sitekey=["\']([^"\']+)["\']'
        match = re.search(sitekey_pattern, page_source)
        
        if not match:
            # Try alternative pattern
            sitekey_pattern = r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            match = re.search(sitekey_pattern, page_source)
        
        if not match:
            print("⚠️ Could not find Turnstile sitekey in page source")
            return False
        
        sitekey = match.group(1)
        print(f"✅ Found Turnstile sitekey: {sitekey[:20]}...")
        
        # Solve the Turnstile CAPTCHA
        print("⏳ Sending CAPTCHA to 2captcha for solving (this may take 10-30 seconds)...")
        result = solver.turnstile(
            sitekey=sitekey,
            url=current_url
        )
        
        token = result['code']
        print("✅ CAPTCHA solved successfully!")
        
        # Inject the solution token into the page
        script = f"""
        document.querySelector('[name="cf-turnstile-response"]').value = '{token}';
        """
        driver.execute_script(script)
        
        # Wait a moment for the page to process the token
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"⚠️ Captcha solving attempt failed: {e}")
        return False

# Configure Chrome options for regular Selenium
options = Options()
if HEADLESS:
    options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
# Add stealth options to avoid bot detection
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')
# Use recent Chrome user agent for better compatibility
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Create driver
driver = None
try:
    # Use system-installed Chrome and ChromeDriver (version 131 from workflow)
    # Service() automatically finds chromedriver from PATH
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
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
            try:
                # Extract matchup text (cells[0])
                matchup_text = cells[0].text.strip()
                
                # Extract teams from matchup cell
                team1, team2 = extract_teams_from_matchup(matchup_text)
                
                # Extract prediction text (cells[3])
                prediction_text = cells[3].text.strip()
                
                # Parse prediction to get scores, winner, win probability, and tempo
                parsed = parse_prediction(prediction_text, team1, team2)
                
                matchups.append({
                    'Date': today,
                    'Team1': team1,
                    'Team2': team2,
                    'Team1_Predicted_Score': parsed['team1_score'],
                    'Team2_Predicted_Score': parsed['team2_score'],
                    'Predicted_Winner': parsed['predicted_winner'],
                    'Win_Probability': parsed['win_probability'],
                    'Tempo': parsed['tempo'],
                    'Full_Prediction': prediction_text
                })
            except Exception as e:
                print(f"⚠️ Error parsing row: {e}")
                # Log the error but continue with next row
                continue

    # Save to CSV
    with open('daily_matchups.csv', 'w', encoding="utf-8") as f:
        f.write('Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n')
        for m in matchups:
            # Escape fields that may contain commas or quotes
            date = m['Date']
            team1 = '"' + m['Team1'].replace('"', '""') + '"'
            team2 = '"' + m['Team2'].replace('"', '""') + '"'
            team1_score = m['Team1_Predicted_Score']
            team2_score = m['Team2_Predicted_Score']
            # Only quote winner if it's not empty
            winner = '"' + m['Predicted_Winner'].replace('"', '""') + '"' if m['Predicted_Winner'] else ''
            win_prob = m['Win_Probability']
            tempo = m['Tempo']
            full_pred = '"' + m['Full_Prediction'].replace('"', '""') + '"'
            
            f.write(f"{date},{team1},{team2},{team1_score},{team2_score},{winner},{win_prob},{tempo},{full_pred}\n")

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

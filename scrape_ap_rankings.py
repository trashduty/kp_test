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

# Load login credentials
load_dotenv()
USERNAME = os.getenv("KENPOM_USERNAME")
PASSWORD = os.getenv("KENPOM_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Missing KENPOM_USERNAME or KENPOM_PASSWORD in environment variables.")
    sys.exit(1)

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

# Initialize driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to login page
    print("🔍 Navigating to KenPom login...")
    driver.get("https://kenpom.com")
    time.sleep(2)

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

    # Navigate to AP Rankings page
    print("📊 Navigating to AP Rankings...")
    driver.get("https://kenpom.com/aprankings.php")
    time.sleep(2)

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
    sys.exit(1)

finally:
    driver.quit()
    print("🏁 Browser closed")

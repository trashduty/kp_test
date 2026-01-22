import os
import sys
import time
import csv
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Initialize driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to login page
    print("🔍 Navigating to KenPom login...")
    driver.get("https://kenpom.com/login.php")
    time.sleep(2)

    # Find and fill the login form
    print("🔐 Logging in...")
    username_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    
    # Submit the form
    login_button = driver.find_element(By.NAME, "submit")
    login_button.click()
    time.sleep(3)
    
    # Navigate to main stats page
    print("📊 Navigating to main ratings page...")
    driver.get("https://kenpom.com/")
    time.sleep(2)

    # Get the page source
    page_source = driver.page_source
    
    # Parse the HTML
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find the ratings table
    teams_data = []
    table = soup.find('table', {'id': 'ratings-table'})
    
    if table:
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            # KenPom team rows have 21 columns
            if len(cells) == 21:
                row_data = [cell.text.strip() for cell in cells]
                # Only include rows that start with a numeric rank
                if row_data[0].isdigit():
                    teams_data.append(row_data)

    # Save to CSV
    csv_file = "kenpom_stats.csv"
    # Header constructed to match your exact version (including the duplicated SOS names)
    header = [
        'Rk', 'Team', 'Conf', 'W-L', 'NetRtg_value', 'ORtg_value', 'ORtg_rank', 
        'DRtg_value', 'DRtg_rank', 'AdjT_value', 'AdjT_rank', 'Luck_value', 'Luck_rank', 
        'NetRtg_rank', 'NetRtg_rank', 'ORtg_rank', 'ORtg_rank', 'DRtg_rank', 'DRtg_rank', 
        'NetRtg_rank', 'NetRtg_rank'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(teams_data)
    
    print(f"✅ Successfully saved {len(teams_data)} teams to {csv_file}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    driver.quit()
    print("🏁 Browser closed")

import os
import sys
import time
import csv
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

def scrape_kenpom_ratings():
    """Scrape the main ratings table from KenPom"""
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to login page
        print("🔍 Navigating to KenPom login...")
        driver.get("https://kenpom.com")
        time.sleep(2)
        
        # Find and fill the login form
        print("🔐 Logging in...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.send_keys(USERNAME)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(PASSWORD)
        
        # Submit the form
        login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
        login_button.click()
        time.sleep(3)
        
        # Verify login
        if "Log Out" not in driver.page_source:
            print("❌ Login failed. Please check credentials.")
            driver.save_screenshot("error_screenshot.png")
            sys.exit(1)
        
        print("✅ Successfully logged in!")
        
        # Navigate to main ratings page
        print("📊 Fetching ratings table...")
        driver.get("https://kenpom.com/")
        time.sleep(2)
        
        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the ratings table (id="ratings-table")
        ratings_table = soup.find('table', {'id': 'ratings-table'})
        
        if not ratings_table:
            print("❌ Could not find ratings table.")
            driver.save_screenshot("error_screenshot.png")
            sys.exit(1)
        
        # Extract data from table
        data = []
        rows = ratings_table.find('tbody').find_all('tr')
        
        print(f"📈 Processing {len(rows)} teams...")
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 21:
                continue
            
            # Extract data based on the 21-column format
            team_data = {
                'Rk': cols[0].text.strip(),
                'Team': cols[1].text.strip(),
                'Conf': cols[2].text.strip(),
                'W-L': cols[3].text.strip(),
                'NetRtg_value': cols[4].text.strip(),
                'ORtg_value': cols[5].text.strip(),
                'ORtg_rank': cols[6].text.strip(),
                'DRtg_value': cols[7].text.strip(),
                'DRtg_rank': cols[8].text.strip(),
                'AdjT_value': cols[9].text.strip(),
                'AdjT_rank': cols[10].text.strip(),
                'Luck_value': cols[11].text.strip(),
                'Luck_rank': cols[12].text.strip(),
                'NetRtg_rank': cols[13].text.strip(),
                'NetRtg_rank': cols[14].text.strip(),
                'ORtg_rank': cols[15].text.strip(),
                'ORtg_rank': cols[16].text.strip(),
                'DRtg_rank': cols[17].text.strip(),
                'DRtg_rank': cols[18].text.strip(),
                'NetRtg_rank': cols[19].text.strip(),
                'NetRtg_rank': cols[20].text.strip(),
            }
            data.append(team_data)
        
        print(f"✅ Successfully scraped {len(data)} teams.")
        return data
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        driver.save_screenshot("error_screenshot.png")
        sys.exit(1)
    finally:
        driver.quit()

def save_to_csv(data, filename="kenpom_stats.csv"):
    """Save scraped data to CSV"""
    if not data:
        return
    
    # Header as specified in requirements
    header = [
        'Rk', 'Team', 'Conf', 'W-L', 'NetRtg_value', 'ORtg_value', 'ORtg_rank',
        'DRtg_value', 'DRtg_rank', 'AdjT_value', 'AdjT_rank', 'Luck_value',
        'Luck_rank', 'NetRtg_rank', 'NetRtg_rank', 'ORtg_rank', 'ORtg_rank',
        'DRtg_rank', 'DRtg_rank', 'NetRtg_rank', 'NetRtg_rank'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"📄 Data saved successfully to {filename}")
    
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ratings_data = scrape_kenpom_ratings()
    save_to_csv(ratings_data)

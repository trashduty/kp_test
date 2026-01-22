import os
import sys
import requests
import csv
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("KENPOM_API_KEY")

if not API_KEY:
    print("❌ Missing KENPOM_API_KEY in environment variables.")
    sys.exit(1)

# Configuration
SEASON = 2026  # Current season as of Jan 2026
BASE_URL = "https://kenpom.com/api.php"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

def fetch_four_factors():
    params = {
        "endpoint": "four-factors",
        "y": SEASON
    }
    
    try:
        print(f"🚀 Fetching Four Factors data for {SEASON}...")
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            print("⚠️ No data returned from API.")
            return []
            
        print(f"✅ Successfully retrieved data for {len(data)} teams.")
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request failed: {e}")
        sys.exit(1)

def save_to_csv(data, filename="kenpom_stats.csv"):
    if not data:
        return

    # Use the field names defined in the API documentation
    # Adjusted to prioritize common identifying fields
    header = [
        'TeamName', 'Season', 'ConfOnly', 'OE', 'RankOE', 'DE', 'RankDE', 
        'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE', 'Tempo', 'RankTempo', 
        'AdjTempo', 'RankAdjTempo', 'eFG_Pct', 'RankeFG_Pct', 'TO_Pct', 
        'RankTO_Pct', 'OR_Pct', 'RankOR_Pct', 'FT_Rate', 'RankFT_Rate', 
        'DeFG_Pct', 'RankDeFG_Pct', 'DTO_Pct', 'RankDTO_Pct', 'DOR_Pct', 
        'RankDOR_Pct', 'DFT_Rate', 'RankDFT_Rate'
    ]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for team in data:
                # Filter dictionary to only include keys in our header
                row = {k: team.get(k, "") for k in header}
                writer.writerow(row)
        
        print(f"📄 Data saved successfully to {filename}")

    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    four_factors_data = fetch_four_factors()
    save_to_csv(four_factors_data)

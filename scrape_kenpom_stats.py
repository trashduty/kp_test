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
        
        # Debug: Print first team's keys to understand API structure
        if data:
            print(f"🔍 DEBUG: Sample team data keys: {list(data[0].keys())}")
            print(f"🔍 DEBUG: Sample team: {data[0].get('TeamName', 'N/A')}")
            print(f"🔍 DEBUG: Has 'RankAdjEM' field: {'RankAdjEM' in data[0]}")
            print(f"🔍 DEBUG: RankAdjEM value: {data[0].get('RankAdjEM', 'NOT_FOUND')}")
        
        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request failed: {e}")
        sys.exit(1)

def save_to_csv(data, filename="kenpom_stats.csv"):
    if not data:
        return

    # Define the mapping from API fields to the names expected by other scripts
    field_mapping = {
        'TeamName': 'Team',
        'RankAdjEM': 'Rk',           # Map the overall rank to 'Rk'
        'AdjOE': 'ORtg_value',
        'RankAdjOE': 'ORtg_rank',
        'AdjDE': 'DRtg_value',
        'RankAdjDE': 'DRtg_rank',
        'AdjTempo': 'AdjT_value',
        'RankAdjTempo': 'AdjT_rank',
        'Luck': 'Luck_value',
        'RankLuck': 'Luck_rank'
    }

    # IMPORTANT: 'Rk' MUST be in this list
    header = [
        'Team', 'Rk', 'Season', 'ConfOnly', 'ORtg_value', 'ORtg_rank', 'DRtg_value', 'DRtg_rank',
        'AdjT_value', 'AdjT_rank', 'Luck_value', 'Luck_rank',
        'OE', 'RankOE', 'DE', 'RankDE', 'Tempo', 'RankTempo',
        'eFG_Pct', 'RankeFG_Pct', 'TO_Pct', 'RankTO_Pct', 'OR_Pct', 'RankOR_Pct', 
        'FT_Rate', 'RankFT_Rate', 'DeFG_Pct', 'RankDeFG_Pct', 'DTO_Pct', 
        'RankDTO_Pct', 'DOR_Pct', 'RankDOR_Pct', 'DFT_Rate', 'RankDFT_Rate'
    ]

    # Check if RankAdjEM field exists in the data
    rank_field_missing = False
    if data and 'RankAdjEM' not in data[0]:
        rank_field_missing = True
        print("⚠️  WARNING: 'RankAdjEM' field not found in API response.")
        print("⚠️  Falling back to enumeration: assigning ranks 1, 2, 3... based on position.")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # extrasaction='ignore' is the key fix here
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            
            for idx, team in enumerate(data, start=1):
                row = {}
                
                # 1. Map renamed fields
                for api_key, target_key in field_mapping.items():
                    row[target_key] = team.get(api_key, "")
                
                # 2. Handle missing or empty Rk field
                # If RankAdjEM is missing or the mapped value is empty, use enumeration
                if rank_field_missing or not row.get('Rk'):
                    row['Rk'] = idx
                
                # 3. Fill the rest of the fields from the API data
                # Any fields in 'team' that aren't in 'header' will be ignored by DictWriter
                for key, value in team.items():
                    if key not in row:
                        row[key] = value
                
                writer.writerow(row)
        
        print(f"📄 Data saved successfully to {filename}")

    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    four_factors_data = fetch_four_factors()
    save_to_csv(four_factors_data)

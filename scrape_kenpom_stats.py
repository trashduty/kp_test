import os
import sys
import requests
import csv
import json
from dotenv import load_dotenv
from collections import defaultdict

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

ENDPOINTS_TO_FETCH = [
    'ratings',
    'four-factors',
    'pointdist', 
    'height',
    'misc-stats',
    'teams'
]

def fetch_all_data():
    all_data = defaultdict(dict)
    
    for endpoint in ENDPOINTS_TO_FETCH:
        params = {
            "endpoint": endpoint,
            "y": SEASON
        }
        
        try:
            print(f"🚀 Fetching {endpoint} data for {SEASON}...")
            response = requests.get(BASE_URL, headers=HEADERS, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                print(f"⚠️ No data returned from {endpoint} API.")
                continue
                
            print(f"✅ Successfully retrieved {len(data)} records from {endpoint}.")
            
            # Merge data by TeamName
            for record in data:
                team_name = record.get('TeamName')
                if not team_name:
                    print(f"⚠️ Record without TeamName in {endpoint}: {record}")
                    continue
                # Merge all fields into the team dict
                all_data[team_name].update(record)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed for {endpoint}: {e}")
            sys.exit(1)
    
    # Convert back to list
    merged_data = list(all_data.values())
    print(f"📊 Total unique teams after merging: {len(merged_data)}")
    
    # Debug: Show fields for first team
    if merged_data:
        print(f"🔍 DEBUG: Fields for first team ({merged_data[0].get('TeamName')}): {list(merged_data[0].keys())}")
    
    return merged_data

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
        'Team', 'Rk', 'Coach', 'Wins', 'Losses', 'Season', 'ConfOnly', 'ORtg_value', 'ORtg_rank', 'DRtg_value', 'DRtg_rank',
        'AdjT_value', 'AdjT_rank', 'Luck_value', 'Luck_rank',
        'OE', 'RankOE', 'DE', 'RankDE', 'Tempo', 'RankTempo',
        'eFG_Pct', 'RankeFG_Pct', 'TO_Pct', 'RankTO_Pct', 'OR_Pct', 'RankOR_Pct', 
        'FT_Rate', 'RankFT_Rate', 'DeFG_Pct', 'RankDeFG_Pct', 'DTO_Pct', 
        'RankDTO_Pct', 'DOR_Pct', 'RankDOR_Pct', 'DFT_Rate', 'RankDFT_Rate',
        'OffFt', 'RankOffFt', 'OffFg2', 'RankOffFg2', 'OffFg3', 'RankOffFg3',
        'DefFt', 'RankDefFt', 'DefFg2', 'RankDefFg2', 'DefFg3', 'RankDefFg3',
        'AvgHgt', 'AvgHgtRank', 'HgtEff', 'HgtEffRank', 'Hgt5', 'Hgt5Rank',
        'Hgt4', 'Hgt4Rank', 'Hgt3', 'Hgt3Rank', 'Hgt2', 'Hgt2Rank', 'Hgt1', 'Hgt1Rank',
        'Exp', 'ExpRank', 'Bench', 'BenchRank', 'Continuity', 'RankContinuity',
        'FG3Pct', 'RankFG3Pct', 'FG2Pct', 'RankFG2Pct', 'FTPct', 'RankFTPct',
        'BlockPct', 'RankBlockPct', 'StlRate', 'RankStlRate', 'NSTRate', 'RankNSTRate',
        'ARate', 'RankARate', 'F3GRate', 'RankF3GRate', 'OppFG3Pct', 'RankOppFG3Pct',
        'OppFG2Pct', 'RankOppFG2Pct', 'OppFTPct', 'RankOppFTPct', 'OppBlockPct', 'RankOppBlockPct',
        'OppStlRate', 'RankOppStlRate', 'OppNSTRate', 'RankOppNSTRate', 'OppARate', 'RankOppARate',
        'OppF3GRate', 'RankOppF3GRate', 'Arena', 'ArenaCity', 'ArenaState'
    ]

    # Check if RankAdjEM field exists in the data
    rank_field_missing = False
    if data and 'RankAdjEM' not in data[0]:
        rank_field_missing = True
        print("⚠️  WARNING: 'RankAdjEM' field not found in API response.")
        print("⚠️  Falling back to sorting by AdjEM descending to determine ranks.")
        
        # Check if AdjEM field exists
        if 'AdjEM' not in data[0]:
            print("❌ ERROR: Neither 'RankAdjEM' nor 'AdjEM' found in API response!")
            print("❌ Cannot determine team rankings. Using alphabetical order as last resort.")
        else:
            # Sort teams by AdjEM (efficiency margin) descending
            # Higher AdjEM = better team = lower rank number
            print(f"📊 Sorting {len(data)} teams by AdjEM (efficiency margin) descending...")
            
            # Convert AdjEM to float once before sorting for better performance
            # and to handle potential non-numeric values
            try:
                data = sorted(data, key=lambda x: float(x.get('AdjEM', -999)), reverse=True)
            except (ValueError, TypeError) as e:
                print(f"❌ ERROR: Failed to sort by AdjEM - invalid numeric values: {e}")
                print("❌ Using input order as last resort.")
            else:
                # Show top 5 teams for validation
                print("\n✅ Top 5 teams after sorting by AdjEM:")
                for i in range(min(5, len(data))):
                    team = data[i]
                    team_name = team.get('TeamName', 'Unknown')
                    adj_em = team.get('AdjEM', 'N/A')
                    print(f"   {i+1}. {team_name} (AdjEM: {adj_em})")
                print()
    
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
                # ASSUMPTION: The KenPom API returns teams pre-sorted by rank (best to worst)
                # This enumeration (1, 2, 3...) is only valid if the input data is sorted
                if rank_field_missing or not row.get('Rk'):
                    row['Rk'] = idx
                
                # 3. Fill the rest of the fields from the API data
                # Any fields in 'team' that aren't in 'header' will be ignored by DictWriter
                for key, value in team.items():
                    if key not in row:
                        row[key] = value
                
                writer.writerow(row)
        
        print(f"📄 Data saved successfully to {filename}")
        
        # Validation: Check that rankings make sense
        print("\n🔍 VALIDATION: Checking that rankings make sense...")
        if rank_field_missing and 'AdjEM' in data[0]:
            # Verify that AdjEM values decrease as rank increases
            print("   Checking that AdjEM decreases with rank...")
            for i in range(min(10, len(data))):
                team_name = data[i].get('TeamName', 'Unknown')
                adj_em = data[i].get('AdjEM', 'N/A')
                rank = i + 1
                print(f"   Rank {rank}: {team_name} (AdjEM: {adj_em})")
            
            # Check if top 5 AdjEM values are decreasing
            if len(data) >= 5:
                top_5_adem = [float(data[i].get('AdjEM', -999)) for i in range(5)]
                is_sorted = all(top_5_adem[i] >= top_5_adem[i+1] for i in range(4))
                if is_sorted:
                    print("   ✅ Top 5 teams have correctly decreasing AdjEM values")
                else:
                    print("   ⚠️  WARNING: Top 5 teams do NOT have decreasing AdjEM values")
        print()

    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ratings_data = fetch_all_data()
    save_to_csv(ratings_data)

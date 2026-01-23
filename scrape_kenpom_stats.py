import os
import sys
import requests
import csv
import json
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
        print()
        
        # ============================================================
        # COMPREHENSIVE DEBUG LOGGING
        # ============================================================
        
        if data:
            # 1. Print full raw API response structure (first team only)
            print("🔍 DEBUG: Raw API Response (first team):")
            print("-" * 60)
            print(json.dumps(data[0], indent=2, default=str))
            print("-" * 60)
            print()
            
            # 2. List all available field names
            all_fields = list(data[0].keys())
            print("📋 DEBUG: Available fields in API response:")
            print(f"   {all_fields}")
            print()
            
            # 3. Check specifically for rank-related fields
            print("🔍 DEBUG: Rank-related fields analysis:")
            rank_related_fields = []
            for field in all_fields:
                if 'rank' in field.lower():
                    rank_related_fields.append(field)
                    value = data[0].get(field)
                    print(f"   - {field}: {value}")
            
            if not rank_related_fields:
                print("   ⚠️  No rank-related fields found in response!")
            print()
            
            # 4. Specifically check for expected rank fields
            print("🔍 DEBUG: Checking for specific expected fields:")
            expected_fields = ['RankAdjEM', 'Rank', 'RankOverall', 'AdjEM']
            for field in expected_fields:
                if field in data[0]:
                    print(f"   ✓ {field}: {data[0][field]}")
                else:
                    print(f"   ✗ {field}: NOT FOUND")
            print()
            
            # 5. Print sample of 3-5 teams with key fields
            print("📊 DEBUG: Sample teams with all fields:")
            sample_size = min(5, len(data))
            for i in range(sample_size):
                team = data[i]
                team_name = team.get('TeamName', 'Unknown')
                rank_adj_em = team.get('RankAdjEM', 'N/A')
                adj_em = team.get('AdjEM', 'N/A')
                print(f"   {i+1}. {team_name}")
                print(f"      - RankAdjEM: {rank_adj_em}")
                print(f"      - AdjEM: {adj_em}")
                print(f"      - All fields: {list(team.keys())[:10]}...")  # First 10 fields
            print()
            
            # 6. Log summary of missing vs present fields
            print("📝 DEBUG: Field availability summary:")
            critical_fields = ['TeamName', 'RankAdjEM', 'AdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE']
            missing_fields = []
            present_fields = []
            for field in critical_fields:
                if field in data[0]:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            print(f"   ✓ Present fields ({len(present_fields)}): {present_fields}")
            if missing_fields:
                print(f"   ✗ Missing fields ({len(missing_fields)}): {missing_fields}")
            else:
                print(f"   ✓ All critical fields are present!")
            print()
            
        print("=" * 60)
        print()
        
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
    four_factors_data = fetch_four_factors()
    save_to_csv(four_factors_data)

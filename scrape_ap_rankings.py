import os
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup

def is_valid_rank(rank_str, min_rank=1, max_rank=25):
    """Validate that rank string is a digit within the expected range."""
    if not rank_str or not rank_str.isdigit():
        return False
    rank_int = int(rank_str)
    return min_rank <= rank_int <= max_rank

try:
    # Navigate to ESPN AP Rankings page (public, no login required)
    print("🔍 Fetching ESPN AP Rankings...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    response = requests.get('https://www.espn.com/mens-college-basketball/rankings', headers=headers, timeout=30)
    response.raise_for_status()
    print("✅ Page fetched successfully!")

    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the rankings table
    tbody = soup.find('tbody', {'class': 'Table__TBODY'})
    
    if tbody:
        # Extract data
        teams = []
        rows = tbody.find_all('tr', {'class': 'Table__TR'})
        
        print(f"📋 Found {len(rows)} rows in table")
        
        for row in rows:
            cells = row.find_all('td', {'class': 'Table__TD'})
            if len(cells) >= 2:
                # First cell is rank
                rank = cells[0].text.strip()
                
                # Second cell contains team name in anchor tag within span
                team_cell = cells[1]
                team_link = team_cell.find('span', {'class': 'pl3'})
                if team_link:
                    anchor = team_link.find('a')
                    if anchor:
                        team_name = anchor.text.strip()
                        if is_valid_rank(rank) and team_name:
                            teams.append({'Rank': rank, 'Team': team_name})
        
        print(f"📊 Scraped {len(teams)} teams from ESPN")
        
        if len(teams) == 0:
            print("⚠️  No teams found using primary method - trying alternate parsing...")
            # Try alternate parsing - look for all table cells
            all_cells = soup.find_all('td', {'class': 'Table__TD'})
            print(f"Found {len(all_cells)} total cells")
            
            # ESPN table has pairs: rank, team info
            i = 0
            while i < len(all_cells) - 1 and len(teams) < 25:
                rank_cell = all_cells[i]
                team_cell = all_cells[i + 1]
                
                rank = rank_cell.text.strip()
                # Get team name from anchor if available
                anchor = team_cell.find('a')
                if anchor:
                    team_name = anchor.text.strip()
                else:
                    team_name = team_cell.text.strip().split('\n')[0]
                
                # Validate rank is valid and team name exists
                if is_valid_rank(rank) and team_name:
                    teams.append({'Rank': rank, 'Team': team_name})
                
                i += 2  # Move to next pair
            
            print(f"📊 Alternate parsing found {len(teams)} teams")
        
        if len(teams) == 0:
            print("❌ Could not extract team data from page")
            sys.exit(1)
        
        # Load crosswalk CSV to convert ESPN names to KenPom format
        print("🔄 Loading team name crosswalk...")
        try:
            crosswalk = pd.read_csv('team_name_crosswalk.csv')
            if 'OddsAPI_Name' not in crosswalk.columns or 'KenPom_Name' not in crosswalk.columns:
                print("⚠️  Crosswalk CSV missing required columns (OddsAPI_Name, KenPom_Name)")
                print("   Proceeding without name mapping...")
                name_map = {}
            else:
                name_map = dict(zip(crosswalk['OddsAPI_Name'], crosswalk['KenPom_Name']))
        except FileNotFoundError:
            print("⚠️  team_name_crosswalk.csv not found. Proceeding without name mapping...")
            name_map = {}
        except Exception as e:
            print(f"⚠️  Error loading crosswalk: {e}. Proceeding without name mapping...")
            name_map = {}
        
        # Apply mapping from ESPN format to KenPom format
        print("🔄 Converting team names to KenPom format...")
        for team in teams:
            original_name = team['Team']
            # Map ESPN name (OddsAPI_Name) to KenPom format
            kenpom_name = name_map.get(original_name, original_name)
            if kenpom_name != original_name:
                print(f"  {original_name} → {kenpom_name}")
            team['Team'] = kenpom_name
        
        # Save to CSV with KenPom-formatted names
        teams_df = pd.DataFrame(teams[:25])  # Top 25
        teams_df.to_csv('ap_top25.csv', index=False)
        
        print(f"✅ Successfully saved {len(teams[:25])} teams to ap_top25.csv")
    else:
        print("❌ Could not find the rankings table with class 'Table__TBODY'")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

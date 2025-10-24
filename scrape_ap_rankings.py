import sys
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

def scrape_ap_top25():
    """Scrape AP Top 25 rankings from ESPN."""
    url = "https://www.espn.com/mens-college-basketball/rankings"
    
    try:
        print("[1/3] Fetching AP Top 25 from ESPN...")
        response = requests.get(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}, 
            timeout=10
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the AP Poll table
        teams = []
        
        # ESPN typically has tables with team rankings
        # Look for the table containing AP rankings
        tables = soup.find_all('table')
        
        if not tables:
            print("❌ Could not find ranking tables on the page")
            sys.exit(1)
        
        print(f"[DEBUG] Found {len(tables)} table(s) on the page")
        print("[2/3] Parsing AP Top 25 data...")
        
        # Parse the first table (usually AP Poll)
        table = tables[0]
        rows = table.find_all('tr')
        print(f"[DEBUG] Found {len(rows)} rows in the first table")
        
        for idx, row in enumerate(rows[1:], 1):  # Skip header
            # Look for team name in 'hide-mobile' span elements
            # ESPN's structure has team names in <span class="hide-mobile">
            hide_mobile_span = row.find('span', class_='hide-mobile')
            
            if hide_mobile_span:
                team_name = hide_mobile_span.get_text(strip=True)
                if team_name:
                    teams.append(team_name)
                    print(f"[DEBUG] Row {idx}: Found team '{team_name}'")
            
            # Stop after 25 teams
            if len(teams) >= 25:
                break
        
        if len(teams) == 0:
            print("❌ No teams found in AP rankings")
            print("[DEBUG] No team names extracted. Check if 'hide-mobile' spans exist in the HTML.")
            sys.exit(1)
        
        # Validate that we got exactly 25 teams
        if len(teams) < 25:
            print(f"❌ Error: Expected 25 teams but only found {len(teams)}. AP Top 25 must have exactly 25 teams.")
            sys.exit(1)
        elif len(teams) > 25:
            print(f"[DEBUG] Found {len(teams)} teams, truncating to top 25")
            teams = teams[:25]
        
        # Create DataFrame
        df = pd.DataFrame({'Team': teams})
        
        # Save to CSV
        output_path = os.path.abspath("ap_top25.csv")
        df.to_csv(output_path, index=False)
        
        print(f"[3/3] ✅ AP Top 25 saved to {output_path} ({len(teams)} teams)")
        
        return df
        
    except requests.RequestException as e:
        print(f"❌ Error fetching AP rankings: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing AP rankings: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    scrape_ap_top25()

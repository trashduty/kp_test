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
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the AP Poll table
        teams = []
        
        # ESPN typically has tables with team rankings
        # Look for the table containing AP rankings
        tables = soup.find_all('table')
        
        if not tables:
            print("⚠️ Could not find ranking tables on the page, trying alternative parsing...")
            # Try to find divs or other elements containing rankings
            ranking_divs = soup.find_all('div', class_='rankings')
            if not ranking_divs:
                print("❌ Could not find ranking data on the page")
                sys.exit(1)
        
        print("[2/3] Parsing AP Top 25 data...")
        
        # Parse the first table (usually AP Poll)
        if tables:
            table = tables[0]
            rows = table.find_all('tr')
            
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # Extract team name - usually in second column
                    team_cell = cols[1] if len(cols) > 1 else cols[0]
                    team_link = team_cell.find('a')
                    
                    if team_link:
                        team_name = team_link.get_text(strip=True)
                        teams.append(team_name)
                    else:
                        # Fallback to text content
                        team_name = team_cell.get_text(strip=True)
                        if team_name and team_name not in ['Rank', 'Team', 'RK', 'TEAM', 'Record', 'Points']:
                            teams.append(team_name)
                
                # Stop after 25 teams
                if len(teams) >= 25:
                    break
        
        if len(teams) == 0:
            print("❌ No teams found in AP rankings")
            sys.exit(1)
        
        # Take only top 25 if we got more
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

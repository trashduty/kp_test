import os
import sys
import json
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("ODDS_API_KEY")

if not API_KEY:
    print("❌ Missing ODDS_API_KEY in environment variables.")
    sys.exit(1)

# The Odds API configuration
SPORT = "basketball_ncaab"
REGIONS = "us"
MARKETS = "outrights"  # Championship futures
ODDS_FORMAT = "american"

def fetch_championship_odds():
    """Fetch NCAA Basketball championship odds from The Odds API."""
    
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    
    params = {
        'api_key': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT
    }
    
    try:
        print(f"[1/3] Fetching championship odds from The Odds API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check remaining requests
        remaining_requests = response.headers.get('x-requests-remaining')
        used_requests = response.headers.get('x-requests-used')
        print(f"[INFO] API requests remaining: {remaining_requests}, used: {used_requests}")
        
        if not data:
            print("❌ No odds data received from API")
            sys.exit(1)
        
        print(f"[2/3] Processing championship odds data...")
        
        # Process the data to extract championship odds
        odds_list = []
        
        for event in data:
            # Look for championship/outright markets
            if 'bookmakers' in event:
                for bookmaker in event['bookmakers']:
                    if 'markets' in bookmaker:
                        for market in bookmaker['markets']:
                            if market['key'] == 'outrights':
                                for outcome in market['outcomes']:
                                    team_name = outcome['name']
                                    odds = outcome['price']  # American odds format
                                    
                                    # Convert American odds to implied probability
                                    if odds > 0:
                                        implied_prob = 100 / (odds + 100) * 100
                                    else:
                                        implied_prob = abs(odds) / (abs(odds) + 100) * 100
                                    
                                    odds_list.append({
                                        'Team': team_name,
                                        'Bookmaker': bookmaker['title'],
                                        'Odds': odds,
                                        'ImpliedProbability': round(implied_prob, 2)
                                    })
        
        if not odds_list:
            print("❌ No championship odds found in the data")
            sys.exit(1)
        
        # Create DataFrame and aggregate by team (take average across bookmakers)
        df = pd.DataFrame(odds_list)
        
        # Group by team and calculate average implied probability
        df_agg = df.groupby('Team').agg({
            'ImpliedProbability': 'mean',
            'Odds': 'first'  # Just take first bookmaker's odds for display
        }).reset_index()
        
        df_agg['ImpliedProbability'] = df_agg['ImpliedProbability'].round(2)
        df_agg = df_agg.sort_values('ImpliedProbability', ascending=False)
        
        # Save to CSV
        output_path = os.path.abspath("championship_odds.csv")
        df_agg.to_csv(output_path, index=False)
        
        print(f"[3/3] ✅ Championship odds saved to {output_path} ({len(df_agg)} teams)")
        print(f"\nTop 10 championship favorites:")
        print(df_agg.head(10).to_string(index=False))
        
        # Also save detailed data with all bookmakers
        detailed_path = os.path.abspath("championship_odds_detailed.csv")
        pd.DataFrame(odds_list).to_csv(detailed_path, index=False)
        print(f"\n[INFO] Detailed odds (all bookmakers) saved to {detailed_path}")
        
        return df_agg
        
    except requests.RequestException as e:
        print(f"❌ Error fetching odds data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error processing odds data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fetch_championship_odds()

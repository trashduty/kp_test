#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()
KENPOM_API_KEY = os.getenv("KENPOM_API_KEY")

if not KENPOM_API_KEY:
    print("❌ Missing KENPOM_API_KEY in environment variables.")
    print("💡 Add your KenPom API key to GitHub Secrets as KENPOM_API_KEY")
    sys.exit(1)

def fetch_fanmatch_data(date_str):
    """
    Fetch game predictions from KenPom Fanmatch API.
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        List of game dictionaries from API response
    """
    url = "https://kenpom.com/api.php"
    params = {
        "endpoint": "fanmatch",
        "d": date_str
    }
    headers = {
        "Authorization": f"Bearer {KENPOM_API_KEY}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    print(f"📊 Fetching matchup data for {date_str} from KenPom API...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Successfully retrieved {len(data)} matchups from API")
        return data
        
    except requests.exceptions.HTTPError as e:
        # response is guaranteed to exist here because HTTPError is raised by raise_for_status()
        if response.status_code == 401:
            print("❌ Authentication failed. Please check your KENPOM_API_KEY")
        elif response.status_code == 403:
            print("❌ Access forbidden. Your API key may not have access to the Fanmatch endpoint")
        else:
            print(f"❌ HTTP Error: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from API: {e}")
        sys.exit(1)
    
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON response: {e}")
        print(f"Response text: {response.text}")
        sys.exit(1)

def convert_to_csv(games, date_str):
    """
    Convert API response to CSV format matching the original scraper output.
    
    API provides:
    - Visitor/Home team names
    - VisitorPred/HomePred scores
    - HomeWP (win probability for home team)
    - PredTempo
    
    We convert to:
    - Team1 (Visitor), Team2 (Home)
    - Team1_Predicted_Score, Team2_Predicted_Score
    - Predicted_Winner, Win_Probability
    - Tempo
    """
    matchups = []
    
    for game in games:
        visitor = game.get('Visitor', '')
        home = game.get('Home', '')
        visitor_pred = game.get('VisitorPred', '')
        home_pred = game.get('HomePred', '')
        home_wp = game.get('HomeWP', '')
        tempo = game.get('PredTempo', '')
        
        # Convert HomeWP (0-1) to percentage
        home_wp_pct = ''
        if home_wp != '':
            try:
                home_wp_float = float(home_wp)
                home_wp_pct = round(home_wp_float * 100)
            except (ValueError, TypeError):
                # If conversion fails, leave as empty
                home_wp = ''
                home_wp_pct = ''
        
        # Determine winner based on HomeWP
        if home_wp != '' and home_wp_pct != '':
            if home_wp_pct > 50:
                predicted_winner = home
                win_probability = home_wp_pct
            else:
                predicted_winner = visitor
                win_probability = 100 - home_wp_pct
        else:
            predicted_winner = ''
            win_probability = ''
        
        # Format full prediction string (matching original format)
        if visitor_pred and home_pred and win_probability:
            if predicted_winner == home:
                full_prediction = f"{home} {home_pred}-{visitor_pred} ({win_probability}%) [{tempo}]"
            else:
                full_prediction = f"{visitor} {visitor_pred}-{home_pred} ({win_probability}%) [{tempo}]"
        else:
            full_prediction = ''
        
        matchups.append({
            'Date': date_str,
            'Team1': visitor,  # Away team
            'Team2': home,     # Home team
            'Team1_Predicted_Score': visitor_pred,
            'Team2_Predicted_Score': home_pred,
            'Predicted_Winner': predicted_winner,
            'Win_Probability': win_probability,
            'Tempo': tempo,
            'Full_Prediction': full_prediction
        })
    
    return matchups

def save_to_csv(matchups, filename='daily_matchups.csv'):
    """Save matchups to CSV file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('Date,Team1,Team2,Team1_Predicted_Score,Team2_Predicted_Score,Predicted_Winner,Win_Probability,Tempo,Full_Prediction\n')
        
        for m in matchups:
            date = m['Date']
            team1 = '"' + str(m['Team1']).replace('"', '""') + '"'
            team2 = '"' + str(m['Team2']).replace('"', '""') + '"'
            team1_score = m['Team1_Predicted_Score']
            team2_score = m['Team2_Predicted_Score']
            winner = '"' + str(m['Predicted_Winner']).replace('"', '""') + '"' if m['Predicted_Winner'] else ''
            win_prob = m['Win_Probability']
            tempo = m['Tempo']
            full_pred = '"' + str(m['Full_Prediction']).replace('"', '""') + '"'
            
            f.write(f"{date},{team1},{team2},{team1_score},{team2_score},{winner},{win_prob},{tempo},{full_pred}\n")
    
    print(f"✅ Successfully saved {len(matchups)} matchups to {filename}")

def main():
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🏀 KenPom Daily Matchups Fetcher")
    print(f"📅 Date: {today}")
    print("-" * 50)
    
    # Fetch data from API
    games = fetch_fanmatch_data(today)
    
    # Convert to CSV format
    matchups = convert_to_csv(games, today)
    
    # Save to CSV
    save_to_csv(matchups)
    
    print("-" * 50)
    print("✅ Done!")

if __name__ == "__main__":
    main()

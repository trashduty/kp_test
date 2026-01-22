import os
import csv
import pandas as pd
import requests
from datetime import datetime
import re
from pathlib import Path

# Team name mapping/cleaning function
def clean_team_name(team_name):
    """Normalize team names for matching between different sources"""
    # Remove common suffixes
    team_name = re.sub(r'\s+(Antelopes|Lopes|State|St\.|College)$', '', team_name, flags=re.IGNORECASE)
    
    # Common mappings
    mappings = {
        'Michigan St.': 'Michigan State',
        'Michigan State': 'Michigan State',
        'Florida St.': 'Florida State',
        'Florida State': 'Florida State',
        'Grand Canyon': 'Grand Canyon',
        'Grand Canyon Antelopes': 'Grand Canyon',
        'UConn': 'Connecticut',
        'UNC': 'North Carolina',
        'UNLV': 'UNLV',
        'UCLA': 'UCLA',
        'USC': 'USC',
        'LSU': 'LSU',
        'SMU': 'SMU',
        'TCU': 'TCU',
        'BYU': 'BYU',
        'UCF': 'UCF',
        'VCU': 'VCU',
    }
    
    # Check if there's a direct mapping
    if team_name in mappings:
        return mappings[team_name]
    
    return team_name.strip()

def find_team_in_kenpom(team_name, kenpom_df):
    """Find a team in KenPom data with fuzzy matching"""
    cleaned_name = clean_team_name(team_name)
    
    # Try exact match first
    match = kenpom_df[kenpom_df['Team'].str.contains(cleaned_name, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]
    
    # Try partial match
    for idx, row in kenpom_df.iterrows():
        kenpom_cleaned = clean_team_name(row['Team'])
        if cleaned_name.lower() in kenpom_cleaned.lower() or kenpom_cleaned.lower() in cleaned_name.lower():
            return row
    
    return None

def generate_slug(home_team, away_team):
    """Generate SEO-friendly slug for filename"""
    slug = f"{away_team}-vs-{home_team}".lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def generate_preview_markdown(game, home_stats, away_stats, date_str):
    """Generate Jekyll-compatible markdown preview"""
    home_team = game['Home Team']
    away_team = game['Away Team']
    
    # Extract stats
    home_rank = home_stats['Rk'] if home_stats is not None else 'Unranked'
    away_rank = away_stats['Rk'] if away_stats is not None else 'Unranked'
    
    home_ortg = home_stats['ORtg_value'] if home_stats is not None else 'N/A'
    away_ortg = away_stats['ORtg_value'] if away_stats is not None else 'N/A'
    
    home_drtg = home_stats['DRtg_value'] if home_stats is not None else 'N/A'
    away_drtg = away_stats['DRtg_value'] if away_stats is not None else 'N/A'
    
    home_tempo = home_stats['AdjT_value'] if home_stats is not None else 'N/A'
    away_tempo = away_stats['AdjT_value'] if away_stats is not None else 'N/A'
    
    predicted_winner = game.get('Predicted Winner', 'TBD')
    predicted_spread = game.get('Model Spread', 'N/A')
    confidence = game.get('Win Probability', 'N/A')
    
    # Generate title
    title = f"{away_team} vs {home_team} Preview & Prediction"
    
    # Generate excerpt
    excerpt = f"Expert analysis and prediction for {away_team} vs {home_team}. Get the latest stats, trends, and betting insights."
    
    # Front matter
    front_matter = f"""---
title: "{title}"
date: {date_str}
categories: [NCAA Basketball, Game Previews]
tags: ["{away_team}", "{home_team}", KenPom, Predictions]
excerpt: "{excerpt}"
---
"""
    
    # Content
    content = f"""
## {away_team} (#{away_rank}) vs {home_team} (#{home_rank})

### Game Overview

The {away_team} will face off against the {home_team} in what promises to be an exciting matchup. Both teams bring unique strengths to the court, and our analysis breaks down the key factors that could determine the outcome.

### Team Statistics

#### {away_team}
- **KenPom Rank:** #{away_rank}
- **Offensive Rating:** {away_ortg}
- **Defensive Rating:** {away_drtg}
- **Adjusted Tempo:** {away_tempo}

#### {home_team}
- **KenPom Rank:** #{home_rank}
- **Offensive Rating:** {home_ortg}
- **Defensive Rating:** {home_drtg}
- **Adjusted Tempo:** {home_tempo}

### Prediction

Our model predicts **{predicted_winner}** will win this matchup.

- **Predicted Spread:** {predicted_spread}
- **Win Probability:** {confidence}%

### Key Matchup Factors

The efficiency ratings suggest {"an offensive battle" if float(str(home_ortg).replace('N/A', '0')) > 110 or float(str(away_ortg).replace('N/A', '0')) > 110 else "a defensive struggle"}. The tempo differential will be crucial in determining which team can impose their style of play.

---

*This preview is generated using advanced statistical models and KenPom efficiency ratings. Check back for updated analysis as game time approaches.*
"""
    
    return front_matter + content

def main():
    """Main function to generate previews"""
    print("🏀 Basketball Preview Generator")
    print("=" * 50)
    
    # Load KenPom stats
    print("📊 Loading KenPom stats...")
    try:
        kenpom_df = pd.read_csv('kenpom_stats.csv')
        print(f"✅ Loaded {len(kenpom_df)} teams from KenPom")
    except Exception as e:
        print(f"❌ Error loading kenpom_stats.csv: {e}")
        return
    
    # Fetch games from GitHub
    print("🌐 Fetching game predictions from GitHub...")
    try:
        url = "https://raw.githubusercontent.com/trashduty/cbb/main/docs/CBB_Output.csv"
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to temporary file and read
        with open('/tmp/cbb_output.csv', 'w') as f:
            f.write(response.text)
        
        games_df = pd.read_csv('/tmp/cbb_output.csv')
        print(f"✅ Loaded {len(games_df)} games from predictions file")
    except Exception as e:
        print(f"❌ Error fetching game predictions: {e}")
        return
    
    # Create _posts directory if it doesn't exist
    posts_dir = Path('_posts')
    posts_dir.mkdir(exist_ok=True)
    print(f"📁 Created/verified _posts directory")
    
    # Filter games where at least one team has KenPom rank ≤ 40
    print("🔍 Filtering games with top-40 teams...")
    filtered_games = []
    
    for idx, game in games_df.iterrows():
        home_team = game.get('Home Team', '')
        away_team = game.get('Away Team', '')
        
        if not home_team or not away_team:
            continue
        
        # Find teams in KenPom data
        home_stats = find_team_in_kenpom(home_team, kenpom_df)
        away_stats = find_team_in_kenpom(away_team, kenpom_df)
        
        # Check if either team is ranked 40 or better
        home_rank = int(home_stats['Rk']) if home_stats is not None and pd.notna(home_stats['Rk']) else 999
        away_rank = int(away_stats['Rk']) if away_stats is not None and pd.notna(away_stats['Rk']) else 999
        
        if home_rank <= 40 or away_rank <= 40:
            filtered_games.append((game, home_stats, away_stats))
    
    print(f"✅ Found {len(filtered_games)} games featuring top-40 teams")
    
    # Generate preview files
    print("📝 Generating preview files...")
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    for game, home_stats, away_stats in filtered_games:
        home_team = game['Home Team']
        away_team = game['Away Team']
        
        # Generate slug and filename
        slug = generate_slug(home_team, away_team)
        filename = f"{date_str}-{slug}.md"
        filepath = posts_dir / filename
        
        # Generate markdown content
        markdown = generate_preview_markdown(game, home_stats, away_stats, date_str)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"  ✅ Created: {filename}")
    
    print(f"\n🎉 Successfully generated {len(filtered_games)} preview files!")
    print(f"📁 Files saved to: {posts_dir.absolute()}")

if __name__ == "__main__":
    main()

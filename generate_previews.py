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
    # Common mappings - handle these first
    mappings = {
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
        'Penn State Nittany Lions': 'Penn St.',
        'Penn State': 'Penn St.',
        'Michigan State': 'Michigan St.',
        'Florida State': 'Florida St.',
        'Mississippi State': 'Mississippi St.',
        'Iowa State': 'Iowa St.',
        'Kansas State': 'Kansas St.',
        'Oklahoma State': 'Oklahoma St.',
        'Oregon State': 'Oregon St.',
        'Arizona State': 'Arizona St.',
        'Arkansas State': 'Arkansas St.',
        'Arkansas St Red Wolves': 'Arkansas St.',
        'Missouri State': 'Missouri St.',
        'Missouri St Bears': 'Missouri St.',
        'Tennessee State': 'Tennessee St.',
        'Tennessee St Tigers': 'Tennessee St.',
    }
    
    # Check if there's a direct mapping
    if team_name in mappings:
        return mappings[team_name]
    
    # Remove common mascot names
    team_name = re.sub(r'\s+(Antelopes|Lopes|Nittany Lions|Badgers|Eagles|Red Wolves|Bears|Tigers|Aggies|Panthers|Colonels|Blazers|Bulls|Dukes|Jaguars|Redhawks|Trojans|Golden Eagles|Screaming Eagles|Cougars|Miners|Golden Panthers|Governors|Hatters|Pride|Mountaineers|Ragin\' Cajuns|49ers|Fighting Camels|Chanticleers|Bobcats|Pioneers|Bison|Vikings|Phoenix|Stags|Purple Eagles|Hawks|Rainbow Warriors|Roadrunners|Vandals|Hornets|Gaels|Warriors|Dolphins|Knights)$', '', team_name, flags=re.IGNORECASE)
    
    return team_name.strip()

def find_team_in_kenpom(team_name, kenpom_df):
    """Find a team in KenPom data with fuzzy matching"""
    cleaned_name = clean_team_name(team_name)
    
    # Try exact match first
    exact_match = kenpom_df[kenpom_df['Team'] == cleaned_name]
    if not exact_match.empty:
        return exact_match.iloc[0]
    
    # Try case-insensitive exact match
    exact_match_ci = kenpom_df[kenpom_df['Team'].str.lower() == cleaned_name.lower()]
    if not exact_match_ci.empty:
        return exact_match_ci.iloc[0]
    
    # Special handling for hyphenated names like "Arkansas-Little Rock"
    # These should NOT match "Arkansas" alone
    if '-' in team_name and ' ' in team_name:
        # For hyphenated multi-word names, require very close match
        for idx, row in kenpom_df.iterrows():
            kenpom_name = row['Team']
            if team_name.lower().replace('-', ' ') == kenpom_name.lower().replace('-', ' '):
                return row
        return None  # Don't do fuzzy matching for hyphenated names
    
    # Try partial match - but be more careful
    # Only match if one is contained in the other AND they share significant overlap
    cleaned_lower = cleaned_name.lower()
    for idx, row in kenpom_df.iterrows():
        kenpom_name = row['Team']
        kenpom_cleaned = clean_team_name(kenpom_name)
        kenpom_lower = kenpom_cleaned.lower()
        
        # Check for substring match with minimum length requirement
        if len(cleaned_lower) >= 8 and len(kenpom_lower) >= 8:
            if cleaned_lower in kenpom_lower or kenpom_lower in cleaned_lower:
                # Make sure it's not a false positive (e.g., "Duke" in "James Madison Dukes")
                # Check that the match starts at word boundary or is at the beginning
                if cleaned_lower == kenpom_lower or \
                   cleaned_lower.startswith(kenpom_lower) or \
                   kenpom_lower.startswith(cleaned_lower):
                    return row
    
    return None

def generate_slug(home_team, away_team):
    """Generate SEO-friendly slug for filename"""
    slug = f"{away_team}-vs-{home_team}".lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def generate_preview_markdown(game_name, home_team, away_team, home_stats, away_stats, game_rows, date_str):
    """Generate Jekyll-compatible markdown preview"""
    
    # Extract stats
    home_rank = home_stats['Rk'] if home_stats is not None else 'Unranked'
    away_rank = away_stats['Rk'] if away_stats is not None else 'Unranked'
    
    home_ortg = home_stats['ORtg_value'] if home_stats is not None else 'N/A'
    away_ortg = away_stats['ORtg_value'] if away_stats is not None else 'N/A'
    
    home_drtg = home_stats['DRtg_value'] if home_stats is not None else 'N/A'
    away_drtg = away_stats['DRtg_value'] if away_stats is not None else 'N/A'
    
    home_tempo = home_stats['AdjT_value'] if home_stats is not None else 'N/A'
    away_tempo = away_stats['AdjT_value'] if away_stats is not None else 'N/A'
    
    # Get prediction data from game rows
    predicted_spread = 'N/A'
    win_probability = 'N/A'
    game_time = 'TBD'
    
    if not game_rows.empty:
        # Try to get home team row
        home_row = game_rows[game_rows['Team'].str.contains(home_team, case=False, na=False)]
        away_row = game_rows[game_rows['Team'].str.contains(away_team, case=False, na=False)]
        
        if not home_row.empty:
            predicted_spread = home_row.iloc[0].get('model_spread', 'N/A')
            win_probability = home_row.iloc[0].get('Moneyline Win Probability', 'N/A')
            game_time = home_row.iloc[0].get('Game Time', 'TBD')
            
            # Convert probability to percentage
            if win_probability != 'N/A':
                try:
                    win_probability = f"{float(win_probability) * 100:.1f}"
                except:
                    win_probability = 'N/A'
    
    # Determine predicted winner based on spread
    predicted_winner = home_team
    if predicted_spread != 'N/A':
        try:
            if float(predicted_spread) < 0:
                predicted_winner = home_team
            else:
                predicted_winner = away_team
        except:
            pass
    
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

**Game Time:** {game_time}

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
- **Win Probability:** {win_probability}%

### Key Matchup Factors

The efficiency ratings suggest {"an offensive battle" if str(home_ortg) != 'N/A' and float(str(home_ortg)) > 110 or str(away_ortg) != 'N/A' and float(str(away_ortg)) > 110 else "a defensive struggle"}. The tempo differential will be crucial in determining which team can impose their style of play.

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
    processed_games = set()
    
    for idx, row in games_df.iterrows():
        game_name = row.get('Game', '')
        team_name = row.get('Team', '')
        
        if not game_name or game_name in processed_games:
            continue
        
        # Parse game name to get both teams (format: "Away Team vs. Home Team")
        if ' vs. ' in game_name:
            parts = game_name.split(' vs. ')
            away_team = parts[0].strip()
            home_team = parts[1].strip()
        else:
            continue
        
        # Mark this game as processed
        processed_games.add(game_name)
        
        # Find teams in KenPom data
        home_stats = find_team_in_kenpom(home_team, kenpom_df)
        away_stats = find_team_in_kenpom(away_team, kenpom_df)
        
        # Check if either team is ranked 40 or better
        home_rank = int(home_stats['Rk']) if home_stats is not None and pd.notna(home_stats['Rk']) else 999
        away_rank = int(away_stats['Rk']) if away_stats is not None and pd.notna(away_stats['Rk']) else 999
        
        if home_rank <= 40 or away_rank <= 40:
            # Get both rows for this game (one for each team)
            game_rows = games_df[games_df['Game'] == game_name]
            filtered_games.append((game_name, home_team, away_team, home_stats, away_stats, game_rows))
    
    print(f"✅ Found {len(filtered_games)} games featuring top-40 teams")
    
    # Generate preview files
    print("📝 Generating preview files...")
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    for game_name, home_team, away_team, home_stats, away_stats, game_rows in filtered_games:
        # Generate slug and filename
        slug = generate_slug(home_team, away_team)
        filename = f"{date_str}-{slug}.md"
        filepath = posts_dir / filename
        
        # Generate markdown content
        markdown = generate_preview_markdown(game_name, home_team, away_team, home_stats, away_stats, game_rows, date_str)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"  ✅ Created: {filename}")
    
    print(f"\n🎉 Successfully generated {len(filtered_games)} preview files!")
    print(f"📁 Files saved to: {posts_dir.absolute()}")

if __name__ == "__main__":
    main()

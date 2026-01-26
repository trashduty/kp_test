import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import re

# Constants for narrative generation
UNRANKED_DEFAULT = 999
ELITE_RANK_THRESHOLD = 50
POOR_DEFENSE_RANK = 200
HIGH_COMBINED_OFFENSE = 240
LOW_COMBINED_DEFENSE = 195
HIGH_TEMPO = 70
LOW_TEMPO = 68

def download_csv(url):
    """Download CSV file from URL and return as pandas DataFrame."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        from io import StringIO
        return pd.read_csv(StringIO(response.text))
    except requests.RequestException as e:
        raise Exception(f"Failed to download {url}: {e}")

def normalize_team_name(team_name):
    """Normalize team name for consistent matching."""
    team_name = re.sub(r'\s+(Rainbow Warriors|Matadors|Bulls|Owls|Jaguars|Mastodons|Lakers|Cougars|Huskies|Ducks|Purple Aces|Salukis|Badgers|Trojans)$', '', team_name)
    replacements = {
        "Hawai'i": "Hawaii",
        "CSU Northridge": "CS Northridge",
        "IUPUI": "IU Indy",
        "Fort Wayne": "Purdue Fort Wayne",
    }
    for old, new in replacements.items():
        if old in team_name:
            team_name = team_name.replace(old, new)
    team_name = team_name.replace(" St ", " St. ")
    if team_name.endswith(" St"):
        team_name = team_name + "."
    return team_name.strip()

def find_team_in_kenpom(team_name, kenpom_df):
    """Find team in KenPom stats using flexible matching."""
    # Try exact match first
    exact_match = kenpom_df[kenpom_df['Team'] == team_name]
    if not exact_match.empty:
        return exact_match.iloc[0]
    
    # Try normalized match
    normalized = normalize_team_name(team_name)
    exact_match_normalized = kenpom_df[kenpom_df['Team'] == normalized]
    if not exact_match_normalized.empty:
        return exact_match_normalized.iloc[0]
    
    # Try matching normalized names
    for _, row in kenpom_df.iterrows():
        if normalize_team_name(row['Team']) == normalized:
            return row
    
    # Only do partial match if no exact or normalized match found
    # And prefer longer matches (more specific)
    best_match = None
    best_match_length = 0
    
    normalized_lower = normalized.lower()
    for _, row in kenpom_df.iterrows():
        row_team_lower = row['Team'].lower()
        
        # Check if either string contains the other
        if normalized_lower in row_team_lower or row_team_lower in normalized_lower:
            # Prefer the match with the longest common substring
            match_length = min(len(normalized_lower), len(row_team_lower))
            if match_length > best_match_length:
                best_match = row
                best_match_length = match_length
    
    return best_match

def find_team_logo(team_name, logos_df, crosswalk_df):
    """
    Find team logo URL using the specific chain:
    CBB_Output Name -> Crosswalk[API] -> Crosswalk[kenpom] -> Logos[ncaa_name]
    """
    if crosswalk_df is None or crosswalk_df.empty:
        print(f"  Warning: Crosswalk data is missing for '{team_name}'")
        return "https://via.placeholder.com/150"

    # Step 1 & 2: Match team_name in API column and get kenpom name
    kenpom_name = None
    # Search for team_name in the 'API' column of crosswalk
    team_lower = team_name.strip().lower()
    for _, row in crosswalk_df.iterrows():
        if str(row['API']).strip().lower() == team_lower:
            kenpom_name = str(row['kenpom']).strip()
            break

    if not kenpom_name:
        print(f"  Warning: '{team_name}' not found in crosswalk API column")
        return "https://via.placeholder.com/150"

    # Step 3: Use kenpom_name to find logo in logos_df['ncaa_name']
    if 'ncaa_name' in logos_df.columns:
        kp_lower = kenpom_name.lower()
        for _, row in logos_df.iterrows():
            if str(row['ncaa_name']).strip().lower() == kp_lower:
                return row['logos']

    print(f"  Warning: No logo found for KenPom name '{kenpom_name}' in logos.csv ncaa_name column")
    return "https://via.placeholder.com/150"

def parse_game_time(game_time_str):
    try:
        time_str = game_time_str.replace(' ET', '')
        current_year = datetime.now().year
        return datetime.strptime(f"{current_year} {time_str}", "%Y %b %d %I:%M%p")
    except:
        return None

def format_stat(value, decimals=1):
    try:
        if pd.isna(value): return "N/A"
        return f"{float(value):.{decimals}f}" if decimals > 0 else str(int(value))
    except: return "N/A"

def format_percentage(value):
    try:
        if pd.isna(value): return "N/A"
        return f"{float(value)*100:.1f}%" if float(value) < 1 and float(value) > -1 else f"{float(value):.1f}%"
    except: return "N/A"

def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def generate_post_content(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions, away_logo, home_logo, game_date):
    def team_section(team_name, stats):
        return f"""
## {team_name}
{team_name} comes in ranked #{format_stat(stats.get('Rk', 'N/A'), 0)} overall by KenPom.

### Record & Metrics
- **Record:** {format_stat(stats.get('Wins', 'N/A'), 0)}-{format_stat(stats.get('Losses', 'N/A'), 0)}
- **KenPom Rank:** #{format_stat(stats.get('Rk', 'N/A'), 0)}
- **Offensive Efficiency:** {format_stat(stats.get('OE', 'N/A'))} (Rank: #{format_stat(stats.get('RankOE', 'N/A'), 0)})
- **Defensive Efficiency:** {format_stat(stats.get('DE', 'N/A'))} (Rank: #{format_stat(stats.get('RankDE', 'N/A'), 0)})
"""

    post = f"""---
layout: post
title: "{away_team} vs {home_team} - Game Preview"
date: {game_date.strftime('%Y-%m-%d')}
categories: [basketball, preview]
---

# {away_team} vs {home_team}
## Game Preview for {game_date.strftime('%B %d, %Y')}

<table style="width: 100%; border-collapse: collapse; margin: 20px auto;">
  <tr>
    <td style="width: 45%; text-align: center;">
      <img src="{away_logo}" alt="{away_team} logo">
      <p><strong>{away_team}</strong></p>
    </td>
    <td style="width: 10%; font-size: 2em; font-weight: bold;">VS</td>
    <td style="width: 45%; text-align: center;">
      <img src="{home_logo}" alt="{home_team} logo">
      <p><strong>{home_team}</strong></p>
    </td>
  </tr>
</table>
"""
    # Logic for narratives and predictions would follow...
    return post

def main():
    print("Starting game preview generation...")
    
    # Create output directories if they don't exist
    os.makedirs('_posts', exist_ok=True)
    os.makedirs('_html', exist_ok=True)
    os.makedirs('_seo', exist_ok=True)
    
    CBB_OUTPUT_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/CBB_Output.csv"
    KP_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/kp.csv"
    LOGOS_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/logos.csv"
    CROSSWALK_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/crosswalk.csv"
    
    cbb_output = download_csv(CBB_OUTPUT_URL)
    kp_data = download_csv(KP_URL)
    logos_data = download_csv(LOGOS_URL)
    crosswalk_data = download_csv(CROSSWALK_URL)
    kenpom_stats = pd.read_csv('kenpom_stats.csv')
    
    cbb_output['parsed_time'] = cbb_output['Game Time'].apply(parse_game_time)
    target_games = cbb_output[cbb_output['parsed_time'].notna()]
    
    posts_created = 0
    for game_name in target_games['Game'].unique():
        game_entries = target_games[target_games['Game'] == game_name]
        if len(game_entries) < 2: continue
        
        # Teams directly from CBB_Output
        away_team = game_entries.iloc[0]['Team']
        home_team = game_entries.iloc[1]['Team']
        
        # Logo Lookup Chain
        away_logo = find_team_logo(away_team, logos_data, crosswalk_data)
        home_logo = find_team_logo(home_team, logos_data, crosswalk_data)
        
        away_stats = find_team_in_kenpom(away_team, kenpom_stats)
        home_stats = find_team_in_kenpom(home_team, kenpom_stats)
        
        if away_stats is not None and home_stats is not None:
            post_content = generate_post_content(away_team, home_team, away_stats, home_stats, None, None, away_logo, home_logo, game_entries.iloc[0]['parsed_time'])
            
            # Generate filename
            game_date = game_entries.iloc[0]['parsed_time']
            away_slug = slugify(away_team)
            home_slug = slugify(home_team)
            filename = f"{game_date.strftime('%Y-%m-%d')}-{away_slug}-vs-{home_slug}"
            
            # Save markdown file to _posts
            try:
                md_filepath = os.path.join('_posts', f"{filename}.md")
                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(post_content)
                print(f"  ✓ Created: {md_filepath}")
                posts_created += 1
            except Exception as e:
                print(f"  ✗ Error saving {filename}.md: {e}")
    
    print(f"\n{'='*60}")
    print(f"Generation complete! Created {posts_created} preview posts.")
    print(f"Files created in:")
    print(f"  - _posts/ ({len(os.listdir('_posts'))} files)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

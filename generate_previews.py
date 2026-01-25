#!/usr/bin/env python3
"""
Generate college basketball game matchup preview posts.

This script:
1. Downloads CBB_Output.csv and kp.csv from the trashduty/cbb repository
2. Loads local kenpom_stats.csv
3. Identifies games for the next day
4. Generates markdown preview posts for each game
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import re


def download_csv(url):
    """Download CSV file from URL and return as pandas DataFrame."""
    response = requests.get(url)
    response.raise_for_status()
    from io import StringIO
    return pd.read_csv(StringIO(response.text))


def normalize_team_name(team_name):
    """Normalize team name for consistent matching."""
    # Remove common suffixes (mascots)
    team_name = re.sub(r'\s+(Rainbow Warriors|Matadors|Bulls|Owls|Jaguars|Mastodons|Lakers|Cougars|Huskies|Ducks|Purple Aces|Salukis|Badgers|Trojans)$', '', team_name)
    # Handle special cases
    replacements = {
        "Hawai'i": "Hawaii",
        "CSU Northridge": "CS Northridge",
        "IUPUI": "IU Indy",
        "Fort Wayne": "Purdue Fort Wayne",
    }
    for old, new in replacements.items():
        if old in team_name:
            team_name = team_name.replace(old, new)
    
    # Normalize "St" vs "St."
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
    for _, row in kenpom_df.iterrows():
        if normalize_team_name(row['Team']) == normalized:
            return row
    
    # Try partial match
    for _, row in kenpom_df.iterrows():
        if normalized.lower() in row['Team'].lower() or row['Team'].lower() in normalized.lower():
            return row
    
    return None


def parse_game_time(game_time_str):
    """Parse game time string to datetime object."""
    # Example: "Jan 24 11:59PM ET" or "Jan 25 01:00PM ET"
    try:
        # Remove timezone
        time_str = game_time_str.replace(' ET', '')
        # Parse the date and time
        dt = datetime.strptime(f"2026 {time_str}", "%Y %b %d %I:%M%p")
        return dt
    except Exception as e:
        print(f"Error parsing time '{game_time_str}': {e}")
        return None


def format_stat(value, decimals=1):
    """Format stat value for display."""
    try:
        if pd.isna(value):
            return "N/A"
        if isinstance(value, (int, float)):
            if decimals == 0:
                return str(int(value))
            return f"{float(value):.{decimals}f}"
        return str(value)
    except:
        return "N/A"


def generate_post_content(away_team, home_team, away_stats, home_stats, game_date):
    """Generate markdown content for a game preview post."""
    
    def team_section(team_name, stats, is_away=True):
        """Generate content section for a team."""
        side = "Away" if is_away else "Home"
        
        content = f"""
## {side} Team: {team_name}

### Record & Ranking
- **KenPom Rank:** #{format_stat(stats.get('Rk', 'N/A'), 0)}
- **Offensive Efficiency:** {format_stat(stats.get('OE', 'N/A'))} (Rank: #{format_stat(stats.get('RankOE', 'N/A'), 0)})
- **Defensive Efficiency:** {format_stat(stats.get('DE', 'N/A'))} (Rank: #{format_stat(stats.get('RankDE', 'N/A'), 0)})
- **Tempo:** {format_stat(stats.get('Tempo', 'N/A'))} (Rank: #{format_stat(stats.get('RankTempo', 'N/A'), 0)})

### Offensive Profile

Offensively, the four-factor profile suggests a team that relies on efficient shooting ({format_stat(stats.get('eFG_Pct', 'N/A'))}%, #{format_stat(stats.get('RankeFG_Pct', 'N/A'), 0)}), ball security ({format_stat(stats.get('TO_Pct', 'N/A'))}% turnover rate, #{format_stat(stats.get('RankTO_Pct', 'N/A'), 0)}), offensive rebounding ({format_stat(stats.get('OR_Pct', 'N/A'))}%, #{format_stat(stats.get('RankOR_Pct', 'N/A'), 0)}), and getting to the line ({format_stat(stats.get('FT_Rate', 'N/A'))} FT Rate, #{format_stat(stats.get('RankFT_Rate', 'N/A'), 0)}).

### Shooting Breakdown

- **2-Point Shooting:** {format_stat(stats.get('OffFg2', 'N/A'))}% (Rank: #{format_stat(stats.get('RankOffFg2', 'N/A'), 0)})
- **3-Point Shooting:** {format_stat(stats.get('OffFg3', 'N/A'))}% (Rank: #{format_stat(stats.get('RankOffFg3', 'N/A'), 0)})
- **Free Throw Shooting:** {format_stat(stats.get('OffFt', 'N/A'))}% (Rank: #{format_stat(stats.get('RankOffFt', 'N/A'), 0)})
- **3-Point Rate:** {format_stat(stats.get('F3GRate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankF3GRate', 'N/A'), 0)})

### Defensive Profile

Defensively, they hold opponents to {format_stat(stats.get('DeFG_Pct', 'N/A'))}% effective FG (#{format_stat(stats.get('RankDeFG_Pct', 'N/A'), 0)}), force turnovers at a {format_stat(stats.get('DTO_Pct', 'N/A'))}% rate (#{format_stat(stats.get('RankDTO_Pct', 'N/A'), 0)}), limit offensive rebounds to {format_stat(stats.get('DOR_Pct', 'N/A'))}% (#{format_stat(stats.get('RankDOR_Pct', 'N/A'), 0)}), and allow a {format_stat(stats.get('DFT_Rate', 'N/A'))} FT Rate (#{format_stat(stats.get('RankDFT_Rate', 'N/A'), 0)}).

**Opponent Shooting:**
- **2-Point Defense:** {format_stat(stats.get('DefFg2', 'N/A'))}% (Rank: #{format_stat(stats.get('RankDefFg2', 'N/A'), 0)})
- **3-Point Defense:** {format_stat(stats.get('DefFg3', 'N/A'))}% (Rank: #{format_stat(stats.get('RankDefFg3', 'N/A'), 0)})
- **Block Percentage:** {format_stat(stats.get('BlockPct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankBlockPct', 'N/A'), 0)})
- **Steal Rate:** {format_stat(stats.get('StlRate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankStlRate', 'N/A'), 0)})

### Advanced Metrics

- **Assist Rate:** {format_stat(stats.get('ARate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankARate', 'N/A'), 0)})
- **Experience:** {format_stat(stats.get('Exp', 'N/A'))} (Rank: #{format_stat(stats.get('ExpRank', 'N/A'), 0)})
- **Bench Minutes:** {format_stat(stats.get('Bench', 'N/A'))}% (Rank: #{format_stat(stats.get('BenchRank', 'N/A'), 0)})
- **Continuity:** {format_stat(stats.get('Continuity', 'N/A'))} (Rank: #{format_stat(stats.get('RankContinuity', 'N/A'), 0)})

### Team Composition

- **Average Height:** {format_stat(stats.get('AvgHgt', 'N/A'))}" (Rank: #{format_stat(stats.get('AvgHgtRank', 'N/A'), 0)})
- **Height Efficiency:** {format_stat(stats.get('HgtEff', 'N/A'))} (Rank: #{format_stat(stats.get('HgtEffRank', 'N/A'), 0)})
"""
        return content
    
    # Create the full post
    post = f"""---
layout: post
title: "{away_team} vs {home_team} - Game Preview"
date: {game_date.strftime('%Y-%m-%d')}
categories: [basketball, preview]
---

# {away_team} vs {home_team}
## Game Preview for {game_date.strftime('%B %d, %Y')}

"""
    
    post += team_section(away_team, away_stats, is_away=True)
    post += "\n---\n"
    post += team_section(home_team, home_stats, is_away=False)
    
    return post


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def main():
    print("Starting game preview generation...")
    
    # URLs for external data
    CBB_OUTPUT_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/CBB_Output.csv"
    KP_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/kp.csv"
    
    # Download external data
    print("Downloading CBB_Output.csv...")
    cbb_output = download_csv(CBB_OUTPUT_URL)
    
    print("Downloading kp.csv...")
    kp_data = download_csv(KP_URL)
    
    # Load local KenPom stats
    print("Loading kenpom_stats.csv...")
    kenpom_stats = pd.read_csv('kenpom_stats.csv')
    
    # Determine target date (next day)
    today = datetime.now()
    target_date = today + timedelta(days=1)
    target_date_str = target_date.strftime('%b %d').replace(' 0', ' ')  # e.g., "Jan 25"
    
    print(f"Looking for games on: {target_date_str} (tomorrow)")
    
    # Parse game times and filter for target date
    cbb_output['parsed_time'] = cbb_output['Game Time'].apply(parse_game_time)
    cbb_output = cbb_output[cbb_output['parsed_time'].notna()]
    
    # Filter for target date
    target_games = cbb_output[
        cbb_output['parsed_time'].dt.date == target_date.date()
    ]
    
    print(f"Found {len(target_games)} game entries for {target_date_str}")
    
    # Get unique games
    unique_games = target_games['Game'].unique()
    print(f"Processing {len(unique_games)} unique games...")
    
    posts_created = 0
    
    for game_name in unique_games:
        print(f"\nProcessing: {game_name}")
        game_entries = target_games[target_games['Game'] == game_name]
        
        if len(game_entries) < 2:
            print(f"  Warning: Found only {len(game_entries)} entries for {game_name}")
            continue
        
        # Get the two teams
        teams = game_entries['Team'].tolist()
        if len(teams) < 2:
            print(f"  Warning: Could not find both teams for {game_name}")
            continue
        
        team1, team2 = teams[0], teams[1]
        
        # Determine away and home teams using kp.csv
        # Convert kp date format to match target date
        kp_target_date = target_date.strftime('%Y-%m-%d')
        
        # Normalize team names for matching with kp.csv
        team1_normalized = normalize_team_name(team1)
        team2_normalized = normalize_team_name(team2)
        
        # Find entries in kp.csv for this date and these teams
        # Try exact match first, then normalized
        team1_kp = kp_data[
            (kp_data['date'] == kp_target_date) &
            ((kp_data['team'] == team1) | (kp_data['team'] == team1_normalized))
        ]
        
        team2_kp = kp_data[
            (kp_data['date'] == kp_target_date) &
            ((kp_data['team'] == team2) | (kp_data['team'] == team2_normalized))
        ]
        
        # Determine away/home based on 'side' column
        if not team1_kp.empty and 'side' in team1_kp.columns:
            team1_side = team1_kp.iloc[0]['side']
            if team1_side == 'away':
                away_team, home_team = team1, team2
            else:
                away_team, home_team = team2, team1
        elif not team2_kp.empty and 'side' in team2_kp.columns:
            team2_side = team2_kp.iloc[0]['side']
            if team2_side == 'away':
                away_team, home_team = team2, team1
            else:
                away_team, home_team = team1, team2
        else:
            # Fallback: use order from game name if possible
            print(f"  Warning: Could not determine away/home from kp.csv for {game_name}")
            print(f"  Using team order from game name as fallback")
            away_team, home_team = team1, team2
        
        print(f"  Away: {away_team}")
        print(f"  Home: {home_team}")
        
        # Find stats for both teams
        away_stats = find_team_in_kenpom(away_team, kenpom_stats)
        home_stats = find_team_in_kenpom(home_team, kenpom_stats)
        
        if away_stats is None:
            print(f"  Warning: Could not find stats for {away_team}")
            continue
        
        if home_stats is None:
            print(f"  Warning: Could not find stats for {home_team}")
            continue
        
        print(f"  Found stats for both teams")
        
        # Generate post content
        post_content = generate_post_content(
            away_team, home_team,
            away_stats, home_stats,
            target_date
        )
        
        # Create filename
        away_slug = slugify(away_team)
        home_slug = slugify(home_team)
        filename = f"{target_date.strftime('%Y-%m-%d')}-{away_slug}-vs-{home_slug}.md"
        filepath = os.path.join('_posts', filename)
        
        # Write post to file
        with open(filepath, 'w') as f:
            f.write(post_content)
        
        print(f"  Created: {filepath}")
        posts_created += 1
    
    print(f"\n{'='*60}")
    print(f"Generation complete! Created {posts_created} preview posts.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate college basketball game matchup preview posts.

This script:
1. Downloads CBB_Output.csv and kp.csv from the trashduty/cbb repository
2. Loads local kenpom_stats.csv
3. Identifies games for today and tomorrow
4. Generates markdown preview posts for each game
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import re


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


def find_team_logo(team_name, logos_df):
    """Find team logo URL from logos dataframe using only exact matches on ncaa_name."""
    # Normalize the search term
    normalized = normalize_team_name(team_name)
    
    # First priority: Try exact match on ncaa_name
    exact_match = logos_df[logos_df['ncaa_name'].str.strip() == team_name.strip()]
    if not exact_match.empty:
        return exact_match.iloc[0]['logos']
    
    # Second priority: Try exact match on normalized ncaa_name
    exact_match = logos_df[logos_df['ncaa_name'].str.strip() == normalized.strip()]
    if not exact_match.empty:
        return exact_match.iloc[0]['logos']
    
    # Third priority: Try case-insensitive exact match on ncaa_name
    for _, row in logos_df.iterrows():
        if str(row['ncaa_name']).strip().lower() == team_name.strip().lower():
            return row['logos']
    
    # Fourth priority: Try case-insensitive exact match on normalized ncaa_name
    for _, row in logos_df.iterrows():
        if str(row['ncaa_name']).strip().lower() == normalized.strip().lower():
            return row['logos']
    
    # Fifth priority: Try exact match on other columns (name, reference_name)
    for col in ['name', 'reference_name']:
        exact_match = logos_df[logos_df[col].str.strip() == normalized.strip()]
        if not exact_match.empty:
            return exact_match.iloc[0]['logos']
    
    # Sixth priority: Try case-insensitive exact match on other columns
    for col in ['name', 'reference_name']:
        for _, row in logos_df.iterrows():
            if str(row[col]).strip().lower() == normalized.strip().lower():
                return row['logos']
    
    # Return a default placeholder if no match found
    print(f"  Warning: No logo found for '{team_name}' (normalized: '{normalized}')")
    return "https://via.placeholder.com/150"


def parse_game_time(game_time_str):
    """Parse game time string to datetime object."""
    # Example: "Jan 24 11:59PM ET" or "Jan 25 01:00PM ET"
    try:
        # Remove timezone
        time_str = game_time_str.replace(' ET', '')
        # Parse the date and time using current year
        current_year = datetime.now().year
        dt = datetime.strptime(f"{current_year} {time_str}", "%Y %b %d %I:%M%p")
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


def format_percentage(value):
    """Format probability value as percentage."""
    try:
        if pd.isna(value):
            return "N/A"
        # If value is already a percentage (>1), use as is
        if float(value) > 1:
            return f"{float(value):.1f}%"
        # If value is a decimal (0-1), convert to percentage
        return f"{float(value) * 100:.1f}%"
    except:
        return "N/A"


def format_moneyline(value):
    """Format moneyline odds."""
    try:
        val = float(value)
        if val > 0:
            return f"+{int(val)}"
        else:
            return str(int(val))
    except:
        return "N/A"


def get_rank_description(rank):
    """Get descriptive text for a team's rank."""
    try:
        rank = int(rank)
        if rank <= 25:
            return "elite"
        elif rank <= 50:
            return "very strong"
        elif rank <= 100:
            return "solid"
        elif rank <= 200:
            return "middle-of-the-pack"
        else:
            return "struggling"
    except:
        return "N/A"


def generate_betting_info(away_team, home_team, away_predictions, home_predictions):
    """Generate betting lines section."""
    try:
        # Get spread - use the favorite's line (negative number)
        away_spread = float(away_predictions.get('market_spread', 0))
        home_spread = float(home_predictions.get('market_spread', 0))
        
        if away_spread < 0:
            spread_text = f"{away_team} {away_spread}"
        elif home_spread < 0:
            spread_text = f"{home_team} {home_spread}"
        else:
            spread_text = "Pick'em"
        
        # Get moneylines from "Current Moneyline" column
        away_ml = format_moneyline(away_predictions.get('Current Moneyline', 'N/A'))
        home_ml = format_moneyline(home_predictions.get('Current Moneyline', 'N/A'))
        
        # Get total from "Opening Total" column (should be same for both)
        total = format_stat(away_predictions.get('Opening Total', 'N/A'), 1)
        
        betting_info = f"""
<div style="text-align: center; margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px;">
  <h3 style="margin-top: 0;">Betting Lines</h3>
  <p style="font-size: 1.1em; margin: 10px 0;"><strong>Spread:</strong> {spread_text}</p>
  <p style="font-size: 1.1em; margin: 10px 0;"><strong>Moneyline:</strong> {away_team} ({away_ml}) | {home_team} ({home_ml})</p>
  <p style="font-size: 1.1em; margin: 10px 0;"><strong>Total:</strong> {total}</p>
</div>
"""
        return betting_info
    except Exception as e:
        print(f"  Warning: Could not generate betting info: {e}")
        return ""


def generate_game_narrative(away_team, home_team, away_stats, home_stats):
    """Generate conversational narrative comparing the two teams."""
    
    try:
        away_rank = int(away_stats.get('Rk', 999))
        home_rank = int(home_stats.get('Rk', 999))
        away_oe_rank = int(away_stats.get('RankOE', 999))
        home_oe_rank = int(home_stats.get('RankOE', 999))
        away_de_rank = int(away_stats.get('RankDE', 999))
        home_de_rank = int(home_stats.get('RankDE', 999))
        away_tempo = float(away_stats.get('Tempo', 0))
        home_tempo = float(home_stats.get('Tempo', 0))
        away_fg3_pct = float(away_stats.get('FG3Pct', 0))
        home_fg3_pct = float(home_stats.get('FG3Pct', 0))
        away_opp_fg3_pct = float(home_stats.get('OppFG3Pct', 0))
        home_opp_fg3_pct = float(home_stats.get('OppFG3Pct', 0))
    except:
        return ""
    
    narrative = "### Game Storylines\n\n"
    
    # Overall matchup comparison
    rank_diff = abs(away_rank - home_rank)
    if rank_diff <= 10:
        narrative += f"This matchup features two evenly-matched teams, with {away_team} at #{away_rank} and {home_team} at #{home_rank} in the KenPom rankings. Expect a competitive battle throughout. "
    elif rank_diff <= 50:
        favorite = away_team if away_rank < home_rank else home_team
        underdog = home_team if away_rank < home_rank else away_team
        narrative += f"On paper, {favorite} holds the advantage as the higher-ranked team, but {underdog} could make this interesting if they play to their potential. "
    else:
        favorite = away_team if away_rank < home_rank else home_team
        underdog = home_team if away_rank < home_rank else away_team
        narrative += f"This looks like a mismatch on paper with {favorite} significantly higher in the rankings, but as they say, that's why they play the games. {underdog} will need their best performance of the season to pull off the upset. "
    
    # Offensive vs Defensive matchup
    narrative += "\n\n**Key Matchup: "
    if away_oe_rank < home_de_rank - 50:
        narrative += f"{away_team}'s Offense vs {home_team}'s Defense**\n\n"
        narrative += f"{away_team} brings a {get_rank_description(away_oe_rank)} offense (ranked #{away_oe_rank}) that could exploit {home_team}'s defensive vulnerabilities (ranked #{home_de_rank}). "
    elif home_oe_rank < away_de_rank - 50:
        narrative += f"{home_team}'s Offense vs {away_team}'s Defense**\n\n"
        narrative += f"{home_team} features a {get_rank_description(home_oe_rank)} offense (ranked #{home_oe_rank}) that should find success against {away_team}'s defensive unit (ranked #{away_de_rank}). "
    elif away_de_rank < 50 and home_oe_rank > 150:
        narrative += f"{away_team}'s Defense vs {home_team}'s Offense**\n\n"
        narrative += f"{away_team}'s stingy defense (ranked #{away_de_rank}) will look to frustrate {home_team}'s offense, which has struggled at times this season. "
    elif home_de_rank < 50 and away_oe_rank > 150:
        narrative += f"{home_team}'s Defense vs {away_team}'s Offense**\n\n"
        narrative += f"{home_team}'s defensive prowess (ranked #{home_de_rank}) sets up well against {away_team}'s offense. Expect a grind-it-out game. "
    else:
        narrative += "The Battle in the Trenches**\n\n"
        narrative += f"Both teams are fairly evenly matched on both ends of the floor. This could come down to execution in crunch time. "
    
    # Tempo analysis
    tempo_diff = abs(away_tempo - home_tempo)
    if tempo_diff > 5:
        faster_team = away_team if away_tempo > home_tempo else home_team
        slower_team = home_team if away_tempo > home_tempo else away_team
        narrative += f"\n\n**Pace of Play:** {faster_team} likes to push the pace, while {slower_team} prefers a more deliberate approach. The team that can impose their preferred tempo will have a significant advantage. "
    
    # Three-point shooting matchup
    if away_fg3_pct > 35 and home_opp_fg3_pct < 32:
        narrative += f"\n\n**X-Factor:** {away_team} can light it up from three-point range ({away_fg3_pct:.1f}%), but {home_team} defends the arc exceptionally well, holding opponents to just {home_opp_fg3_pct:.1f}%. This battle could determine the outcome. "
    elif home_fg3_pct > 35 and away_opp_fg3_pct < 32:
        narrative += f"\n\n**X-Factor:** {home_team}'s three-point shooting ({home_fg3_pct:.1f}%) faces a tough test against {away_team}'s perimeter defense, which limits opponents to {away_opp_fg3_pct:.1f}% from deep. "
    elif away_fg3_pct > 37 and home_fg3_pct > 37:
        narrative += f"\n\n**Shootout Alert:** Both teams can stroke it from downtown. Don't be surprised if this turns into a high-scoring affair with plenty of made threes. "
    
    return narrative + "\n\n"


def generate_predictions_section(away_team, home_team, away_predictions, home_predictions):
    """Generate the model predictions section."""
    
    # Extract prediction values
    away_spread = format_stat(away_predictions.get('Predicted Outcome', 'N/A'), 1)
    away_spread_edge = format_percentage(away_predictions.get('Edge For Covering Spread', 'N/A'))
    home_spread = format_stat(home_predictions.get('Predicted Outcome', 'N/A'), 1)
    home_spread_edge = format_percentage(home_predictions.get('Edge For Covering Spread', 'N/A'))
    
    away_ml_prob = format_percentage(away_predictions.get('Moneyline Win Probability', 'N/A'))
    home_ml_prob = format_percentage(home_predictions.get('Moneyline Win Probability', 'N/A'))
    
    # For total, we can use either team's row (should be the same)
    predicted_total = format_stat(away_predictions.get('average_total', 'N/A'), 1)
    over_edge = format_percentage(away_predictions.get('Over Total Edge', 'N/A'))
    under_edge = format_percentage(away_predictions.get('Under Total Edge', 'N/A'))
    
    predictions = f"""
---

## Model Predictions

All that being said, here's how our model prices this game.

### Spread
- **{away_team}**: {away_spread}, Cover Probability: {away_spread_edge}
- **{home_team}**: {home_spread}, Cover Probability: {home_spread_edge}

### Moneyline
- **{away_team} Win Probability**: {away_ml_prob}
- **{home_team} Win Probability**: {home_ml_prob}

### Total
- **Predicted Total**: {predicted_total}
- **Over Cover Probability**: {over_edge}
- **Under Cover Probability**: {under_edge}

---

To see predictions for spreads, moneylines, and totals for every D1 men's college basketball game, be sure to get access at [btb-analytics.com](https://btb-analytics.com)
"""
    
    return predictions


def generate_post_content(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions, away_logo, home_logo, game_date):
    """Generate markdown content for a game preview post."""
    
    # Track which analysis snippets have been used to avoid duplicates
    used_snippets = set()
    
    def team_section(team_name, stats, is_away=True):
        """Generate content section for a team."""
        side = "Away" if is_away else "Home"
        
        # Generate conversational analysis without duplicates
        try:
            rank = int(stats.get('Rk', 999))
            oe_rank = int(stats.get('RankOE', 999))
            de_rank = int(stats.get('RankDE', 999))
            fg3_pct = float(stats.get('FG3Pct', 0))
            fg3_rank = int(stats.get('RankFG3Pct', 999))
            opp_fg3_pct = float(stats.get('OppFG3Pct', 0))
            opp_fg3_rank = int(stats.get('RankOppFG3Pct', 999))
            
            offensive_style = ""
            # Good 3-point shooting
            if fg3_pct > 36 and fg3_rank < 100 and "good_3pt" not in used_snippets:
                offensive_style = f"They're dangerous from beyond the arc, shooting {fg3_pct:.1f}% from three (ranked #{fg3_rank} nationally), so expect them to let it fly from deep. "
                used_snippets.add("good_3pt")
            # Poor 3-point shooting
            elif fg3_pct < 32 and "poor_3pt" not in used_snippets:
                offensive_style = "The three-point shot hasn't been falling this season, so look for them to attack the paint and work inside-out. "
                used_snippets.add("poor_3pt")
            # Alternative for poor shooting if already used
            elif fg3_pct < 32 and "poor_3pt" in used_snippets and "alt_poor_3pt" not in used_snippets:
                offensive_style = "They've struggled from deep this year, meaning they'll need to rely on interior scoring and getting to the free throw line. "
                used_snippets.add("alt_poor_3pt")
            # Strong offensive efficiency
            elif oe_rank < 50 and "strong_offense" not in used_snippets:
                offensive_style = f"They boast one of the nation's top offenses, ranked #{oe_rank} in efficiency. "
                used_snippets.add("strong_offense")
            
            defensive_style = ""
            # Elite perimeter defense
            if opp_fg3_pct < 30 and opp_fg3_rank < 100 and "elite_perimeter_d" not in used_snippets:
                defensive_style = f"On the defensive end, they're lockdown on the perimeter, holding opponents to just {opp_fg3_pct:.1f}% from three. "
                used_snippets.add("elite_perimeter_d")
            # Strong overall defense
            elif de_rank < 50 and "strong_defense" not in used_snippets:
                defensive_style = "Their defense has been a calling card this season, making life difficult for opposing offenses. "
                used_snippets.add("strong_defense")
            # Alternative strong defense
            elif de_rank < 50 and "strong_defense" in used_snippets and "alt_strong_defense" not in used_snippets:
                defensive_style = f"Defensively, they've been rock solid, ranking #{de_rank} nationally in efficiency. "
                used_snippets.add("alt_strong_defense")
            # Weak defense
            elif de_rank > 250 and "weak_defense" not in used_snippets:
                defensive_style = "Defense has been a struggle, and they'll need to tighten things up to have a chance in this one. "
                used_snippets.add("weak_defense")
            # Alternative weak defense
            elif de_rank > 250 and "weak_defense" in used_snippets and "alt_weak_defense" not in used_snippets:
                defensive_style = "Stopping opponents has been an issue all season long. "
                used_snippets.add("alt_weak_defense")
                
        except:
            offensive_style = ""
            defensive_style = ""
        
        content = f"""
## Team: {team_name}

{team_name} comes in ranked #{format_stat(stats.get('Rk', 'N/A'), 0)} overall by KenPom. {offensive_style}{defensive_style}

### Record & Ranking
- **KenPom Rank:** #{format_stat(stats.get('Rk', 'N/A'), 0)}
- **Offensive Efficiency:** {format_stat(stats.get('OE', 'N/A'))} (Rank: #{format_stat(stats.get('RankOE', 'N/A'), 0)})
- **Defensive Efficiency:** {format_stat(stats.get('DE', 'N/A'))} (Rank: #{format_stat(stats.get('RankDE', 'N/A'), 0)})
- **Tempo:** {format_stat(stats.get('Tempo', 'N/A'))} (Rank: #{format_stat(stats.get('RankTempo', 'N/A'), 0)})

### Shooting Breakdown

- **2-Point Shooting:** {format_stat(stats.get('FG2Pct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankFG2Pct', 'N/A'), 0)})
- **3-Point Shooting:** {format_stat(stats.get('FG3Pct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankFG3Pct', 'N/A'), 0)})
- **Free Throw Shooting:** {format_stat(stats.get('FTPct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankFTPct', 'N/A'), 0)})
- **3-Point Rate:** {format_stat(stats.get('F3GRate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankF3GRate', 'N/A'), 0)})

### Defensive Stats

- **Opponent 2-Point Shooting:** {format_stat(stats.get('OppFG2Pct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankOppFG2Pct', 'N/A'), 0)})
- **Opponent 3-Point Shooting:** {format_stat(stats.get('OppFG3Pct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankOppFG3Pct', 'N/A'), 0)})
- **Block Percentage:** {format_stat(stats.get('BlockPct', 'N/A'))}% (Rank: #{format_stat(stats.get('RankBlockPct', 'N/A'), 0)})
- **Steal Rate:** {format_stat(stats.get('StlRate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankStlRate', 'N/A'), 0)})

### Team Metrics

- **Assist Rate:** {format_stat(stats.get('ARate', 'N/A'))}% (Rank: #{format_stat(stats.get('RankARate', 'N/A'), 0)})
- **Experience:** {format_stat(stats.get('Exp', 'N/A'))} years (Rank: #{format_stat(stats.get('ExpRank', 'N/A'), 0)})
- **Bench Minutes:** {format_stat(stats.get('Bench', 'N/A'))}% (Rank: #{format_stat(stats.get('BenchRank', 'N/A'), 0)})
- **Average Height:** {format_stat(stats.get('AvgHgt', 'N/A'))}" (Rank: #{format_stat(stats.get('AvgHgtRank', 'N/A'), 0)})
"""
        return content
    
    # Create the full post with centered logos using table
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
    <td style="width: 45%; text-align: center; vertical-align: middle;">
      <img src="{away_logo}" alt="{away_team} logo" style="width: 150px; height: 150px; object-fit: contain; display: block; margin: 0 auto;">
      <p><strong>{away_team}</strong></p>
    </td>
    <td style="width: 10%; text-align: center; vertical-align: middle; font-size: 2em; font-weight: bold;">
      VS
    </td>
    <td style="width: 45%; text-align: center; vertical-align: middle;">
      <img src="{home_logo}" alt="{home_team} logo" style="width: 150px; height: 150px; object-fit: contain; display: block; margin: 0 auto;">
      <p><strong>{home_team}</strong></p>
    </td>
  </tr>
</table>

"""
    
    # Add betting information
    post += generate_betting_info(away_team, home_team, away_predictions, home_predictions)
    
    # Add game narrative
    post += "\n" + generate_game_narrative(away_team, home_team, away_stats, home_stats)
    
    post += team_section(away_team, away_stats, is_away=True)
    post += "\n---\n"
    post += team_section(home_team, home_stats, is_away=False)
    post += "\n"
    post += generate_predictions_section(away_team, home_team, away_predictions, home_predictions)
    
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
    LOGOS_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/logos.csv"
    
    # Download external data
    print("Downloading CBB_Output.csv...")
    cbb_output = download_csv(CBB_OUTPUT_URL)
    
    print("Downloading kp.csv...")
    kp_data = download_csv(KP_URL)
    
    print("Downloading logos.csv...")
    logos_data = download_csv(LOGOS_URL)
    
    # Load local KenPom stats
    print("Loading kenpom_stats.csv...")
    kenpom_stats = pd.read_csv('kenpom_stats.csv')
    
    # Determine target dates (today and tomorrow)
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    print(f"Looking for games on: {today.strftime('%b %d').replace(' 0', ' ')} (today) and {tomorrow.strftime('%b %d').replace(' 0', ' ')} (tomorrow)")

    # Parse game times and filter for valid dates
    cbb_output['parsed_time'] = cbb_output['Game Time'].apply(parse_game_time)
    cbb_output = cbb_output[cbb_output['parsed_time'].notna()]

    # Filter for today and tomorrow
    target_games = cbb_output[
        (cbb_output['parsed_time'].dt.date == today.date()) |
        (cbb_output['parsed_time'].dt.date == tomorrow.date())
    ]

    today_str = today.strftime('%b %d').replace(' 0', ' ')
    tomorrow_str = tomorrow.strftime('%b %d').replace(' 0', ' ')
    print(f"Found {len(target_games)} game entries for {today_str} and {tomorrow_str}")
    
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
        # Convert kp date format to match target dates
        kp_today = today.strftime('%Y-%m-%d')
        kp_tomorrow = tomorrow.strftime('%Y-%m-%d')
        
        # Normalize team names for matching with kp.csv
        team1_normalized = normalize_team_name(team1)
        team2_normalized = normalize_team_name(team2)
        
        # Find entries in kp.csv for these dates and teams
        team1_kp = kp_data[
            ((kp_data['date'] == kp_today) | (kp_data['date'] == kp_tomorrow)) &
            ((kp_data['team'] == team1) | (kp_data['team'] == team1_normalized))
        ]
        
        team2_kp = kp_data[
            ((kp_data['date'] == kp_today) | (kp_data['date'] == kp_tomorrow)) &
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
        print(f"  Away team matched: {away_stats.get('Team', 'Unknown')} (Rank: {away_stats.get('Rk', 'N/A')})")
        print(f"  Home team matched: {home_stats.get('Team', 'Unknown')} (Rank: {home_stats.get('Rk', 'N/A')})")
        
        # Find logos for both teams
        away_logo = find_team_logo(away_team, logos_data)
        home_logo = find_team_logo(home_team, logos_data)
        print(f"  Away logo: {away_logo}")
        print(f"  Home logo: {home_logo}")
        
        # Get predictions for both teams from game_entries
        away_predictions = game_entries[game_entries['Team'] == away_team].iloc[0]
        home_predictions = game_entries[game_entries['Team'] == home_team].iloc[0]
        
        # Get the actual game date from parsed_time
        game_date = game_entries.iloc[0]['parsed_time']
        
        # Generate post content
        post_content = generate_post_content(
            away_team, home_team,
            away_stats, home_stats,
            away_predictions, home_predictions,
            away_logo, home_logo,
            game_date
        )
        
        # Create filename
        away_slug = slugify(away_team)
        home_slug = slugify(home_team)
        filename = f"{game_date.strftime('%Y-%m-%d')}-{away_slug}-vs-{home_slug}.md"
        
        # Ensure _posts directory exists
        os.makedirs('_posts', exist_ok=True)
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

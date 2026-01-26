#!/usr/bin/env python3
"""
Generate college basketball game matchup preview posts.

This script:
1. Downloads CBB_Output.csv and kp.csv from the trashduty/cbb repository
2. Loads local kenpom_stats.csv
3. Identifies games for today and tomorrow
4. Generates markdown preview posts for each game
5. Generates SEO-optimized HTML versions for Squarespace
"""

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


def find_team_logo(team_name, logos_df, crosswalk_df):
    """
    Find team logo URL using the specific crosswalk-to-kenpom-to-logo-ncaa_name chain.
    
    1. Find team name in crosswalk.csv
    2. Convert to 'kenpom' column name
    3. Search logos.csv 'ncaa_name' column using the KenPom name
    """
    
    if crosswalk_df is None or crosswalk_df.empty:
        print(f"  Warning: Crosswalk data is missing for '{team_name}' logo lookup.")
        return "https://via.placeholder.com/150"

    # Step 1 & 2: Find team in crosswalk and get 'kenpom' name
    kenpom_name = None
    team_name_lower = team_name.strip().lower()
    
    for _, row in crosswalk_df.iterrows():
        match_found = False
        # Search across all columns in the crosswalk for the team name
        for col in crosswalk_df.columns:
            if str(row[col]).strip().lower() == team_name_lower:
                kenpom_name = str(row['kenpom']).strip()
                match_found = True
                break
        if match_found:
            break
            
    if not kenpom_name:
        print(f"  Warning: No 'kenpom' mapping found in crosswalk for '{team_name}'")
        # If not in crosswalk, use the original name as a last resort
        kenpom_name = team_name
        
    # Step 3: Use kenpom_name to find logo in logos_df['ncaa_name']
    if 'ncaa_name' in logos_df.columns:
        # Try exact match first
        match = logos_df[logos_df['ncaa_name'] == kenpom_name]
        if not match.empty:
            return match.iloc[0]['logos']
            
        # Try case-insensitive match on ncaa_name
        kenpom_name_lower = kenpom_name.lower()
        for _, row in logos_df.iterrows():
            if str(row['ncaa_name']).lower().strip() == kenpom_name_lower:
                return row['logos']

    # Final fallback if the chain breaks
    print(f"  Warning: No logo found in logos.csv for kenpom name '{kenpom_name}' (original: '{team_name}')")
    return "https://via.placeholder.com/150"


def parse_game_time(game_time_str):
    """Parse game time string to datetime object."""
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
        if float(value) > 1:
            return f"{float(value):.1f}%"
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


def generate_seo_metadata(away_team, home_team, game_date, away_predictions, home_predictions):
    """Generate comprehensive SEO metadata."""
    try:
        away_spread = float(away_predictions.get('market_spread', 0))
        home_spread = float(home_predictions.get('market_spread', 0))
        if away_spread < 0:
            spread_text = f"{away_team} {away_spread}"
            favorite = away_team
        elif home_spread < 0:
            spread_text = f"{home_team} {home_spread}"
            favorite = home_team
        else:
            spread_text = "Pick'em"
            favorite = away_team
        total = format_stat(away_predictions.get('Opening Total', 'N/A'), 1)
    except:
        spread_text = "N/A"
        total = "N/A"
        favorite = away_team
    
    seo_title = f"{away_team} vs {home_team} Prediction & Picks - {game_date.strftime('%b %d')}"
    meta_description = f"Expert {away_team} vs {home_team} prediction for {game_date.strftime('%B %d, %Y')}. Spread: {spread_text}, Total: {total}. View our model's picks and KenPom analysis."

    keywords = [f"{away_team}", f"{home_team}", "college basketball prediction", "KenPom"]
    slug = f"{game_date.strftime('%Y-%m-%d')}-{slugify(away_team)}-vs-{slugify(home_team)}"
    
    return {
        'seo_title': seo_title,
        'meta_description': meta_description,
        'keywords': ', '.join(keywords),
        'og_title': f"{away_team} vs {home_team}: Prediction & Betting Analysis",
        'og_description': f"Our model predicts {favorite} covers. Full analysis for {game_date.strftime('%B %d')}.",
        'canonical_url': f"https://btb-analytics.com/blog/{slug}",
        'slug': slug
    }


def convert_to_html(markdown_content):
    """Convert markdown to clean, SEO-optimized HTML for Squarespace with dark theme."""
    lines = markdown_content.split('\n')
    if lines[0] == '---':
        try:
            end_idx = lines[1:].index('---') + 1
            markdown_content = '\n'.join(lines[end_idx+1:])
        except ValueError:
            pass
    
    html = markdown_content
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)
    html = html.replace('---', '<hr>')
    
    lines = html.split('\n')
    in_list, new_lines = False, []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            new_lines.append(f'  <li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list: new_lines.append('</ul>')
    html = '\n'.join(new_lines)
    
    lines = html.split('\n')
    new_lines, in_paragraph = [], False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('<'):
            if in_paragraph:
                new_lines.append('</p>')
                in_paragraph = False
            new_lines.append(line)
        else:
            if not in_paragraph:
                new_lines.append('<p>')
                in_paragraph = True
            new_lines.append(line)
    if in_paragraph: new_lines.append('</p>')
    html = '\n'.join(new_lines)
    
    css = """
<style>
  .game-preview-container { max-width: 800px; margin: 0 auto; color: #ffffff; line-height: 1.6; }
  .betting-lines { text-align: center; margin: 20px 0; padding: 20px; background-color: #000000; border-radius: 8px; border: 2px solid #23A354; }
  .betting-lines h3 { color: #23A354; }
  table { width: 100%; margin: 20px 0; border-collapse: collapse; }
  td { text-align: center; vertical-align: middle; padding: 10px; }
  td img { width: 150px; height: 150px; object-fit: contain; }
  h1, h2, h3, strong, a { color: #23A354; }
  hr { border: none; border-top: 2px solid #23A354; margin: 30px 0; }
</style>
"""
    return f"{css}\n<div class=\"game-preview-container\">\n{html}\n</div>"


def generate_betting_info(away_team, home_team, away_predictions, home_predictions):
    """Generate betting lines section."""
    try:
        away_spread = float(away_predictions.get('market_spread', 0))
        home_spread = float(home_predictions.get('market_spread', 0))
        spread_text = f"{away_team} {away_spread}" if away_spread < 0 else (f"{home_team} {home_spread}" if home_spread < 0 else "Pick'em")
        away_ml = format_moneyline(away_predictions.get('Current Moneyline', 'N/A'))
        home_ml = format_moneyline(home_predictions.get('Current Moneyline', 'N/A'))
        total = format_stat(away_predictions.get('Opening Total', 'N/A'), 1)
        
        return f"""
<div class="betting-lines">
  <h3>Betting Lines</h3>
  <p><strong>Spread:</strong> {spread_text}</p>
  <p><strong>Moneyline:</strong> {away_team} ({away_ml}) | {home_team} ({home_ml})</p>
  <p><strong>Total:</strong> {total}</p>
</div>
"""
    except Exception as e:
        return ""


def generate_enhanced_narrative(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions):
    """Generate professional-style enhanced narrative content with betting insights."""
    try:
        away_rank = int(away_stats.get('Rk', UNRANKED_DEFAULT))
        home_rank = int(home_stats.get('Rk', UNRANKED_DEFAULT))
        away_oe, home_oe = float(away_stats.get('OE', 0)), float(home_stats.get('OE', 0))
        away_de, home_de = float(away_stats.get('DE', 0)), float(home_stats.get('DE', 0))
        away_tempo, home_tempo = float(away_stats.get('Tempo', 0)), float(home_stats.get('Tempo', 0))
        away_spread = float(away_predictions.get('market_spread', 0))
        home_spread = float(home_predictions.get('market_spread', 0))
        total = float(away_predictions.get('Opening Total', 0))
        
        favorite = away_team if away_spread < 0 else home_team
        underdog = home_team if away_spread < 0 else away_team
        spread_value = abs(away_spread) if away_spread < 0 else abs(home_spread)
    except:
        return ""
    
    sections = ["### Game Analysis & Betting Breakdown\n", "#### Setting the Stage\n"]
    sections.append(f"{away_team} travels to face {home_team}. The early betting action has shaped into {favorite} favored by {spread_value:.1f} points, with the total sitting at {total:.1f}.\n")
    
    sections.append("\n#### Breaking Down the Spread\n")
    sections.append(f"The {spread_value:.1f}-point spread indicates {favorite} is viewed as the better team. ")
    sections.append(f"The total of {total:.1f} points to the scoring expectations for this matchup.\n")
    
    sections.append("\n#### Offensive Firepower\n")
    sections.append(f"**{away_team}** bring an offensive efficiency of {away_oe:.2f}, while **{home_team}** counter with {home_oe:.2f}.\n")
    
    sections.append("\n#### Tempo & Playing Style\n")
    sections.append(f"{away_team} operate at a {away_tempo:.1f} tempo, while {home_team} play at {home_tempo:.1f}.\n")
    
    return ''.join(sections)


def generate_game_narrative(away_team, home_team, away_stats, home_stats):
    """Generate conversational narrative comparing the two teams."""
    try:
        away_rank, home_rank = int(away_stats.get('Rk', 999)), int(home_stats.get('Rk', 999))
    except:
        return ""
    
    narrative = "### Game Storylines\n\n"
    rank_diff = abs(away_rank - home_rank)
    if rank_diff <= 15:
        narrative += f"This matchup features two evenly-matched teams according to KenPom (#{away_rank} vs #{home_rank})."
    else:
        favorite = away_team if away_rank < home_rank else home_team
        narrative += f"On paper, {favorite} holds the advantage as the higher-ranked team."
    
    return narrative + "\n\n"


def generate_predictions_section(away_team, home_team, away_predictions, home_predictions):
    """Generate the model predictions section."""
    away_spread = format_stat(away_predictions.get('Predicted Outcome', 'N/A'), 1)
    away_edge = format_percentage(away_predictions.get('Edge For Covering Spread', 'N/A'))
    home_spread = format_stat(home_predictions.get('Predicted Outcome', 'N/A'), 1)
    home_edge = format_percentage(home_predictions.get('Edge For Covering Spread', 'N/A'))
    
    predicted_total = format_stat(away_predictions.get('average_total', 'N/A'), 1)
    over_edge = format_percentage(away_predictions.get('Over Total Edge', 'N/A'))
    under_edge = format_percentage(away_predictions.get('Under Total Edge', 'N/A'))
    
    return f"""
---
## Model Predictions

### Spread
- **{away_team}**: {away_spread}, Edge: {away_edge}
- **{home_team}**: {home_spread}, Edge: {home_edge}

### Total
- **Predicted Total**: {predicted_total}
- **Edge Over**: {over_edge}
- **Edge Under**: {under_edge}

To see all predictions, visit [btb-analytics.com](https://btb-analytics.com)
"""


def generate_post_content(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions, away_logo, home_logo, game_date):
    """Generate markdown content for a game preview post."""
    
    def team_section(team_name, stats, is_away=True):
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
    post += generate_betting_info(away_team, home_team, away_predictions, home_predictions)
    post += "\n" + generate_enhanced_narrative(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions)
    post += "\n" + generate_game_narrative(away_team, home_team, away_stats, home_stats)
    post += team_section(away_team, away_stats, is_away=True)
    post += "\n---\n"
    post += team_section(home_team, home_stats, is_away=False)
    post += "\n" + generate_predictions_section(away_team, home_team, away_predictions, home_predictions)
    
    return post


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def main():
    print("Starting game preview generation...")
    
    CBB_OUTPUT_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/CBB_Output.csv"
    KP_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/kp.csv"
    LOGOS_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/logos.csv"
    CROSSWALK_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/crosswalk.csv"
    
    cbb_output = download_csv(CBB_OUTPUT_URL)
    kp_data = download_csv(KP_URL)
    logos_data = download_csv(LOGOS_URL)
    crosswalk_data = download_csv(CROSSWALK_URL)
    kenpom_stats = pd.read_csv('kenpom_stats.csv')
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    cbb_output['parsed_time'] = cbb_output['Game Time'].apply(parse_game_time)
    cbb_output = cbb_output[cbb_output['parsed_time'].notna()]
    target_games = cbb_output[
        (cbb_output['parsed_time'].dt.date == today.date()) |
        (cbb_output['parsed_time'].dt.date == tomorrow.date())
    ]
    
    unique_games = target_games['Game'].unique()
    os.makedirs('_posts', exist_ok=True)
    os.makedirs('_html', exist_ok=True)
    os.makedirs('_seo', exist_ok=True)
    
    for game_name in unique_games:
        game_entries = target_games[target_games['Game'] == game_name]
        if len(game_entries) < 2: continue
        
        teams = game_entries['Team'].tolist()
        team1, team2 = teams[0], teams[1]
        
        # Determine Away/Home using kp_data side column
        kp_today = today.strftime('%Y-%m-%d')
        team1_kp = kp_data[(kp_data['date'] == kp_today) & (kp_data['team'].str.contains(team1, case=False, na=False))]
        
        if not team1_kp.empty and team1_kp.iloc[0]['side'] == 'away':
            away_team, home_team = team1, team2
        else:
            away_team, home_team = team2, team1
            
        away_stats = find_team_in_kenpom(away_team, kenpom_stats)
        home_stats = find_team_in_kenpom(home_team, kenpom_stats)
        if away_stats is None or home_stats is None: continue
        
        # LOGO LOOKUP CHAIN: CBB_Output -> Crosswalk (any col) -> Crosswalk[kenpom] -> Logos[ncaa_name]
        away_logo = find_team_logo(away_team, logos_data, crosswalk_data)
        home_logo = find_team_logo(home_team, logos_data, crosswalk_data)
        
        away_predictions = game_entries[game_entries['Team'] == away_team].iloc[0]
        home_predictions = game_entries[game_entries['Team'] == home_team].iloc[0]
        game_date = game_entries.iloc[0]['parsed_time']
        
        post_content = generate_post_content(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions, away_logo, home_logo, game_date)
        filename = f"{game_date.strftime('%Y-%m-%d')}-{slugify(away_team)}-vs-{slugify(home_team)}"
        
        with open(os.path.join('_posts', f"{filename}.md"), 'w', encoding='utf-8') as f:
            f.write(post_content)
        with open(os.path.join('_html', f"{filename}.html"), 'w', encoding='utf-8') as f:
            f.write(convert_to_html(post_content))
            
    print("Generation complete!")

if __name__ == "__main__":
    main()

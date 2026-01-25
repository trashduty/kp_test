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


def generate_seo_metadata(away_team, home_team, game_date, away_predictions, home_predictions):
    """Generate comprehensive SEO metadata."""
    
    try:
        # Get betting info
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
    
    # SEO Title (60 characters max for best display)
    seo_title = f"{away_team} vs {home_team} Prediction & Picks - {game_date.strftime('%b %d')}"
    
    # Meta Description (155-160 characters for optimal display)
    meta_description = f"Expert {away_team} vs {home_team} prediction for {game_date.strftime('%B %d, %Y')}. Spread: {spread_text}, Total: {total}. View our model's picks, KenPom analysis & betting edge."
    
    # Keywords
    keywords = [
        f"{away_team}",
        f"{home_team}",
        f"{away_team} vs {home_team}",
        "college basketball prediction",
        "college basketball picks",
        "betting picks",
        "game preview",
        "KenPom",
        f"{away_team} prediction",
        f"{home_team} prediction",
        f"{game_date.strftime('%B %d')} basketball"
    ]
    
    # Open Graph tags for social media
    og_title = f"{away_team} vs {home_team}: Prediction & Betting Analysis"
    og_description = f"Our model predicts {favorite} covers. Full analysis, KenPom stats, and betting edge for {game_date.strftime('%B %d')}."
    
    # Create slug
    slug = f"{game_date.strftime('%Y-%m-%d')}-{slugify(away_team)}-vs-{slugify(home_team)}"
    
    return {
        'seo_title': seo_title,
        'meta_description': meta_description,
        'keywords': ', '.join(keywords),
        'og_title': og_title,
        'og_description': og_description,
        'canonical_url': f"https://btb-analytics.com/blog/{slug}",
        'slug': slug
    }


def convert_to_html(markdown_content):
    """Convert markdown to clean, SEO-optimized HTML for Squarespace with dark theme."""
    
    # Remove frontmatter
    lines = markdown_content.split('\n')
    if lines[0] == '---':
        try:
            end_idx = lines[1:].index('---') + 1
            markdown_content = '\n'.join(lines[end_idx+1:])
        except ValueError:
            pass
    
    html = markdown_content
    
    # Convert headers with proper semantic HTML
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Convert bold and emphasis
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)
    
    # Convert horizontal rules
    html = html.replace('---', '<hr>')
    
    # Convert lists
    lines = html.split('\n')
    in_list = False
    new_lines = []
    
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
    
    if in_list:
        new_lines.append('</ul>')
    
    html = '\n'.join(new_lines)
    
    # Convert paragraphs (but avoid breaking HTML tags)
    lines = html.split('\n')
    new_lines = []
    in_paragraph = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is HTML tag or empty
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
    
    if in_paragraph:
        new_lines.append('</p>')
    
    html = '\n'.join(new_lines)
    
    # Clean up extra spacing
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # Add CSS for dark theme with #23A354 green
    css = """
<style>
  .game-preview-container {
    max-width: 800px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #ffffff;
    background-color: transparent;
  }
  
  .betting-lines {
    text-align: center;
    margin: 20px 0;
    padding: 20px;
    background-color: #000000;
    border-radius: 8px;
    border: 2px solid #23A354;
  }
  
  .betting-lines h3 {
    margin-top: 0;
    color: #23A354;
    font-weight: bold;
  }
  
  .betting-lines p {
    font-size: 1.1em;
    margin: 10px 0;
    color: #ffffff;
  }
  
  table {
    width: 100%;
    margin: 20px 0;
    border-collapse: collapse;
  }
  
  td {
    text-align: center;
    vertical-align: middle;
    padding: 10px;
  }
  
  td img {
    width: 150px;
    height: 150px;
    object-fit: contain;
    display: block;
    margin: 0 auto;
  }
  
  td p {
    color: #ffffff;
  }
  
  h1 {
    color: #23A354;
    font-size: 2em;
    margin-bottom: 0.2em;
    font-weight: bold;
  }
  
  h2 {
    color: #23A354;
    font-size: 1.8em;
    margin-top: 1.5em;
    border-bottom: 2px solid #23A354;
    padding-bottom: 0.3em;
    font-weight: bold;
  }
  
  h3 {
    color: #23A354;
    font-size: 1.3em;
    margin-top: 1.2em;
    font-weight: bold;
  }
  
  ul {
    padding-left: 20px;
  }
  
  li {
    margin: 8px 0;
    color: #ffffff;
  }
  
  p {
    color: #ffffff;
  }
  
  strong {
    color: #23A354;
    font-weight: bold;
  }
  
  hr {
    border: none;
    border-top: 2px solid #23A354;
    margin: 30px 0;
  }
  
  a {
    color: #23A354;
    text-decoration: none;
  }
  
  a:hover {
    text-decoration: underline;
    color: #2bc46a;
  }
  
  @media (max-width: 768px) {
    h1 {
      font-size: 1.5em;
    }
    
    h2 {
      font-size: 1.3em;
    }
    
    td img {
      width: 100px;
      height: 100px;
    }
  }
</style>
"""
    
    # Wrap everything in a container
    full_html = f"""
{css}
<div class="game-preview-container">
{html}
</div>
"""
    
    return full_html


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
<div class="betting-lines">
  <h3>Betting Lines</h3>
  <p><strong>Spread:</strong> {spread_text}</p>
  <p><strong>Moneyline:</strong> {away_team} ({away_ml}) | {home_team} ({home_ml})</p>
  <p><strong>Total:</strong> {total}</p>
</div>
"""
        return betting_info
    except Exception as e:
        print(f"  Warning: Could not generate betting info: {e}")
        return ""


def generate_enhanced_narrative(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions):
    """Generate professional-style enhanced narrative content with betting insights."""
    
    try:
        # Extract key stats
        away_rank = int(away_stats.get('Rk', 999))
        home_rank = int(home_stats.get('Rk', 999))
        away_oe = float(away_stats.get('OE', 0))
        home_oe = float(home_stats.get('OE', 0))
        away_de = float(away_stats.get('DE', 0))
        home_de = float(home_stats.get('DE', 0))
        away_oe_rank = int(away_stats.get('RankOE', 999))
        home_oe_rank = int(home_stats.get('RankOE', 999))
        away_de_rank = int(away_stats.get('RankDE', 999))
        home_de_rank = int(home_stats.get('RankDE', 999))
        away_tempo = float(away_stats.get('Tempo', 0))
        home_tempo = float(home_stats.get('Tempo', 0))
        away_tempo_rank = int(away_stats.get('RankTempo', 999))
        home_tempo_rank = int(home_stats.get('RankTempo', 999))
        away_fg2_pct = float(away_stats.get('FG2Pct', 0))
        home_fg2_pct = float(home_stats.get('FG2Pct', 0))
        away_fg3_pct = float(away_stats.get('FG3Pct', 0))
        home_fg3_pct = float(home_stats.get('FG3Pct', 0))
        away_ft_rate = float(away_stats.get('FT_Rate', 0))
        home_ft_rate = float(home_stats.get('FT_Rate', 0))
        away_ft_pct = float(away_stats.get('FTPct', 0))
        home_ft_pct = float(home_stats.get('FTPct', 0))
        
        # Extract betting lines
        away_spread = float(away_predictions.get('market_spread', 0))
        home_spread = float(home_predictions.get('market_spread', 0))
        total = float(away_predictions.get('Opening Total', 0))
        
        # Determine favorite and underdog
        if away_spread < 0:
            favorite = away_team
            underdog = home_team
            spread_value = abs(away_spread)
            fav_stats = away_stats
            dog_stats = home_stats
        else:
            favorite = home_team
            underdog = away_team
            spread_value = abs(home_spread)
            fav_stats = home_stats
            dog_stats = away_stats
            
    except Exception as e:
        print(f"  Warning: Could not generate enhanced narrative: {e}")
        return ""
    
    narrative = "### Game Analysis & Betting Breakdown\n\n"
    
    # Opening scene-setting
    narrative += "#### Setting the Stage\n\n"
    rank_diff = abs(away_rank - home_rank)
    if rank_diff <= 15:
        narrative += f"When #{away_rank} {away_team} travels to face #{home_rank} {home_team}, we're looking at a matchup between two programs with similar profiles in the national landscape. "
    elif away_rank < home_rank:
        narrative += f"#{away_rank} {away_team} enters hostile territory as they take on #{home_rank} {home_team} in what the oddsmakers see as a significant talent gap. "
    else:
        narrative += f"#{home_rank} {home_team} hosts #{away_rank} {away_team} in a game where the home team finds itself as the underdog in their own building. "
    
    narrative += f"The early betting action has shaped into {favorite} favored by {spread_value:.1f} points, with the total sitting at {total:.1f}. "
    narrative += "These numbers tell us a story, but let's dig deeper into what's really happening on the court.\n\n"
    
    # Spread discussion
    narrative += "#### Breaking Down the Spread\n\n"
    if spread_value < 3:
        narrative += f"A spread under a field goal suggests the books see this as essentially a coin flip. {favorite}'s {spread_value:.1f}-point cushion reflects home court advantage more than a talent disparity. "
    elif spread_value < 7:
        narrative += f"The {spread_value:.1f}-point spread indicates {favorite} is viewed as the better team, but this isn't an overwhelming edge. {underdog} has a legitimate path to covering or winning outright with a solid performance. "
    elif spread_value < 12:
        narrative += f"A spread around {spread_value:.1f} points tells us {favorite} has clear advantages, but games aren't played on paper. {underdog} needs to punch above their weight class to keep this competitive. "
    else:
        narrative += f"The {spread_value:.1f}-point spread screams mismatch. The books are asking {underdog} to hang within two possessions, which based on the profiles, requires {favorite} to play below their standard. "
    
    narrative += f"The total of {total:.1f} "
    if total < 135:
        narrative += "suggests a defensive slugfest or slower tempo that limits possessions. "
    elif total < 150:
        narrative += "sits right around league average, indicating a standard pace without extreme scoring expectations either way. "
    else:
        narrative += "points to a track meet. The books are anticipating fireworks with both teams getting their shots up. "
    narrative += "\n\n"
    
    # Deep offensive breakdown
    narrative += "#### Offensive Firepower\n\n"
    narrative += f"**{away_team}** brings an offensive efficiency of {away_oe:.2f} (ranked #{away_oe_rank} nationally). "
    if away_oe_rank < 50:
        narrative += "This is an elite offense that can score in multiple ways. "
    elif away_oe_rank < 150:
        narrative += "They're solid offensively, capable of putting up points but not overwhelming. "
    else:
        narrative += "Scoring has been a struggle, and they'll need their best offensive showing to hit their number. "
    
    if away_fg3_pct > 36:
        narrative += f"The three-ball has been a weapon, connecting at {away_fg3_pct:.1f}% from deep. They'll look to stretch the floor and create driving lanes through that perimeter threat. "
    elif away_fg3_pct < 32:
        narrative += f"At {away_fg3_pct:.1f}% from three, they can't rely on the arc. Expect a paint-focused attack. "
    else:
        narrative += f"Their {away_fg3_pct:.1f}% three-point shooting is serviceable but won't scare anyone. "
    
    narrative += f"\n\nMeanwhile, **{home_team}** counters with {home_oe:.2f} offensive efficiency (#{home_oe_rank}). "
    if home_oe_rank < 50:
        narrative += "This offense can match anyone bucket-for-bucket. "
    elif home_oe_rank < 150:
        narrative += "They're competent on offense without being spectacular. "
    else:
        narrative += "Points have been hard to come by, making every possession critical. "
    
    if home_fg3_pct > 36:
        narrative += f"They're lethal from beyond the arc at {home_fg3_pct:.1f}%, giving them spacing and shot creation. "
    elif home_fg3_pct < 32:
        narrative += f"The three-point shot hasn't fallen this year at {home_fg3_pct:.1f}%, forcing them to grind in the half court. "
    else:
        narrative += f"At {home_fg3_pct:.1f}% from three, they have adequate spacing but must pick their spots. "
    narrative += "\n\n"
    
    # Tempo and style
    narrative += "#### Tempo & Playing Style\n\n"
    tempo_diff = abs(away_tempo - home_tempo)
    avg_tempo = (away_tempo + home_tempo) / 2
    
    narrative += f"{away_team} operates at a {away_tempo:.1f} tempo (#{away_tempo_rank}), while {home_team} plays at {home_tempo:.1f} (#{home_tempo_rank}). "
    
    if tempo_diff > 5:
        if away_tempo > home_tempo:
            narrative += f"{away_team} wants to run, but {home_team} prefers to slow things down. "
        else:
            narrative += f"{home_team} likes to push the pace, while {away_team} wants to control the clock. "
        narrative += "This tempo battle will be crucial—whoever dictates pace gains a significant edge. "
    else:
        narrative += "Both teams operate at similar speeds, so we shouldn't see much of a tempo conflict. "
    
    if avg_tempo > 72:
        narrative += f"With an average tempo around {avg_tempo:.1f}, expect plenty of possessions and transition opportunities. "
    elif avg_tempo < 68:
        narrative += f"The slower pace (averaging {avg_tempo:.1f}) means fewer possessions, making each one more valuable. "
    else:
        narrative += f"The moderate pace (around {avg_tempo:.1f}) should create a standard flow. "
    narrative += "\n\n"
    
    # Interior game
    narrative += "#### The Interior Battle\n\n"
    narrative += f"Inside the paint, {away_team} shoots {away_fg2_pct:.1f}% on two-pointers, while {home_team} converts at {home_fg2_pct:.1f}%. "
    
    if abs(away_fg2_pct - home_fg2_pct) > 5:
        better_interior = away_team if away_fg2_pct > home_fg2_pct else home_team
        narrative += f"{better_interior} has a clear edge in interior scoring efficiency. "
    else:
        narrative += "Both teams are evenly matched in paint efficiency. "
    
    narrative += f"\n\nGetting to the line matters too. {away_team}'s free throw rate sits at {away_ft_rate:.1f}, "
    if away_ft_rate > 35:
        narrative += "indicating they're aggressive attacking the rim and drawing contact. "
    else:
        narrative += "suggesting they're more perimeter-oriented or struggle to draw fouls. "
    
    narrative += f"{home_team} checks in at {home_ft_rate:.1f}, "
    if home_ft_rate > 35:
        narrative += "showing they also get to the stripe frequently. "
    else:
        narrative += "meaning they don't manufacture easy points at the line. "
    
    narrative += f"When they do get fouled, {away_team} converts {away_ft_pct:.1f}% while {home_team} hits {home_ft_pct:.1f}%. "
    if abs(away_ft_pct - home_ft_pct) > 5:
        if away_ft_pct > home_ft_pct:
            narrative += f"{away_team}'s superior free throw shooting could be the difference in a tight game. "
        else:
            narrative += f"{home_team}'s edge at the charity stripe matters in close finishes. "
    else:
        narrative += "Both teams are comparable from the stripe. "
    narrative += "\n\n"
    
    # X-factors
    narrative += "#### X-Factors & Intangibles\n\n"
    narrative += f"Playing at home, {home_team} gets the crowd advantage and familiar surroundings. "
    if home_rank < away_rank - 20:
        narrative += f"But despite the friendly confines, they're significant underdogs for a reason—{away_team} is simply the superior team on paper. "
    elif home_rank > away_rank + 20:
        narrative += f"Combined with their ranking advantage, this home court could create an intimidating environment for {away_team}. "
    else:
        narrative += "In a fairly even matchup, home court becomes magnified as a potential deciding factor. "
    
    narrative += "\n\nDefensively, "
    if away_de_rank < home_de_rank - 50:
        narrative += f"{away_team} (#{away_de_rank} defensive efficiency) should have success against {home_team}'s weaker defense (#{home_de_rank}). "
    elif home_de_rank < away_de_rank - 50:
        narrative += f"{home_team} (#{home_de_rank} defensive efficiency) will look to clamp down on {away_team} (#{away_de_rank} defensively). "
    else:
        narrative += f"both teams rank similarly on the defensive end (#{away_de_rank} and #{home_de_rank}), so offense may determine the outcome. "
    narrative += "\n\n"
    
    # Betting angles
    narrative += "#### The Betting Angle\n\n"
    
    # Spread value discussion
    if spread_value < 5:
        narrative += f"Small spreads like {spread_value:.1f} create interesting dynamics. "
        narrative += f"I'm looking at whether {favorite} can actually separate, or if this stays inside one possession. "
    elif spread_value < 10:
        narrative += f"The {spread_value:.1f}-point spread asks: can {underdog} keep it within striking distance? "
    else:
        narrative += f"With {spread_value:.1f} points to work with, {underdog} doesn't need to win—just stay competitive. "
    
    # Provide actual betting insight
    if away_oe_rank < 50 and home_de_rank > 200:
        narrative += f"The matchup favors {away_team}'s offense against a porous defense. "
        if away_team == favorite:
            narrative += "Laying the points makes sense. "
        else:
            narrative += "The underdog has an offensive path to covering. "
    elif home_oe_rank < 50 and away_de_rank > 200:
        narrative += f"The matchup favors {home_team}'s offense against a weak defense. "
        if home_team == favorite:
            narrative += "The favorite should be able to flex here. "
        else:
            narrative += "Don't sleep on the home dog with that offensive capability. "
    
    # Total discussion
    narrative += f"\n\nRegarding the total of {total:.1f}: "
    combined_oe = away_oe + home_oe
    combined_de = away_de + home_de
    
    if combined_oe > 240 and avg_tempo > 70:
        narrative += "Two offenses that can score, playing at pace? I lean over. "
    elif combined_de < 195 and avg_tempo < 68:
        narrative += "Elite defenses playing slower? Under has my attention. "
    elif total > 150 and combined_oe < 230:
        narrative += "The number seems inflated relative to the offensive profiles. Under could be the move. "
    elif total < 135 and combined_oe > 235:
        narrative += "This total feels low given the offensive firepower. Over has value. "
    else:
        narrative += "The total seems fairly priced. I'd need to see where sharp money moves it. "
    
    narrative += "\n\nThe sharp play isn't always obvious. Watch for line movement, injury reports, and whether the public is hammering one side. That's where the value emerges.\n\n"
    
    return narrative


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
## {team_name}

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
    
    # Add enhanced narrative with betting insights
    post += "\n" + generate_enhanced_narrative(away_team, home_team, away_stats, home_stats, away_predictions, home_predictions)
    
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
    
    # Create directories
    os.makedirs('_posts', exist_ok=True)
    os.makedirs('_html', exist_ok=True)
    os.makedirs('_seo', exist_ok=True)
    
    print("\n" + "="*60)
    print("Created directories:")
    print(f"  _posts/: {os.path.exists('_posts')}")
    print(f"  _html/: {os.path.exists('_html')}")
    print(f"  _seo/: {os.path.exists('_seo')}")
    print("="*60 + "\n")
    
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
        
        # Generate post content (markdown)
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
        filename = f"{game_date.strftime('%Y-%m-%d')}-{away_slug}-vs-{home_slug}"
        
        # Save markdown version
        md_filepath = os.path.join('_posts', f"{filename}.md")
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(post_content)
        print(f"  ✓ Created Markdown: {md_filepath}")
        
        # Convert to HTML and save
        html_content = convert_to_html(post_content)
        
        html_filepath = os.path.join('_html', f"{filename}.html")
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  ✓ Created HTML: {html_filepath}")
        
        # Generate and save SEO metadata
        seo_data = generate_seo_metadata(away_team, home_team, game_date, away_predictions, home_predictions)
        
        seo_filepath = os.path.join('_seo', f"{filename}-seo.txt")
        with open(seo_filepath, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write(f"SEO METADATA FOR: {away_team} vs {home_team}\n")
            f.write("="*60 + "\n\n")
            f.write(f"BLOG POST TITLE:\n{seo_data['seo_title']}\n\n")
            f.write(f"META DESCRIPTION (copy this into Squarespace):\n{seo_data['meta_description']}\n\n")
            f.write(f"URL SLUG (copy this into Squarespace):\n{seo_data['slug']}\n\n")
            f.write(f"KEYWORDS:\n{seo_data['keywords']}\n\n")
            f.write(f"OPEN GRAPH TITLE (for social media):\n{seo_data['og_title']}\n\n")
            f.write(f"OPEN GRAPH DESCRIPTION:\n{seo_data['og_description']}\n\n")
            f.write(f"CANONICAL URL:\n{seo_data['canonical_url']}\n\n")
            f.write("="*60 + "\n")
        print(f"  ✓ Created SEO file: {seo_filepath}")
        
        # Verify files were created
        if not os.path.exists(html_filepath):
            print(f"  ⚠ WARNING: HTML file was not created!")
        if not os.path.exists(seo_filepath):
            print(f"  ⚠ WARNING: SEO file was not created!")
        
        posts_created += 1
    
    print(f"\n{'='*60}")
    print(f"Generation complete! Created {posts_created} preview posts.")
    print(f"Files created in:")
    print(f"  - _posts/ ({len(os.listdir('_posts'))} files)")
    print(f"  - _html/ ({len(os.listdir('_html'))} files)")
    print(f"  - _seo/ ({len(os.listdir('_seo'))} files)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

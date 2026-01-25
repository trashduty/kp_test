import pandas as pd
import os
import re
from datetime import datetime, timedelta

# GitHub raw content base URLs
CBB_REPO_BASE = "https://raw.githubusercontent.com/trashduty/cbb/main/"
KP_TEST_REPO_BASE = "https://raw.githubusercontent.com/trashduty/kp_test/main/"

# Template with placeholders in format: ["column_name", file_name]
MATCHUP_TEMPLATE = """---
title: "Away Team vs Home Team Preview & Prediction"
date: {game_date}
categories: [NCAA Basketball, Game Previews]
tags: [Away Team, Home Team, KenPom, Predictions]
excerpt: "Expert analysis and prediction for Away Team vs Home Team. Get the latest stats, trends, and betting insights."
---

## Away Team @ Home Team

**Game Date:** {game_date}

### Game Overview

The Away Team (["Rk", kenpom_stats]) will travel to face the Home Team (["Rk", kenpom_stats]) in what promises to be an exciting matchup. Both teams bring unique strengths to the court, and our analysis breaks down the key factors that will determine the outcome.

---

### Away Team Analysis

**Record & Ranking:**
- **KenPom Rank:** #["Rk", kenpom_stats]
- **Adjusted Efficiency Margin:** ["OE", kenpom_stats] (Rank: #["RankOE", kenpom_stats])

**Offensive Profile:**
Offensively, the four-factor profile suggests a team that relies on efficient shooting (["eFG_Pct", kenpom_stats]%, #["RankeFG_Pct", kenpom_stats]), ball security (["TO_Pct", kenpom_stats]% turnover rate, #["RankTO_Pct", kenpom_stats]), offensive rebounding (["OR_Pct", kenpom_stats]%, #["RankOR_Pct", kenpom_stats]), and getting to the line (["FT_Rate", kenpom_stats] FT Rate, #["RankFT_Rate", kenpom_stats]).

The team's offensive efficiency ranks #["RankOE", kenpom_stats] nationally at ["OE", kenpom_stats] points per 100 possessions. They play at an adjusted tempo of ["Tempo", kenpom_stats] possessions per game (Rank: #["RankTempo", kenpom_stats]).

**Shooting Breakdown:**
- Three-point shooting: ["FG3Pct", kenpom_stats]% (Rank: #["RankFG3Pct", kenpom_stats])
- Two-point shooting: ["FG2Pct", kenpom_stats]% (Rank: #["RankFG2Pct", kenpom_stats])
- Free throw percentage: ["FTPct", kenpom_stats]% (Rank: #["RankFTPct", kenpom_stats])
- Three-point rate: ["F3GRate", kenpom_stats]% (Rank: #["RankF3GRate", kenpom_stats])

**Defensive Profile:**
Defensively, Away Team ranks #["RankDE", kenpom_stats] with a defensive efficiency of ["DE", kenpom_stats]. They force opponents into:
- Opponent eFG%: ["DeFG_Pct", kenpom_stats]% (Rank: #["RankDeFG_Pct", kenpom_stats])
- Opponent turnover rate: ["DTO_Pct", kenpom_stats]% (Rank: #["RankDTO_Pct", kenpom_stats])
- Defensive rebounding: ["DOR_Pct", kenpom_stats]% (Rank: #["RankDOR_Pct", kenpom_stats])
- Opponent free throw rate: ["DFT_Rate", kenpom_stats] (Rank: #["RankDFT_Rate", kenpom_stats])

**Advanced Metrics:**
- Block percentage: ["BlockPct", kenpom_stats]% (Rank: #["RankBlockPct", kenpom_stats])
- Steal rate: ["StlRate", kenpom_stats] (Rank: #["RankStlRate", kenpom_stats])
- Assist rate: ["ARate", kenpom_stats]% (Rank: #["RankARate", kenpom_stats])

**Team Composition:**
- Average height: ["AvgHgt", kenpom_stats]" (Rank: #["AvgHgtRank", kenpom_stats])
- Effective height: ["HgtEff", kenpom_stats] (Rank: #["HgtEffRank", kenpom_stats])
- Experience: ["Exp", kenpom_stats] (Rank: #["ExpRank", kenpom_stats])
- Bench strength: ["Bench", kenpom_stats] (Rank: #["BenchRank", kenpom_stats])
- Continuity: ["Continuity", kenpom_stats] (Rank: #["RankContinuity", kenpom_stats])

---

### Home Team Analysis

**Record & Ranking:**
- **KenPom Rank:** #["Rk", kenpom_stats]
- **Adjusted Efficiency Margin:** ["OE", kenpom_stats] (Rank: #["RankOE", kenpom_stats])

**Offensive Profile:**
Offensively, the four-factor profile suggests a team that relies on efficient shooting (["eFG_Pct", kenpom_stats]%, #["RankeFG_Pct", kenpom_stats]), ball security (["TO_Pct", kenpom_stats]% turnover rate, #["RankTO_Pct", kenpom_stats]), offensive rebounding (["OR_Pct", kenpom_stats]%, #["RankOR_Pct", kenpom_stats]), and getting to the line (["FT_Rate", kenpom_stats] FT Rate, #["RankFT_Rate", kenpom_stats]).

The team's offensive efficiency ranks #["RankOE", kenpom_stats] nationally at ["OE", kenpom_stats] points per 100 possessions. They play at an adjusted tempo of ["Tempo", kenpom_stats] possessions per game (Rank: #["RankTempo", kenpom_stats]).

**Shooting Breakdown:**
- Three-point shooting: ["FG3Pct", kenpom_stats]% (Rank: #["RankFG3Pct", kenpom_stats])
- Two-point shooting: ["FG2Pct", kenpom_stats]% (Rank: #["RankFG2Pct", kenpom_stats])
- Free throw percentage: ["FTPct", kenpom_stats]% (Rank: #["RankFTPct", kenpom_stats])
- Three-point rate: ["F3GRate", kenpom_stats]% (Rank: #["RankF3GRate", kenpom_stats])

**Defensive Profile:**
Defensively, Home Team ranks #["RankDE", kenpom_stats] with a defensive efficiency of ["DE", kenpom_stats]. They force opponents into:
- Opponent eFG%: ["DeFG_Pct", kenpom_stats]% (Rank: #["RankDeFG_Pct", kenpom_stats])
- Opponent turnover rate: ["DTO_Pct", kenpom_stats]% (Rank: #["RankDTO_Pct", kenpom_stats])
- Defensive rebounding: ["DOR_Pct", kenpom_stats]% (Rank: #["RankDOR_Pct", kenpom_stats])
- Opponent free throw rate: ["DFT_Rate", kenpom_stats] (Rank: #["RankDFT_Rate", kenpom_stats])

**Advanced Metrics:**
- Block percentage: ["BlockPct", kenpom_stats]% (Rank: #["RankBlockPct", kenpom_stats])
- Steal rate: ["StlRate", kenpom_stats] (Rank: #["RankStlRate", kenpom_stats])
- Assist rate: ["ARate", kenpom_stats]% (Rank: #["RankARate", kenpom_stats])

**Team Composition:**
- Average height: ["AvgHgt", kenpom_stats]" (Rank: #["AvgHgtRank", kenpom_stats])
- Effective height: ["HgtEff", kenpom_stats] (Rank: #["HgtEffRank", kenpom_stats])
- Experience: ["Exp", kenpom_stats] (Rank: #["ExpRank", kenpom_stats])
- Bench strength: ["Bench", kenpom_stats] (Rank: #["BenchRank", kenpom_stats])
- Continuity: ["Continuity", kenpom_stats] (Rank: #["RankContinuity", kenpom_stats])

---

### Prediction & Model Lean

Our model predicts **{predicted_winner}** will win this matchup.

**Win Probabilities:**
- Away Team: {away_win_prob}%
- Home Team: {home_win_prob}%

---

### Key Matchup Factors

**Tempo Battle:**
Away Team plays at a tempo of ["Tempo", kenpom_stats] possessions per game (Rank #["RankTempo", kenpom_stats]), while Home Team operates at ["Tempo", kenpom_stats] (Rank #["RankTempo", kenpom_stats]). The team that can impose their preferred pace will have a significant advantage.

**Offensive Efficiency:**
Away Team ranks #["RankOE", kenpom_stats] in adjusted offensive efficiency (["OE", kenpom_stats]), compared to Home Team's #["RankOE", kenpom_stats] ranking (["OE", kenpom_stats]).

**Defensive Matchup:**
Defensively, Away Team ranks #["RankDE", kenpom_stats] (["DE", kenpom_stats]), while Home Team ranks #["RankDE", kenpom_stats] (["DE", kenpom_stats]).

**Three-Point Shooting:**
Away Team shoots ["FG3Pct", kenpom_stats]% from beyond the arc and attempts threes at a rate of ["F3GRate", kenpom_stats]%. Home Team counters with ["FG3Pct", kenpom_stats]% shooting and a ["F3GRate", kenpom_stats]% three-point rate.

**Rebounding:**
Away Team grabs offensive rebounds at a ["OR_Pct", kenpom_stats]% rate, while Home Team secures ["DOR_Pct", kenpom_stats]% of available defensive rebounds.

**Ball Security:**
Away Team turns the ball over on ["TO_Pct", kenpom_stats]% of possessions, while Home Team's defense forces turnovers at a ["DTO_Pct", kenpom_stats]% rate.

---

*This preview is generated using advanced statistical models and KenPom efficiency ratings. Check back for updated analysis as game time approaches.*
"""


def load_data_from_github():
    """Load all necessary data files from GitHub repositories"""
    try:
        # Load matchups from cbb repo
        kp_df = pd.read_csv(f"{CBB_REPO_BASE}kp.csv")
        
        # Load predictions from cbb repo
        predictions_df = pd.read_csv(f"{CBB_REPO_BASE}CBB_Output.csv")
        
        # Load KenPom stats from kp_test repo
        kenpom_stats_df = pd.read_csv(f"{KP_TEST_REPO_BASE}kenpom_stats.csv")
        
        return kp_df, predictions_df, kenpom_stats_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None, None


def get_tomorrows_games(kp_df):
    """Filter games for tomorrow's date and determine away/home teams using 'side' column"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Filter for tomorrow's games
    tomorrow_games = kp_df[kp_df['date'] == tomorrow].copy()
    
    if tomorrow_games.empty:
        return []
    
    # Reconstruct matchups from the two-row format
    games = []
    processed_pairs = set()
    
    for idx, row in tomorrow_games.iterrows():
        team = row['team']
        opponent = row['opponent']
        
        # Create a sorted tuple to avoid duplicates
        pair = tuple(sorted([team, opponent]))
        
        if pair not in processed_pairs:
            processed_pairs.add(pair)
            
            # Find both rows for this matchup
            team_row = tomorrow_games[
                (tomorrow_games['team'] == team) & 
                (tomorrow_games['opponent'] == opponent)
            ].iloc[0]
            
            opp_row = tomorrow_games[
                (tomorrow_games['team'] == opponent) & 
                (tomorrow_games['opponent'] == team)
            ].iloc[0]
            
            # Determine home and away using 'side' column
            if team_row['side'] == 'away':
                away_team = team
                home_team = opponent
                away_data = team_row
                home_data = opp_row
            else:
                away_team = opponent
                home_team = team
                away_data = opp_row
                home_data = team_row
            
            game = {
                'date': row['date'],
                'away_team': away_team,
                'home_team': home_team,
                'away_win_prob': away_data['win_prob'],
                'home_win_prob': home_data['win_prob'],
            }
            
            games.append(game)
    
    return games


def get_column_value(df, team_name, column_name, file_name):
    """Get a column value for a team from the specified dataframe"""
    # Find team name column
    team_col = None
    possible_cols = ['Team', 'team', 'TeamName', 'team_name']
    for col in possible_cols:
        if col in df.columns:
            team_col = col
            break
    
    if team_col is None:
        return 'N/A'
    
    # Find the team row
    team_data = df[df[team_col] == team_name]
    
    if team_data.empty:
        return 'N/A'
    
    # Get the column value
    if column_name not in df.columns:
        return 'N/A'
    
    value = team_data[column_name].values[0]
    
    # Handle NaN values
    if pd.isna(value):
        return 'N/A'
    
    # Format numeric values
    if isinstance(value, (int, float)):
        # Check if it's a percentage or rate that needs decimal formatting
        if 'Pct' in column_name or 'Rate' in column_name:
            return f"{value:.1f}"
        # Check if it's a ranking (should be integer)
        elif 'Rank' in column_name or column_name == 'Rk':
            return str(int(value))
        # Check if it's wins/losses (should be integer)
        elif column_name in ['Wins', 'Losses']:
            return str(int(value))
        else:
            return f"{value:.2f}"
    
    return str(value)


def parse_and_replace_placeholders(template, away_team, home_team, kenpom_stats_df, predictions_df):
    """Parse template and replace all placeholders with actual data"""
    content = template
    
    # Split content into sections
    parts = content.split('###')
    processed_parts = []
    
    for i, part in enumerate(parts):
        if i == 0:
            # Header section before any ###
            part = part.replace('Away Team', away_team)
            part = part.replace('Home Team', home_team)
            processed_parts.append(part)
        elif 'Away Team Analysis' in part:
            # Process away team section
            part = replace_placeholders_for_team(
                part, away_team, kenpom_stats_df, predictions_df, 
                r'\["([^"]+)",\s*([^\]]+)\]'
            )
            part = part.replace('Away Team', away_team)
            processed_parts.append('###' + part)
        elif 'Home Team Analysis' in part:
            # Process home team section
            part = replace_placeholders_for_team(
                part, home_team, kenpom_stats_df, predictions_df,
                r'\["([^"]+)",\s*([^\]]+)\]'
            )
            part = part.replace('Home Team', home_team)
            processed_parts.append('###' + part)
        elif 'Key Matchup Factors' in part:
            # Process comparison section with both teams
            part = replace_comparison_section(
                part, away_team, home_team, kenpom_stats_df, predictions_df
            )
            processed_parts.append('###' + part)
        else:
            # Other sections - replace team names but not placeholders yet
            part = part.replace('Away Team', away_team)
            part = part.replace('Home Team', home_team)
            # Replace any remaining placeholders with away team data (for prediction section)
            part = replace_placeholders_for_team(
                part, away_team, kenpom_stats_df, predictions_df,
                r'\["([^"]+)",\s*([^\]]+)\]'
            )
            processed_parts.append('###' + part)
    
    content = ''.join(processed_parts)
    return content


def replace_comparison_section(text, away_team, home_team, kenpom_stats_df, predictions_df):
    """Replace placeholders in comparison sections where both teams are mentioned"""
    # Split by sentences that contain both "Away Team" and "Home Team"
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        if 'Away Team' in line and 'Home Team' in line:
            # This line compares both teams
            # Handle different separator patterns
            if ' while ' in line:
                parts = line.split(' while ')
                parts[0] = replace_placeholders_for_team(
                    parts[0], away_team, kenpom_stats_df, predictions_df,
                    r'\["([^"]+)",\s*([^\]]+)\]'
                )
                parts[0] = parts[0].replace('Away Team', away_team)
                
                parts[1] = replace_placeholders_for_team(
                    parts[1], home_team, kenpom_stats_df, predictions_df,
                    r'\["([^"]+)",\s*([^\]]+)\]'
                )
                parts[1] = parts[1].replace('Home Team', home_team)
                
                line = ' while '.join(parts)
            elif 'compared to' in line or ', compared to' in line:
                parts = re.split(r',?\s*compared to\s*', line)
                if len(parts) >= 2:
                    parts[0] = replace_placeholders_for_team(
                        parts[0], away_team, kenpom_stats_df, predictions_df,
                        r'\["([^"]+)",\s*([^\]]+)\]'
                    )
                    parts[0] = parts[0].replace('Away Team', away_team)
                    
                    parts[1] = replace_placeholders_for_team(
                        parts[1], home_team, kenpom_stats_df, predictions_df,
                        r'\["([^"]+)",\s*([^\]]+)\]'
                    )
                    parts[1] = parts[1].replace('Home Team', home_team)
                    
                    line = ', compared to '.join(parts)
            else:
                # Handle cases where sentence has both teams separated by period or other markers
                # Split by ". Home Team" or similar patterns
                if '. Home Team' in line or ', Home Team' in line:
                    # Find the split point
                    split_markers = ['. Home Team', ', Home Team']
                    for marker in split_markers:
                        if marker in line:
                            parts = line.split(marker)
                            # First part is about away team
                            parts[0] = replace_placeholders_for_team(
                                parts[0], away_team, kenpom_stats_df, predictions_df,
                                r'\["([^"]+)",\s*([^\]]+)\]'
                            )
                            parts[0] = parts[0].replace('Away Team', away_team)
                            
                            # Second part is about home team (add marker back)
                            parts[1] = marker[1:] + ' ' + parts[1]  # Add back without the period/comma
                            parts[1] = replace_placeholders_for_team(
                                parts[1], home_team, kenpom_stats_df, predictions_df,
                                r'\["([^"]+)",\s*([^\]]+)\]'
                            )
                            parts[1] = parts[1].replace('Home Team', home_team)
                            
                            line = marker[0] + parts[1] if marker[0] in '.,;' else parts[1]
                            line = parts[0] + marker[0] + ' ' + parts[1]
                            break
                else:
                    # Default: process sequentially (may not work perfectly)
                    # Split into away and home mentions
                    import copy
                    # Process each placeholder individually based on surrounding context
                    pattern = r'\["([^"]+)",\s*([^\]]+)\]'
                    matches = list(re.finditer(pattern, line))
                    
                    # Find index of "Home Team" in line
                    home_idx = line.find('Home Team')
                    
                    # Replace placeholders before "Home Team" with away team data
                    for match in reversed(matches):
                        if match.start() < home_idx:
                            value = get_column_value(kenpom_stats_df, away_team, match.group(1), match.group(2).strip())
                            line = line[:match.start()] + value + line[match.end():]
                    
                    # Now replace placeholders after "Home Team" with home team data
                    matches = list(re.finditer(pattern, line))
                    for match in reversed(matches):
                        value = get_column_value(kenpom_stats_df, home_team, match.group(1), match.group(2).strip())
                        line = line[:match.start()] + value + line[match.end():]
                    
                    line = line.replace('Away Team', away_team)
                    line = line.replace('Home Team', home_team)
        elif 'Away Team' in line:
            # Only away team
            line = replace_placeholders_for_team(
                line, away_team, kenpom_stats_df, predictions_df,
                r'\["([^"]+)",\s*([^\]]+)\]'
            )
            line = line.replace('Away Team', away_team)
        elif 'Home Team' in line:
            # Only home team
            line = replace_placeholders_for_team(
                line, home_team, kenpom_stats_df, predictions_df,
                r'\["([^"]+)",\s*([^\]]+)\]'
            )
            line = line.replace('Home Team', home_team)
        
        processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def replace_placeholders_for_team(text, team_name, kenpom_stats_df, predictions_df, pattern):
    """Replace all placeholders in text for a specific team"""
    file_mapping = {
        'kenpom_stats': kenpom_stats_df,
        'cbb_output': predictions_df
    }
    
    def replace_match(match):
        column_name = match.group(1)
        file_name = match.group(2).strip()
        
        if file_name in file_mapping:
            df = file_mapping[file_name]
            value = get_column_value(df, team_name, column_name, file_name)
            return value
        return 'N/A'
    
    return re.sub(pattern, replace_match, text)


def get_prediction_winner(away_team, home_team, predictions_df, game):
    """Determine the predicted winner and related stats"""
    # Find team name column
    team_col = None
    for col in ['Team', 'team', 'TeamName', 'team_name']:
        if col in predictions_df.columns:
            team_col = col
            break
    
    if team_col is None:
        # Fallback to win probability
        if game['away_win_prob'] > game['home_win_prob']:
            return away_team
        return home_team
    
    # Get predictions for both teams
    away_pred = predictions_df[predictions_df[team_col] == away_team]
    home_pred = predictions_df[predictions_df[team_col] == home_team]
    
    if not away_pred.empty and not home_pred.empty:
        # Use Moneyline Win Probability to determine winner
        if 'Moneyline Win Probability' in predictions_df.columns:
            away_prob = away_pred['Moneyline Win Probability'].values[0]
            home_prob = home_pred['Moneyline Win Probability'].values[0]
            
            if pd.notna(away_prob) and pd.notna(home_prob):
                if away_prob > home_prob:
                    return away_team
                return home_team
    
    # Fallback to kp.csv win probability
    if game['away_win_prob'] > game['home_win_prob']:
        return away_team
    return home_team


def generate_preview_content(away_team, home_team, game_date, kenpom_stats_df, predictions_df, game):
    """Generate the game preview content using template parsing"""
    
    # Get predicted winner
    predicted_winner = get_prediction_winner(away_team, home_team, predictions_df, game)
    
    # Start with template
    content = MATCHUP_TEMPLATE
    
    # Replace date placeholders
    content = content.replace('{game_date}', game_date)
    
    # Replace prediction placeholders
    content = content.replace('{predicted_winner}', predicted_winner)
    content = content.replace('{away_win_prob}', f"{game['away_win_prob']:.1f}")
    content = content.replace('{home_win_prob}', f"{game['home_win_prob']:.1f}")
    
    # Parse and replace all ["column", file] placeholders
    content = parse_and_replace_placeholders(
        content, away_team, home_team, kenpom_stats_df, predictions_df
    )
    
    # Format team names for URL slug
    slug = f"{away_team.lower().replace(' ', '-')}-vs-{home_team.lower().replace(' ', '-')}"
    
    return content, slug


def save_preview(content, slug, game_date):
    """Save the preview to the _posts directory"""
    posts_dir = "_posts"
    os.makedirs(posts_dir, exist_ok=True)
    
    filename = f"{posts_dir}/{game_date}-{slug}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Generated preview: {filename}")


def main():
    """Main function to generate all game previews"""
    print("Loading data from GitHub repositories...")
    kp_df, predictions_df, kenpom_stats_df = load_data_from_github()
    
    if kp_df is None or predictions_df is None or kenpom_stats_df is None:
        print("Failed to load required data files.")
        return
    
    print("Getting tomorrow's games...")
    tomorrow_games = get_tomorrows_games(kp_df)
    
    if not tomorrow_games:
        print("No games scheduled for tomorrow.")
        return
    
    print(f"Found {len(tomorrow_games)} games for tomorrow.\n")
    
    for game in tomorrow_games:
        away_team = game['away_team']
        home_team = game['home_team']
        game_date = game['date']
        
        print(f"Generating preview for: {away_team} @ {home_team}")
        
        # Generate preview content
        content, slug = generate_preview_content(
            away_team, home_team, game_date, 
            kenpom_stats_df, predictions_df, game
        )
        
        # Save preview
        save_preview(content, slug, game_date)
        print()  # Empty line for readability
    
    print("✅ All previews generated successfully!")


if __name__ == "__main__":
    main()

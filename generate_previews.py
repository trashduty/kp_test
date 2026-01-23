import pandas as pd
import os
from datetime import datetime, timedelta
import requests

# GitHub raw content base URLs
CBB_REPO_BASE = "https://raw.githubusercontent.com/trashduty/cbb/main/"
KP_TEST_REPO_BASE = "https://raw.githubusercontent.com/trashduty/kp_test/main/"

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
    """Filter games for tomorrow's date"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Filter for tomorrow's games
    # Assuming date column could be 'Date', 'date', or similar
    date_col = None
    for col in kp_df.columns:
        if col.lower() in ['date', 'gamedate', 'game_date']:
            date_col = col
            break
    
    if date_col is None:
        print(f"Could not find date column. Available columns: {kp_df.columns.tolist()}")
        return pd.DataFrame()
    
    tomorrow_games = kp_df[kp_df[date_col] == tomorrow].copy()
    
    return tomorrow_games

def get_team_stats(team_name, kenpom_stats_df):
    """Extract all relevant KenPom stats for a team"""
    # Find team name column
    team_col = None
    for col in kenpom_stats_df.columns:
        if col.lower() in ['teamname', 'team_name', 'team']:
            team_col = col
            break
    
    if team_col is None:
        print(f"Could not find team name column. Available columns: {kenpom_stats_df.columns.tolist()}")
        return None
    
    team_data = kenpom_stats_df[kenpom_stats_df[team_col] == team_name]
    
    if team_data.empty:
        print(f"  ⚠️  No stats found for team: {team_name}")
        return None
    
    # Helper function to safely get column value
    def safe_get(col_name, default='N/A'):
        if col_name in team_data.columns:
            val = team_data[col_name].values[0]
            # Format numbers nicely
            if isinstance(val, (int, float)) and val != val:  # Check for NaN
                return default
            if isinstance(val, float):
                return round(val, 1)
            return val
        return default
    
    # Extract stats based on KenPom API documentation
    stats = {
        # Ratings endpoint fields
        'rank': safe_get('RankAdjEM'),
        'adj_em': safe_get('AdjEM'),
        'adj_oe': safe_get('AdjOE'),
        'adj_oe_rank': safe_get('RankAdjOE'),
        'adj_de': safe_get('AdjDE'),
        'adj_de_rank': safe_get('RankAdjDE'),
        'adj_tempo': safe_get('AdjTempo'),
        'adj_tempo_rank': safe_get('RankAdjTempo'),
        'wins': safe_get('Wins', 0),
        'losses': safe_get('Losses', 0),
        'record': f"{safe_get('Wins', 0)}-{safe_get('Losses', 0)}",
        
        # Four Factors endpoint fields
        'efg_pct': safe_get('eFG_Pct'),
        'to_pct': safe_get('TO_Pct'),
        'or_pct': safe_get('OR_Pct'),
        'ft_rate': safe_get('FT_Rate'),
        'defg_pct': safe_get('DeFG_Pct'),
        'dto_pct': safe_get('DTO_Pct'),
        'dor_pct': safe_get('DOR_Pct'),
        'dft_rate': safe_get('DFT_Rate'),
        
        # Miscellaneous Stats endpoint fields
        'fg3_pct': safe_get('FG3Pct'),
        'fg2_pct': safe_get('FG2Pct'),
        'ft_pct': safe_get('FTPct'),
        'block_pct': safe_get('BlockPct'),
        'stl_rate': safe_get('StlRate'),
        'a_rate': safe_get('ARate'),
        'f3g_rate': safe_get('F3GRate'),
        
        # Point Distribution endpoint fields
        'off_ft': safe_get('OffFt'),
        'off_fg2': safe_get('OffFg2'),
        'off_fg3': safe_get('OffFg3'),
        
        # Height endpoint fields
        'avg_height': safe_get('AvgHgt'),
        'eff_height': safe_get('HgtEff'),
        'experience': safe_get('Exp'),
        'bench': safe_get('Bench'),
        'continuity': safe_get('Continuity'),
    }
    
    return stats

def get_game_prediction(away_team, home_team, predictions_df):
    """Get prediction data from CBB_Output.csv"""
    # Find team name column
    team_col = None
    for col in predictions_df.columns:
        if col.lower() in ['team', 'teamname', 'team_name']:
            team_col = col
            break
    
    if team_col is None:
        print(f"Could not find team column in predictions. Available columns: {predictions_df.columns.tolist()}")
        return None
    
    # Get both team predictions
    away_pred = predictions_df[predictions_df[team_col] == away_team]
    home_pred = predictions_df[predictions_df[team_col] == home_team]
    
    if away_pred.empty or home_pred.empty:
        print(f"  ⚠️  Could not find prediction for {away_team} or {home_team}")
        return None
    
    # Helper function to safely get column value
    def safe_get(df, col_name, default='N/A'):
        if col_name in df.columns:
            val = df[col_name].values[0]
            if isinstance(val, (int, float)) and val != val:  # Check for NaN
                return default
            return val
        return default
    
    # Get predicted outcome values (negative = favorite)
    away_outcome = safe_get(away_pred, 'Predicted Outcome', 0)
    home_outcome = safe_get(home_pred, 'Predicted Outcome', 0)
    
    # Get moneyline win probabilities
    away_win_prob = safe_get(away_pred, 'Moneyline Win Probability', 0)
    home_win_prob = safe_get(home_pred, 'Moneyline Win Probability', 0)
    
    # Determine winner based on:
    # 1. Who has negative Predicted Outcome (favorite)
    # 2. Who has higher Moneyline Win Probability
    if isinstance(away_outcome, (int, float)) and isinstance(home_outcome, (int, float)):
        if away_outcome < 0 or away_win_prob > home_win_prob:
            predicted_winner = away_team
            winner_prob = away_win_prob
            spread = away_outcome
        else:
            predicted_winner = home_team
            winner_prob = home_win_prob
            spread = home_outcome
    else:
        # Fallback to win probability only
        if away_win_prob > home_win_prob:
            predicted_winner = away_team
            winner_prob = away_win_prob
            spread = away_outcome
        else:
            predicted_winner = home_team
            winner_prob = home_win_prob
            spread = home_outcome
    
    # Get scores if available
    away_score = safe_get(away_pred, 'Predicted Score', 'N/A')
    home_score = safe_get(home_pred, 'Predicted Score', 'N/A')
    
    # Calculate confidence based on probability difference
    if isinstance(away_win_prob, (int, float)) and isinstance(home_win_prob, (int, float)):
        prob_diff = abs(away_win_prob - home_win_prob)
        if prob_diff > 20:
            confidence = "High"
        elif prob_diff > 10:
            confidence = "Medium"
        else:
            confidence = "Low"
    else:
        confidence = "N/A"
    
    # Determine model lean
    if isinstance(spread, (int, float)):
        if abs(spread) > 10:
            model_lean = f"Strong lean towards {predicted_winner}"
        elif abs(spread) > 5:
            model_lean = f"Moderate lean towards {predicted_winner}"
        else:
            model_lean = "Close game, slight edge"
    else:
        model_lean = "N/A"
    
    prediction = {
        'predicted_winner': predicted_winner,
        'away_score': away_score,
        'home_score': home_score,
        'spread': spread,
        'win_probability': winner_prob,
        'confidence': confidence,
        'model_lean': model_lean,
        'away_win_prob': away_win_prob,
        'home_win_prob': home_win_prob,
    }
    
    return prediction

def generate_preview_content(away_team, home_team, game_time, game_date, away_stats, home_stats, prediction):
    """Generate the game preview content using the new template format"""
    
    # Format team names for URL slug
    slug = f"{away_team.lower().replace(' ', '-')}-vs-{home_team.lower().replace(' ', '-')}"
    
    # Format spread display
    if isinstance(prediction['spread'], (int, float)):
        spread_display = f"{prediction['spread']:+.1f}"
    else:
        spread_display = prediction['spread']
    
    # Format win probability
    if isinstance(prediction['win_probability'], (int, float)):
        win_prob_display = f"{prediction['win_probability']:.1f}"
    else:
        win_prob_display = prediction['win_probability']
    
    content = f"""---
title: "{away_team} vs {home_team} Preview & Prediction"
date: {game_date}
categories: [NCAA Basketball, Game Previews]
tags: ["{away_team}", "{home_team}", KenPom, Predictions]
excerpt: "Expert analysis and prediction for {away_team} vs {home_team}. Get the latest stats, trends, and betting insights."
---

## {away_team} (#{away_stats['rank']}) @ {home_team} (#{home_stats['rank']})

**Game Time:** {game_time}

### Game Overview

The {away_team} will travel to face the {home_team} in what promises to be an exciting matchup. Both teams bring unique strengths to the court, and our analysis breaks down the key factors that will determine the outcome.

---

### Team Statistics

#### {away_team} (Away)
- **Record:** {away_stats['record']}
- **KenPom Rank:** #{away_stats['rank']}
- **Adjusted Efficiency Margin:** {away_stats['adj_em']}
- **Offensive Efficiency:** {away_stats['adj_oe']} (Rank: #{away_stats['adj_oe_rank']})
- **Defensive Efficiency:** {away_stats['adj_de']} (Rank: #{away_stats['adj_de_rank']})
- **Adjusted Tempo:** {away_stats['adj_tempo']} (Rank: #{away_stats['adj_tempo_rank']})

**Four Factors (Offense):**
- eFG%: {away_stats['efg_pct']}%
- Turnover Rate: {away_stats['to_pct']}%
- Offensive Rebound Rate: {away_stats['or_pct']}%
- Free Throw Rate: {away_stats['ft_rate']}

**Four Factors (Defense):**
- Opponent eFG%: {away_stats['defg_pct']}%
- Opponent Turnover Rate: {away_stats['dto_pct']}%
- Defensive Rebound Rate: {away_stats['dor_pct']}%
- Opponent Free Throw Rate: {away_stats['dft_rate']}

**Shooting:**
- 3PT%: {away_stats['fg3_pct']}%
- 2PT%: {away_stats['fg2_pct']}%
- FT%: {away_stats['ft_pct']}%

**Advanced Metrics:**
- Block %: {away_stats['block_pct']}%
- Steal Rate: {away_stats['stl_rate']}
- Assist Rate: {away_stats['a_rate']}%
- 3PT Rate: {away_stats['f3g_rate']}%

**Team Composition:**
- Average Height: {away_stats['avg_height']}"
- Effective Height: {away_stats['eff_height']}
- Experience: {away_stats['experience']}
- Bench Strength: {away_stats['bench']}
- Continuity: {away_stats['continuity']}

---

#### {home_team} (Home)
- **Record:** {home_stats['record']}
- **KenPom Rank:** #{home_stats['rank']}
- **Adjusted Efficiency Margin:** {home_stats['adj_em']}
- **Offensive Efficiency:** {home_stats['adj_oe']} (Rank: #{home_stats['adj_oe_rank']})
- **Defensive Efficiency:** {home_stats['adj_de']} (Rank: #{home_stats['adj_de_rank']})
- **Adjusted Tempo:** {home_stats['adj_tempo']} (Rank: #{home_stats['adj_tempo_rank']})

**Four Factors (Offense):**
- eFG%: {home_stats['efg_pct']}%
- Turnover Rate: {home_stats['to_pct']}%
- Offensive Rebound Rate: {home_stats['or_pct']}%
- Free Throw Rate: {home_stats['ft_rate']}

**Four Factors (Defense):**
- Opponent eFG%: {home_stats['defg_pct']}%
- Opponent Turnover Rate: {home_stats['dto_pct']}%
- Defensive Rebound Rate: {home_stats['dor_pct']}%
- Opponent Free Throw Rate: {home_stats['dft_rate']}

**Shooting:**
- 3PT%: {home_stats['fg3_pct']}%
- 2PT%: {home_stats['fg2_pct']}%
- FT%: {home_stats['ft_pct']}%

**Advanced Metrics:**
- Block %: {home_stats['block_pct']}%
- Steal Rate: {home_stats['stl_rate']}
- Assist Rate: {home_stats['a_rate']}%
- 3PT Rate: {home_stats['f3g_rate']}%

**Team Composition:**
- Average Height: {home_stats['avg_height']}"
- Effective Height: {home_stats['eff_height']}
- Experience: {home_stats['experience']}
- Bench Strength: {home_stats['bench']}
- Continuity: {home_stats['continuity']}

---

### Prediction & Model Lean

Our model predicts **{prediction['predicted_winner']}** will win this matchup.

- **Predicted Score:** {away_team} {prediction['away_score']} - {home_team} {prediction['home_score']}
- **{prediction['predicted_winner']} Spread:** {spread_display}
- **{prediction['predicted_winner']} Win Probability:** {win_prob_display}%
- **Model Confidence:** {prediction['confidence']}
- **Model Lean:** {prediction['model_lean']}

**Win Probabilities:**
- {away_team}: {prediction['away_win_prob']}%
- {home_team}: {prediction['home_win_prob']}%

---

### Key Matchup Factors

**Tempo Battle:**
{away_team} plays at a tempo of {away_stats['adj_tempo']} possessions per game (Rank #{away_stats['adj_tempo_rank']}), while {home_team} operates at {home_stats['adj_tempo']} (Rank #{home_stats['adj_tempo_rank']}). The team that can impose their preferred pace will have a significant advantage.

**Offensive Efficiency:**
{away_team} ranks #{away_stats['adj_oe_rank']} in adjusted offensive efficiency ({away_stats['adj_oe']}), compared to {home_team}'s #{home_stats['adj_oe_rank']} ranking ({home_stats['adj_oe']}). 

**Defensive Matchup:**
Defensively, {away_team} ranks #{away_stats['adj_de_rank']} ({away_stats['adj_de']}), while {home_team} ranks #{home_stats['adj_de_rank']} ({home_stats['adj_de']}). 

**Three-Point Shooting:**
{away_team} shoots {away_stats['fg3_pct']}% from beyond the arc and attempts threes at a rate of {away_stats['f3g_rate']}%. {home_team} counters with {home_stats['fg3_pct']}% shooting and a {home_stats['f3g_rate']}% three-point rate.

**Rebounding:**
{away_team} grabs offensive rebounds at a {away_stats['or_pct']}% rate, while {home_team} secures {home_stats['dor_pct']}% of available defensive rebounds.

**Ball Security:**
{away_team} turns the ball over on {away_stats['to_pct']}% of possessions, while {home_team}'s defense forces turnovers at a {home_stats['dto_pct']}% rate.

---

### Betting Insights

- **Spread:** {spread_display} ({prediction['predicted_winner']})
- **Confidence Level:** {prediction['confidence']}
- **Value Pick:** {prediction['model_lean']}

---

*This preview is generated using advanced statistical models and KenPom efficiency ratings. Check back for updated analysis as game time approaches.*
"""
    
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
    
    if tomorrow_games.empty:
        print("No games scheduled for tomorrow.")
        return
    
    print(f"Found {len(tomorrow_games)} games for tomorrow.\n")
    
    # Find column names in kp.csv
    away_col = None
    home_col = None
    time_col = None
    date_col = None
    
    for col in tomorrow_games.columns:
        col_lower = col.lower()
        if col_lower in ['away', 'awayteam', 'away_team', 'visitor']:
            away_col = col
        elif col_lower in ['home', 'hometeam', 'home_team']:
            home_col = col
        elif col_lower in ['time', 'gametime', 'game_time']:
            time_col = col
        elif col_lower in ['date', 'gamedate', 'game_date']:
            date_col = col
    
    if away_col is None or home_col is None:
        print(f"Could not find away/home columns. Available columns: {tomorrow_games.columns.tolist()}")
        return
    
    for idx, game in tomorrow_games.iterrows():
        away_team = game[away_col]
        home_team = game[home_col]
        game_time = game[time_col] if time_col and time_col in game else 'TBD'
        game_date = game[date_col] if date_col and date_col in game else datetime.now().strftime('%Y-%m-%d')
        
        print(f"Generating preview for: {away_team} @ {home_team}")
        
        # Get stats for both teams
        away_stats = get_team_stats(away_team, kenpom_stats_df)
        home_stats = get_team_stats(home_team, kenpom_stats_df)
        
        if away_stats is None or home_stats is None:
            print(f"  ⚠️  Could not find stats for one or both teams. Skipping...\n")
            continue
        
        # Get prediction
        prediction = get_game_prediction(away_team, home_team, predictions_df)
        
        if prediction is None:
            print(f"  ⚠️  Could not find prediction data. Skipping...\n")
            continue
        
        # Generate preview content
        content, slug = generate_preview_content(
            away_team, home_team, game_time, game_date, 
            away_stats, home_stats, prediction
        )
        
        # Save preview
        save_preview(content, slug, game_date)
        print()  # Empty line for readability
    
    print("✅ All previews generated successfully!")

if __name__ == "__main__":
    main()

import os
import sys
import html
import pandas as pd
import numpy as np
import requests
import base64
import traceback
from io import StringIO
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")
console = Console()

# Output file paths
DOCS_DIR = "docs"
WEEKLY_DIR = os.path.join(DOCS_DIR, "weekly")
HISTORICAL_DIR = os.path.join(WEEKLY_DIR, "historical")
CURRENT_WEEK_HTML = os.path.join(WEEKLY_DIR, "current_week.html")
CURRENT_WEEK_CSV = os.path.join(WEEKLY_DIR, "current_week.csv")

# Color constants for result styling
RESULT_WIN_COLOR = "#16a34a"  # Green
RESULT_LOSS_COLOR = "#dc2626"  # Red
RESULT_FONT_WEIGHT = "600"

"""
Weekly Model Performance Analysis Script

This script analyzes model performance on a weekly basis (Monday-Sunday).
It generates an HTML report for the current week and saves historical CSV files
when a new week begins.

Usage:
    python analyze_model_performance_weekly.py

Environment Variables:
    GITHUB_TOKEN - Optional GitHub token for accessing private repositories
"""


def get_week_start_end(date=None):
    """
    Get the start (Monday) and end (Sunday) dates for a given week.
    
    Args:
        date: datetime object (defaults to today)
    
    Returns:
        tuple: (week_start, week_end) as datetime objects
    """
    if date is None:
        date = datetime.now(timezone.utc)
    
    # Get Monday of the current week (weekday() returns 0 for Monday)
    days_since_monday = date.weekday()
    week_start = (date - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = (week_start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return week_start, week_end


def get_week_label(week_start, week_end):
    """
    Generate a human-readable week label.
    
    Args:
        week_start: datetime object for Monday
        week_end: datetime object for Sunday
    
    Returns:
        str: Week label (e.g., "Week of Jan 6-12, 2025")
    """
    return f"Week of {week_start.strftime('%b %d')}-{week_end.strftime('%d, %Y')}"


def get_week_filename(week_start):
    """
    Generate a filename for a given week.
    
    Args:
        week_start: datetime object for Monday
    
    Returns:
        str: Filename (e.g., "week_2025_01_06.csv")
    """
    return f"week_{week_start.strftime('%Y_%m_%d')}.csv"


def fetch_graded_results_from_github():
    """
    Fetches graded_results.csv from the trashduty/cbb repository main branch
    Falls back to local file if API access fails
    """
    raw_url = "https://raw.githubusercontent.com/trashduty/cbb/main/graded_results.csv"
    
    try:
        logger.info("[cyan]Fetching graded_results.csv from trashduty/cbb repository...[/cyan]")
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        
        logger.info(f"[green]✓[/green] Successfully loaded graded_results.csv with {len(df)} rows")
        return df
        
    except Exception as err:
        logger.warning(f"[yellow]⚠[/yellow] Error occurred: {err}")
        logger.info("[cyan]Attempting to use GitHub API...[/cyan]")
        return fetch_via_api()


def fetch_via_api():
    """
    Try to fetch using GitHub API with base64 decoding
    """
    url = "https://api.github.com/repos/trashduty/cbb/contents/graded_results.csv"
    params = {'ref': 'main'}
    
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        file_data = response.json()
        content_base64 = file_data['content']
        content_decoded = base64.b64decode(content_base64).decode('utf-8')
        
        df = pd.read_csv(StringIO(content_decoded))
        logger.info(f"[green]✓[/green] Successfully loaded graded_results.csv with {len(df)} rows")
        return df
        
    except Exception as err:
        logger.warning(f"[yellow]⚠[/yellow] Error occurred: {err}")
        logger.info("[cyan]Attempting to use local graded_results.csv file...[/cyan]")
        return try_local_file()


def try_local_file():
    """
    Try to load graded_results.csv from local directory
    """
    try:
        if os.path.exists('graded_results.csv'):
            df = pd.read_csv('graded_results.csv')
            logger.info(f"[green]✓[/green] Successfully loaded local graded_results.csv with {len(df)} rows")
            return df
        else:
            logger.error("[red]✗[/red] Local graded_results.csv file not found")
            logger.info("[yellow]Please ensure you have access to the trashduty/cbb repository or place graded_results.csv in the current directory[/yellow]")
            return None
    except Exception as e:
        logger.error(f"[red]✗[/red] Error loading local file: {e}")
        return None


def filter_data_by_week(df, week_start, week_end):
    """
    Filter DataFrame to only include games from the specified week.
    
    Args:
        df: pandas DataFrame with game data
        week_start: datetime object for Monday
        week_end: datetime object for Sunday
    
    Returns:
        DataFrame: Filtered data for the week
    """
    # Convert date column to datetime
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter for the week
    mask = (df['date'] >= week_start) & (df['date'] <= week_end)
    week_data = df[mask].copy()
    
    logger.info(f"[cyan]Filtered to {len(week_data)} rows for {get_week_label(week_start, week_end)}[/cyan]")
    
    return week_data


def save_historical_week(df, week_start):
    """
    Save historical week data to CSV file.
    
    Args:
        df: DataFrame with week's game data
        week_start: datetime object for Monday
    """
    os.makedirs(HISTORICAL_DIR, exist_ok=True)
    
    filename = get_week_filename(week_start)
    filepath = os.path.join(HISTORICAL_DIR, filename)
    
    # Only save if file doesn't exist (don't overwrite historical data)
    if not os.path.exists(filepath):
        df.to_csv(filepath, index=False)
        logger.info(f"[green]✓[/green] Saved historical week data to {filepath}")
    else:
        logger.info(f"[yellow]⚠[/yellow] Historical file {filepath} already exists, skipping save")


def check_and_archive_previous_week():
    """
    Check if we need to archive the previous week's data.
    If current_week.csv exists and is from a previous week, archive it.
    """
    if not os.path.exists(CURRENT_WEEK_CSV):
        return
    
    try:
        # Load current week CSV
        current_df = pd.read_csv(CURRENT_WEEK_CSV)
        
        if len(current_df) == 0:
            return
        
        # Get the date range from the CSV
        current_df['date'] = pd.to_datetime(current_df['date'])
        csv_min_date = current_df['date'].min()
        csv_max_date = current_df['date'].max()
        
        # Get current week range
        now = datetime.now(timezone.utc)
        current_week_start, current_week_end = get_week_start_end(now)
        
        # If the CSV data is from a previous week, archive it
        if csv_max_date < current_week_start.replace(tzinfo=None):
            # Find the week start for the CSV data
            csv_week_start, _ = get_week_start_end(csv_min_date.to_pydatetime().replace(tzinfo=timezone.utc))
            
            logger.info(f"[yellow]Archiving previous week: {get_week_label(csv_week_start, csv_week_start + timedelta(days=6))}[/yellow]")
            save_historical_week(current_df, csv_week_start)
    
    except Exception as e:
        logger.warning(f"[yellow]⚠[/yellow] Error checking previous week: {e}")


def format_win_loss_pct(wins, losses):
    """
    Format win-loss record with percentage
    """
    total = wins + losses
    if total == 0:
        return "0-0 (0.0%)"
    pct = (wins / total) * 100
    return f"{wins}-{losses} ({pct:.1f}%)"


def deduplicate_games(df):
    """
    De-duplicate games to have one row per game instead of one row per team.
    """
    df = df.copy()
    
    team_min = df[['home_team', 'away_team']].min(axis=1)
    team_max = df[['home_team', 'away_team']].max(axis=1)
    df['game_id'] = df['date'].astype(str) + '_' + team_min + '_' + team_max
    
    df_dedup = df.drop_duplicates(subset=['game_id'], keep='first')
    df_dedup = df_dedup.drop('game_id', axis=1)
    
    return df_dedup


def extract_game_details(row, bet_type='spread', result_field=None, edge_field=None):
    """
    Extract game details from a DataFrame row
    """
    date = row.get('date', row.get('game_date', 'N/A'))
    if hasattr(date, 'strftime'):
        date = date.strftime('%Y-%m-%d')
    
    home_team = row.get('home_team', 'N/A')
    away_team = row.get('away_team', 'N/A')
    matchup = f"{away_team} @ {home_team}"
    
    details = {
        'date': date,
        'matchup': matchup
    }
    
    if result_field:
        result_value = row.get(result_field, None)
        if result_value is not None and result_value == 1:
            details['result'] = 'Win'
        elif result_value is not None and result_value == 0:
            details['result'] = 'Loss'
        else:
            details['result'] = 'N/A'
    
    if edge_field:
        edge_value = row.get(edge_field, None)
        if pd.notna(edge_value):
            if isinstance(edge_value, (int, float, np.integer, np.floating)):
                edge_pct = float(edge_value) * 100
                details['edge'] = f"{edge_pct:.1f}%"
            else:
                details['edge'] = 'N/A'
        else:
            details['edge'] = 'N/A'
    
    if bet_type == 'spread':
        details['team'] = row.get('team', 'N/A')
        details['opening_spread'] = row.get('opening_spread', 'N/A')
        details['closing_spread'] = row.get('closing_spread', 'N/A')
    elif bet_type == 'total':
        details['opening_total'] = row.get('opening_total', 'N/A')
        details['closing_total'] = row.get('closing_total', 'N/A')
    elif bet_type == 'moneyline':
        details['team'] = row.get('team', 'N/A')
        details['opening_moneyline'] = row.get('opening_moneyline', 'N/A')
        details['closing_moneyline'] = row.get('closing_moneyline', 'N/A')
    
    return details


def collect_spread_performance_by_edge(df, consensus_only=False):
    """
    Collect spread performance by edge data for output
    """
    data = df.dropna(subset=['spread_covered', 'opening_spread_edge']).copy()
    
    if consensus_only:
        data = data[data['spread_consensus_flag'] == 1].copy()
    
    tiers = [
        (0.0, 0.01, "0-0.9%"),
        (0.01, 0.02, "1-1.9%"),
        (0.02, 0.03, "2-2.9%"),
        (0.03, 0.04, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    results = []
    for min_edge, max_edge, label in tiers:
        tier_data = data[(data['opening_spread_edge'] >= min_edge) & (data['opening_spread_edge'] < max_edge)]
        wins = (tier_data['spread_covered'] == 1).sum()
        losses = (tier_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        games = []
        for _, row in tier_data.iterrows():
            games.append(extract_game_details(row, bet_type='spread', result_field='spread_covered', edge_field='opening_spread_edge'))
        
        if total > 0:
            win_pct = (wins / total) * 100
            results.append({
                'tier': label, 
                'record': f"{wins}-{losses}", 
                'pct': f"{win_pct:.1f}%",
                'games': games
            })
        else:
            results.append({
                'tier': label, 
                'record': "0-0", 
                'pct': "0.0%",
                'games': games
            })
    
    return results


def collect_over_under_performance_by_edge(df, consensus_only=False):
    """
    Collect over/under performance by edge data for output
    """
    tiers = [
        (0.0, 0.01, "0-0.9%"),
        (0.01, 0.02, "1-1.9%"),
        (0.02, 0.03, "2-2.9%"),
        (0.03, 0.04, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    # Overs
    over_data = df.dropna(subset=['over_hit', 'opening_over_edge']).copy()
    if consensus_only:
        over_data = over_data[over_data['over_consensus_flag'] == 1].copy()
    over_data = deduplicate_games(over_data)
    
    over_results = []
    for min_edge, max_edge, label in tiers:
        tier_data = over_data[(over_data['opening_over_edge'] >= min_edge) & (over_data['opening_over_edge'] < max_edge)]
        wins = (tier_data['over_hit'] == 1).sum()
        losses = (tier_data['over_hit'] == 0).sum()
        total = wins + losses
        
        games = []
        for _, row in tier_data.iterrows():
            games.append(extract_game_details(row, bet_type='total', result_field='over_hit', edge_field='opening_over_edge'))
        
        if total > 0:
            win_pct = (wins / total) * 100
            over_results.append({
                'tier': label, 
                'record': f"{wins}-{losses}", 
                'pct': f"{win_pct:.1f}%",
                'games': games
            })
        else:
            over_results.append({
                'tier': label, 
                'record': "0-0", 
                'pct': "0.0%",
                'games': games
            })
    
    # Unders
    under_data = df.dropna(subset=['under_hit', 'opening_under_edge']).copy()
    if consensus_only:
        under_data = under_data[under_data['under_consensus_flag'] == 1].copy()
    under_data = deduplicate_games(under_data)
    
    under_results = []
    for min_edge, max_edge, label in tiers:
        tier_data = under_data[(under_data['opening_under_edge'] >= min_edge) & (under_data['opening_under_edge'] < max_edge)]
        wins = (tier_data['under_hit'] == 1).sum()
        losses = (tier_data['under_hit'] == 0).sum()
        total = wins + losses
        
        games = []
        for _, row in tier_data.iterrows():
            games.append(extract_game_details(row, bet_type='total', result_field='under_hit', edge_field='opening_under_edge'))
        
        if total > 0:
            win_pct = (wins / total) * 100
            under_results.append({
                'tier': label, 
                'record': f"{wins}-{losses}", 
                'pct': f"{win_pct:.1f}%",
                'games': games
            })
        else:
            under_results.append({
                'tier': label, 
                'record': "0-0", 
                'pct': "0.0%",
                'games': games
            })
    
    return {'overs': over_results, 'unders': under_results}


def collect_moneyline_performance_by_probability(df, consensus_only=False):
    """
    Collect moneyline performance by win probability data for output
    """
    data = df[df['moneyline_consensus_flag'] == 1].copy() if consensus_only else df.copy()
    data = data.dropna(subset=['moneyline_win_probability'])
    
    tiers = [
        (0.10, 0.19, "10-19%"),
        (0.20, 0.29, "20-29%"),
        (0.30, 0.39, "30-39%"),
        (0.40, 0.49, "40-49%"),
        (0.50, 0.59, "50-59%"),
        (0.60, 0.69, "60-69%"),
        (0.70, 0.79, "70-79%"),
        (0.80, 0.89, "80-89%"),
        (0.90, 1.0, "90%+")
    ]
    
    results = []
    for min_prob, max_prob, label in tiers:
        tier_data = data[(data['moneyline_win_probability'] >= min_prob) & (data['moneyline_win_probability'] <= max_prob)]
        wins = (tier_data['moneyline_won'] == 1).sum()
        losses = (tier_data['moneyline_won'] == 0).sum()
        total = wins + losses
        
        games = []
        for _, row in tier_data.iterrows():
            games.append(extract_game_details(row, bet_type='moneyline', result_field='moneyline_won', edge_field='opening_moneyline_edge'))
        
        if total > 0:
            win_pct = (wins / total) * 100
            results.append({
                'tier': label, 
                'record': f"{wins}-{losses}", 
                'pct': f"{win_pct:.1f}%",
                'games': games
            })
        else:
            results.append({
                'tier': label, 
                'record': "0-0", 
                'pct': "0.0%",
                'games': games
            })
    
    return results


def escape_html(value):
    """
    Escape HTML special characters to prevent XSS
    """
    return html.escape(str(value))


def generate_game_details_html(games, bet_type='spread'):
    """
    Generate HTML for game details drill-down
    """
    if not games:
        return '<p style="color: #999; font-style: italic; margin: 10px 0;">No games in this category</p>'
    
    html_str = '<table class="game-details-table">'
    html_str += '<thead><tr>'
    html_str += '<th>Date</th>'
    html_str += '<th>Matchup</th>'
    
    if bet_type == 'spread':
        html_str += '<th>Team</th>'
        html_str += '<th>Opening Spread</th>'
        html_str += '<th>Edge</th>'
        html_str += '<th>Closing Spread</th>'
    elif bet_type == 'total':
        html_str += '<th>Opening Total</th>'
        html_str += '<th>Edge</th>'
        html_str += '<th>Closing Total</th>'
    elif bet_type == 'moneyline':
        html_str += '<th>Team</th>'
        html_str += '<th>Opening ML</th>'
        html_str += '<th>Edge</th>'
        html_str += '<th>Closing ML</th>'
    
    html_str += '<th>Result</th>'
    html_str += '</tr></thead><tbody>'
    
    for game in games:
        html_str += '<tr>'
        html_str += f'<td>{escape_html(game.get("date", "N/A"))}</td>'
        html_str += f'<td>{escape_html(game.get("matchup", "N/A"))}</td>'
        
        if bet_type == 'spread':
            html_str += f'<td>{escape_html(game.get("team", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("opening_spread", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("edge", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("closing_spread", "N/A"))}</td>'
        elif bet_type == 'total':
            html_str += f'<td>{escape_html(game.get("opening_total", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("edge", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("closing_total", "N/A"))}</td>'
        elif bet_type == 'moneyline':
            html_str += f'<td>{escape_html(game.get("team", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("opening_moneyline", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("edge", "N/A"))}</td>'
            html_str += f'<td>{escape_html(game.get("closing_moneyline", "N/A"))}</td>'
        
        result = game.get("result", "N/A")
        if result == "Win":
            html_str += f'<td style="color: {RESULT_WIN_COLOR}; font-weight: {RESULT_FONT_WEIGHT};">{escape_html(result)}</td>'
        elif result == "Loss":
            html_str += f'<td style="color: {RESULT_LOSS_COLOR}; font-weight: {RESULT_FONT_WEIGHT};">{escape_html(result)}</td>'
        else:
            html_str += f'<td>{escape_html(result)}</td>'
        
        html_str += '</tr>'
    
    html_str += '</tbody></table>'
    return html_str


def generate_weekly_html(analysis_data, week_label, timestamp):
    """
    Generate HTML output for weekly analysis
    """
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Model Performance - {escape_html(week_label)}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #2c5282;
        }}
        h1 {{
            color: #2c5282;
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .week-label {{
            color: #e53e3e;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9rem;
        }}
        .disclaimer {{
            font-size: 0.9rem;
            color: #718096;
            margin-top: 10px;
            font-style: italic;
        }}
        section {{
            margin-bottom: 40px;
        }}
        h2 {{
            color: #2c5282;
            font-size: 1.3rem;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        h3 {{
            color: #4a5568;
            font-size: 1.1rem;
            margin: 20px 0 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #2c5282;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        tr:hover {{
            background-color: #edf2f7;
        }}
        td:last-child, th:last-child {{
            text-align: right;
        }}
        td:nth-child(2), th:nth-child(2) {{
            text-align: center;
        }}
        .subsection {{
            margin-top: 25px;
        }}
        details {{
            margin-bottom: 2px;
        }}
        summary {{
            cursor: pointer;
            padding: 12px 15px;
            background-color: #f7fafc;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s ease;
        }}
        summary:hover {{
            background-color: #edf2f7;
        }}
        summary::marker {{
            content: '▶ ';
            font-size: 0.8em;
        }}
        details[open] summary::marker {{
            content: '▼ ';
        }}
        .summary-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }}
        .summary-content > span:first-child {{
            flex: 1;
            text-align: left;
        }}
        .summary-content > span:nth-child(2) {{
            flex: 1;
            text-align: center;
        }}
        .summary-content > span:last-child {{
            flex: 1;
            text-align: right;
        }}
        .game-details {{
            padding: 20px;
            background-color: #fff;
            border-left: 3px solid #2c5282;
            margin: 0;
        }}
        .game-details-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.9rem;
        }}
        .game-details-table th {{
            background-color: #4a5568;
            color: white;
            font-weight: 600;
            padding: 8px 12px;
            text-align: left;
        }}
        .game-details-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .game-details-table tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        .game-details-table tr:hover {{
            background-color: #edf2f7;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #666;
            font-size: 0.9rem;
        }}
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 15px;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
            h2 {{
                font-size: 1.1rem;
            }}
            table {{
                font-size: 0.9rem;
            }}
            th, td {{
                padding: 8px 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Weekly Model Performance Analysis</h1>
            <p class="week-label">{escape_html(week_label)}</p>
            <p class="timestamp">Generated: {escape_html(timestamp)}</p>
            <p class="disclaimer">This report shows the model's weekly performance against opening lines for spreads, totals, and moneylines.</p>
        </header>

        <section>
            <h2>Spread Performance by Edge (All Games)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Edge Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['spread_by_edge_all']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{escape_html(row['tier'])}</span>
                                        <span>{escape_html(row['record'])}</span>
                                        <span>{escape_html(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>Spread Performance by Edge (Consensus Only)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Edge Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['spread_by_edge_consensus']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{escape_html(row['tier'])}</span>
                                        <span>{escape_html(row['record'])}</span>
                                        <span>{escape_html(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>Over/Under Performance by Edge (All Games)</h2>
            <div class="subsection">
                <h3>Overs Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_all']['overs']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['tier'])}</span>
                                            <span>{escape_html(row['record'])}</span>
                                            <span>{escape_html(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Unders Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_all']['unders']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['tier'])}</span>
                                            <span>{escape_html(row['record'])}</span>
                                            <span>{escape_html(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>Over/Under Performance by Edge (Consensus Only)</h2>
            <div class="subsection">
                <h3>Overs Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_consensus']['overs']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['tier'])}</span>
                                            <span>{escape_html(row['record'])}</span>
                                            <span>{escape_html(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Unders Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_consensus']['unders']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['tier'])}</span>
                                            <span>{escape_html(row['record'])}</span>
                                            <span>{escape_html(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>Moneyline Performance by Win Probability (All Games)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_all']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='moneyline')
        html += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{escape_html(row['tier'])}</span>
                                        <span>{escape_html(row['record'])}</span>
                                        <span>{escape_html(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>Moneyline Performance by Win Probability (Consensus Only)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_consensus']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='moneyline')
        html += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{escape_html(row['tier'])}</span>
                                        <span>{escape_html(row['record'])}</span>
                                        <span>{escape_html(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <footer>
            <p>Weekly analysis generated automatically | <a href="historical/" style="color: #2c5282;">View Historical Weeks</a></p>
        </footer>
    </div>
</body>
</html>
'''
    return html


def main():
    """
    Main function to orchestrate the weekly model performance analysis
    """
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]Weekly Model Performance Analysis Report[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    try:
        # Check and archive previous week if needed
        check_and_archive_previous_week()
        
        # Fetch data from GitHub
        df = fetch_graded_results_from_github()
        
        if df is None:
            logger.error("[red]✗[/red] Failed to fetch graded_results.csv")
            sys.exit(1)
        
        # Get current week range
        now = datetime.now(timezone.utc)
        week_start, week_end = get_week_start_end(now)
        week_label = get_week_label(week_start, week_end)
        
        logger.info(f"[cyan]Analyzing: {week_label}[/cyan]")
        
        # Filter data for current week
        week_df = filter_data_by_week(df, week_start, week_end)
        
        if len(week_df) == 0:
            logger.warning("[yellow]⚠[/yellow] No games found for current week")
            # Still generate HTML with empty data
        
        # Save current week CSV
        os.makedirs(WEEKLY_DIR, exist_ok=True)
        week_df.to_csv(CURRENT_WEEK_CSV, index=False)
        logger.info(f"[green]✓[/green] Saved current week data to {CURRENT_WEEK_CSV}")
        
        # Collect analysis data
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        analysis_data = {
            'spread_by_edge_all': collect_spread_performance_by_edge(week_df, consensus_only=False),
            'spread_by_edge_consensus': collect_spread_performance_by_edge(week_df, consensus_only=True),
            'ou_by_edge_all': collect_over_under_performance_by_edge(week_df, consensus_only=False),
            'ou_by_edge_consensus': collect_over_under_performance_by_edge(week_df, consensus_only=True),
            'moneyline_all': collect_moneyline_performance_by_probability(week_df, consensus_only=False),
            'moneyline_consensus': collect_moneyline_performance_by_probability(week_df, consensus_only=True),
        }
        
        # Generate and save HTML
        html_output = generate_weekly_html(analysis_data, week_label, timestamp)
        with open(CURRENT_WEEK_HTML, 'w', encoding='utf-8') as f:
            f.write(html_output)
        logger.info(f"[green]✓[/green] Saved weekly HTML to {CURRENT_WEEK_HTML}")
        
        # Print shareable link (GitHub Pages URL)
        repo_url = "https://trashduty.github.io/kp_test/weekly/current_week.html"
        console.print(f"\n[bold green]✓[/bold green] Analysis complete!")
        console.print(f"[bold cyan]Shareable link:[/bold cyan] {repo_url}\n")
        
        console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
        console.print("[bold green]Weekly Analysis Complete![/bold green]")
        console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")
        
    except Exception as e:
        logger.error(f"[red]✗[/red] Error in weekly analysis script: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

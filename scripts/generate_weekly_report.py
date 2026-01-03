#!/usr/bin/env python3
"""
Generate Weekly Performance Report Script

This script generates a weekly performance report by filtering data from the main 
model performance analysis for a specific week. The weekly reports have the same 
structure and format as docs/model_performance_analysis.html but only include 
games from the specified week.

Usage:
    python scripts/generate_weekly_report.py --week-start 2025-12-29

The script:
1. Takes a week start date as input (e.g., "2025-12-29")
2. Reads data from graded_results.csv (from GitHub or local)
3. Filters games to only include those in the specified 7-day week
4. Generates an HTML report with the same structure as model_performance_analysis.html
5. Outputs to docs/weekly/current_week.html
"""

import os
import sys
import argparse
import html
import pandas as pd
import numpy as np
import requests
import base64
from io import StringIO
from datetime import datetime, timedelta, timezone

# Add parent directory to path to import from analyze_model_performance
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import required functions from analyze_model_performance
from analyze_model_performance import (
    fetch_graded_results_from_github,
    collect_spread_performance_by_edge,
    collect_spread_performance_by_point_spread,
    collect_over_under_performance_by_edge,
    RESULT_WIN_COLOR,
    RESULT_LOSS_COLOR,
    RESULT_FONT_WEIGHT
)

# Output directory
WEEKLY_DIR = os.path.join(parent_dir, "docs", "weekly")
OUTPUT_FILE = os.path.join(WEEKLY_DIR, "current_week.html")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate weekly performance report for a specific week'
    )
    parser.add_argument(
        '--week-start',
        type=str,
        required=True,
        help='Week start date in YYYY-MM-DD format (e.g., 2025-12-29)'
    )
    return parser.parse_args()


def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error: Invalid date format '{date_str}'. Please use YYYY-MM-DD format.")
        sys.exit(1)


def filter_by_week(df, week_start_str):
    """
    Filter dataframe to only include games within the specified week
    
    Args:
        df: pandas DataFrame with game data
        week_start_str: Week start date string (YYYY-MM-DD)
    
    Returns:
        Filtered DataFrame
    
    Note:
        Creates a 7-day inclusive date range from start_date (inclusive) to 
        start_date + 6 days (inclusive), covering exactly 7 days.
    """
    # Parse the week start date
    week_start = parse_date(week_start_str)
    # Week end is 6 days after start, making it an inclusive 7-day range
    week_end = week_start + timedelta(days=6)
    
    print(f"Filtering games from {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')} (7 days, inclusive)")
    
    # Check if date column exists
    date_columns = ['date', 'game_date', 'Date', 'GameDate']
    date_col = None
    
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        print("Error: No date column found in the data")
        sys.exit(1)
    
    # Convert date column to datetime (strip time component for date comparison)
    df_filtered = df.copy()
    df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce').dt.normalize()
    
    # Normalize week boundaries to start of day for consistent comparison
    week_start_normalized = pd.Timestamp(week_start).normalize()
    week_end_normalized = pd.Timestamp(week_end).normalize()
    
    # Filter by date range (inclusive on both ends for exactly 7 days)
    mask = (df_filtered[date_col] >= week_start_normalized) & (df_filtered[date_col] <= week_end_normalized)
    df_week = df_filtered[mask].copy()
    
    print(f"Found {len(df_week)} rows for the specified week (out of {len(df)} total)")
    
    if len(df_week) == 0:
        print("Warning: No games found for the specified week")
    
    return df_week


def escape_html(text):
    """Escape HTML special characters"""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return "N/A"
    return html.escape(str(text))


def generate_game_details_html(games, bet_type='spread'):
    """
    Generate HTML for game details table
    
    Args:
        games: List of game dictionaries
        bet_type: Type of bet ('spread', 'total', 'moneyline')
    
    Returns:
        HTML string for game details table
    """
    if not games:
        return '<p>No games in this tier.</p>'
    
    # Define headers based on bet type
    if bet_type == 'spread':
        headers = ['Date', 'Matchup', 'Team', 'Opening Spread', 'Edge', 'Closing Spread', 'Result']
    elif bet_type == 'total':
        headers = ['Date', 'Matchup', 'Team', 'Opening Total', 'Edge', 'Closing Total', 'Result']
    elif bet_type == 'moneyline':
        headers = ['Date', 'Matchup', 'Team', 'Opening ML', 'Edge', 'Closing ML', 'Result']
    else:
        headers = ['Date', 'Matchup', 'Team', 'Opening', 'Edge', 'Closing', 'Result']
    
    html_str = '<table class="game-details-table"><thead><tr>'
    for header in headers:
        html_str += f'<th>{header}</th>'
    html_str += '</tr></thead><tbody>'
    
    for game in games:
        result_color = RESULT_WIN_COLOR if game.get('result') == 'Win' else RESULT_LOSS_COLOR
        html_str += '<tr>'
        html_str += f"<td>{escape_html(game.get('date', 'N/A'))}</td>"
        html_str += f"<td>{escape_html(game.get('matchup', 'N/A'))}</td>"
        html_str += f"<td>{escape_html(game.get('team', 'N/A'))}</td>"
        
        # Use bet-type-specific column names
        if bet_type == 'spread':
            html_str += f"<td>{escape_html(game.get('opening_spread', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('edge', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('closing_spread', 'N/A'))}</td>"
        elif bet_type == 'total':
            html_str += f"<td>{escape_html(game.get('opening_total', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('edge', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('closing_total', 'N/A'))}</td>"
        elif bet_type == 'moneyline':
            html_str += f"<td>{escape_html(game.get('opening_moneyline', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('edge', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('closing_moneyline', 'N/A'))}</td>"
        else:
            # Fallback for unknown bet types
            html_str += f"<td>{escape_html(game.get('opening', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('edge', 'N/A'))}</td>"
            html_str += f"<td>{escape_html(game.get('closing', 'N/A'))}</td>"
        
        html_str += f'<td style="color: {result_color}; font-weight: {RESULT_FONT_WEIGHT};">{escape_html(game.get("result", "N/A"))}</td>'
        html_str += '</tr>'
    
    html_str += '</tbody></table>'
    return html_str


def count_games_in_section(section_data):
    """
    Count total number of games in a section
    
    Args:
        section_data: Either a list of tier results or a dict with 'favorites'/'underdogs' or 'overs'/'unders'
    
    Returns:
        Total number of games
    """
    if isinstance(section_data, list):
        # For simple lists like spread_by_edge_all
        return sum(len(tier.get('games', [])) for tier in section_data)
    elif isinstance(section_data, dict):
        # For dicts like spread_by_point_spread or ou_by_edge_all
        total = 0
        for key in section_data:
            if isinstance(section_data[key], list):
                total += sum(len(tier.get('games', [])) for tier in section_data[key])
        return total
    return 0


def generate_weekly_html(analysis_data, week_start_str, week_end_str, timestamp, game_count):
    """
    Generate HTML output for weekly report
    
    Args:
        analysis_data: Dictionary containing analysis results
        week_start_str: Week start date string
        week_end_str: Week end date string
        timestamp: Report generation timestamp
        game_count: Number of games in the week
    
    Returns:
        HTML string
    """
    # Format dates for display
    start_date = datetime.strptime(week_start_str, '%Y-%m-%d')
    end_date = datetime.strptime(week_end_str, '%Y-%m-%d')
    date_range = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
    
    # Calculate game counts for each section
    section1_count = count_games_in_section(analysis_data['spread_by_edge_all'])
    section2_count = count_games_in_section(analysis_data['spread_by_edge_consensus'])
    section3_favorites_count = sum(len(tier.get('games', [])) for tier in analysis_data['spread_by_point_spread']['favorites'])
    section3_underdogs_count = sum(len(tier.get('games', [])) for tier in analysis_data['spread_by_point_spread']['underdogs'])
    section4_overs_count = sum(len(tier.get('games', [])) for tier in analysis_data['ou_by_edge_all']['overs'])
    section4_unders_count = sum(len(tier.get('games', [])) for tier in analysis_data['ou_by_edge_all']['unders'])
    section5_overs_count = sum(len(tier.get('games', [])) for tier in analysis_data['ou_by_edge_consensus']['overs'])
    section5_unders_count = sum(len(tier.get('games', [])) for tier in analysis_data['ou_by_edge_consensus']['unders'])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Model Performance - {week_start_str} to {week_end_str}</title>
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
        .week-range {{
            color: #4a5568;
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: 10px;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
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
            <h1>Weekly Model Performance Report</h1>
            <p class="week-range">Week of {escape_html(date_range)}</p>
            <p class="timestamp">Generated: {escape_html(timestamp)}</p>
            <p class="timestamp">Total Games: {game_count}</p>
            <p class="disclaimer">This report shows the model's record against the opening lines for spreads, totals, and moneylines for the specified week.</p>
        </header>

        <section>
            <h2>1. Model Spread Performance by Edge (All Games) ({section1_count} games)</h2>
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
            <h2>2. Model Spread Performance by Edge (Consensus Only) ({section2_count} games)</h2>
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
            <h2>3. Model Spread Performance by Point Spread Ranges</h2>
            <div class="subsection">
                <h3>Favorites (opening_spread &lt; 0) ({section3_favorites_count} games)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Point Spread Range</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    
    for row in analysis_data['spread_by_point_spread']['favorites']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['range'])}</span>
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
                <h3>Underdogs (opening_spread &gt; 0) ({section3_underdogs_count} games)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Point Spread Range</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    
    for row in analysis_data['spread_by_point_spread']['underdogs']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{escape_html(row['range'])}</span>
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
            <h2>4. Model Over/Under Performance by Edge (All Games)</h2>
            <div class="subsection">
                <h3>Overs ({section4_overs_count} games)</h3>
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
                <h3>Unders ({section4_unders_count} games)</h3>
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
            <h2>5. Model Over/Under Performance by Edge (Consensus Only)</h2>
            <div class="subsection">
                <h3>Overs ({section5_overs_count} games)</h3>
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
                <h3>Unders ({section5_unders_count} games)</h3>
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

        <footer>
            <p>Analysis generated automatically by weekly report script</p>
        </footer>
    </div>
</body>
</html>
'''
    
    return html


def main():
    """Main function to generate weekly performance report"""
    # Parse arguments
    args = parse_arguments()
    week_start_str = args.week_start
    
    # Calculate week end date
    week_start = parse_date(week_start_str)
    week_end = week_start + timedelta(days=6)
    week_end_str = week_end.strftime('%Y-%m-%d')
    
    print(f"=" * 80)
    print(f"Generating Weekly Performance Report")
    print(f"Week: {week_start_str} to {week_end_str}")
    print(f"=" * 80)
    print()
    
    # Fetch data from GitHub (or local fallback)
    print("Fetching graded_results.csv...")
    df = fetch_graded_results_from_github()
    
    if df is None:
        print("Error: Failed to fetch graded_results.csv")
        sys.exit(1)
    
    print(f"Loaded {len(df)} total rows from graded_results.csv")
    print()
    
    # Filter by week
    df_week = filter_by_week(df, week_start_str)
    
    if len(df_week) == 0:
        print("Warning: No games found for the specified week. Generating empty report...")
    
    print()
    print("Analyzing data...")
    
    # Collect analysis data for the week
    analysis_data = {
        'spread_by_edge_all': collect_spread_performance_by_edge(df_week, consensus_only=False),
        'spread_by_edge_consensus': collect_spread_performance_by_edge(df_week, consensus_only=True),
        'spread_by_point_spread': collect_spread_performance_by_point_spread(df_week),
        'ou_by_edge_all': collect_over_under_performance_by_edge(df_week, consensus_only=False),
        'ou_by_edge_consensus': collect_over_under_performance_by_edge(df_week, consensus_only=True),
    }
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Generate HTML output
    print("Generating HTML report...")
    html_output = generate_weekly_html(
        analysis_data,
        week_start_str,
        week_end_str,
        timestamp,
        len(df_week)
    )
    
    # Ensure output directory exists
    os.makedirs(WEEKLY_DIR, exist_ok=True)
    
    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✓ Report saved to: {OUTPUT_FILE}")
    print()
    print("=" * 80)
    print("Weekly report generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate Weekly Performance Report Script

This script generates weekly performance reports by filtering data from the main 
model performance analysis. It automatically generates reports for both the 
specified "current" week and the "previous" week.

Usage:
    python scripts/generate_weekly_report.py --week-start 2026-01-05
"""

import os
import sys
import argparse
import html
import shutil
import pandas as pd
import numpy as np
import requests
import base64
import pytz
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
CURRENT_WEEK_HTML = os.path.join(WEEKLY_DIR, "current_week.html")
CURRENT_WEEK_CSV = os.path.join(WEEKLY_DIR, "current_week.csv")
PREVIOUS_WEEK_HTML = os.path.join(WEEKLY_DIR, "previous_week.html")
PREVIOUS_WEEK_CSV = os.path.join(WEEKLY_DIR, "previous_week.csv")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate weekly performance reports'
    )
    parser.add_argument(
        '--week-start',
        type=str,
        required=True,
        help='Current week start date in YYYY-MM-DD format (e.g., 2026-01-05)'
    )
    parser.add_argument(
        '--output',
        type=str,
        choices=['current', 'previous', 'both'],
        default='both',
        help='Output file to generate (default: both)'
    )
    parser.add_argument(
        '--archive-current',
        action='store_true',
        help='Archive current week report to previous week (used by workflow)'
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
    """
    week_start = parse_date(week_start_str)
    week_end = week_start + timedelta(days=6)
    
    print(f"Filtering games from {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}...")
    
    date_columns = ['date', 'game_date', 'Date', 'GameDate']
    date_col = next((col for col in date_columns if col in df.columns), None)
    
    if date_col is None:
        print("Error: No date column found in the data")
        sys.exit(1)
    
    df_filtered = df.copy()
    # Treat dates as naive to avoid timezone shifting issues
    df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
    
    # Create mask using normalized dates (ignoring time)
    temp_date_col = df_filtered[date_col].dt.normalize()
    week_start_ts = pd.Timestamp(week_start).normalize()
    week_end_ts = pd.Timestamp(week_end).normalize()
    
    mask = (temp_date_col >= week_start_ts) & (temp_date_col <= week_end_ts)
    df_week = df_filtered[mask].copy()
    
    # Format the date column back to string for display
    df_week[date_col] = df_week[date_col].dt.strftime('%Y-%m-%d')
    
    print(f"  Found {len(df_week)} games.")
    return df_week


def deduplicate_tier_results(tier_results):
    """Deduplicate games and recalculate records for a list of tiers"""
    for tier in tier_results:
        if 'games' in tier and tier['games']:
            # Unique key: date, matchup, team, and the line
            seen = {}
            deduped = []
            for g in tier['games']:
                key = (g.get('date'), g.get('matchup'), g.get('team'), 
                       g.get('opening_spread') or g.get('opening_total'))
                
                # Keep the one with higher edge
                edge = float(str(g.get('edge', '0')).rstrip('%') or 0)
                if key not in seen or edge > seen[key][0]:
                    seen[key] = (edge, g)
            
            tier['games'] = [val[1] for val in seen.values()]
            
            # Recalculate record
            wins = sum(1 for g in tier['games'] if g.get('result') == 'Win')
            losses = sum(1 for g in tier['games'] if g.get('result') == 'Loss')
            total = wins + losses
            tier['wins'], tier['losses'] = wins, losses
            tier['record'] = f"{wins}-{losses}"
            tier['pct'] = f"{(wins/total*100):.1f}%" if total > 0 else "0.0%"
            
    return tier_results


def generate_game_details_html(games, bet_type='spread'):
    """Generate HTML table for individual game results"""
    if not games: return '<p>No games in this tier.</p>'
    
    def format_value(val):
        """Format a value for display, replacing NaN/None with N/A"""
        if val is None or val == '':
            return 'N/A'
        # Check for pandas/numpy NaN values
        if pd.isna(val):
            return 'N/A'
        # Check for string 'nan' (case-insensitive)
        if isinstance(val, str) and val.lower() == 'nan':
            return 'N/A'
        return str(val)
    
    mapping = {
        'spread': ('Opening Spread', 'opening_spread', 'closing_spread'),
        'total': ('Opening Total', 'opening_total', 'closing_total'),
        'moneyline': ('Opening ML', 'opening_moneyline', 'closing_moneyline')
    }
    label, op_col, cl_col = mapping.get(bet_type, ('Opening', 'opening', 'closing'))
    
    headers = ['Date', 'Matchup', 'Team', label, 'Edge', 'Closing', 'Result']
    html_str = '<table class="game-details-table"><thead><tr>'
    for h in headers: html_str += f'<th>{h}</th>'
    html_str += '</tr></thead><tbody>'
    
    for g in games:
        res = g.get('result', 'N/A')
        color = RESULT_WIN_COLOR if res == 'Win' else RESULT_LOSS_COLOR
        html_str += f"""<tr>
            <td>{html.escape(format_value(g.get('date')))}</td>
            <td>{html.escape(format_value(g.get('matchup')))}</td>
            <td>{html.escape(format_value(g.get('team')))}</td>
            <td>{html.escape(format_value(g.get(op_col)))}</td>
            <td>{html.escape(format_value(g.get('edge')))}</td>
            <td>{html.escape(format_value(g.get(cl_col)))}</td>
            <td style="color: {color}; font-weight: {RESULT_FONT_WEIGHT};">{res}</td>
        </tr>"""
    return html_str + '</tbody></table>'


def count_games_in_section(data):
    """Helper to count games across multiple tiers/subsections"""
    if isinstance(data, list):
        return sum(len(t.get('games', [])) for t in data)
    if isinstance(data, dict):
        return sum(count_games_in_section(v) for v in data.values())
    return 0


def generate_weekly_html(analysis_data, week_start_str, week_end_str, timestamp, game_count, report_type='current'):
    """Build the full HTML report string"""
    # Format dates nicely for display
    week_start_date = parse_date(week_start_str)
    week_end_date = parse_date(week_end_str)
    week_range_display = f"{week_start_date.strftime('%B %d, %Y')} - {week_end_date.strftime('%B %d, %Y')}"
    
    report_title = "Current Week" if report_type == 'current' else "Previous Week"
    
    # Count games in each section
    section1_count = count_games_in_section(analysis_data['spread_by_edge_all'])
    section2_count = count_games_in_section(analysis_data['spread_by_edge_consensus'])
    section3_count = count_games_in_section(analysis_data['spread_by_point_spread'])
    section4_count = count_games_in_section(analysis_data['ou_by_edge_all'])
    section5_count = count_games_in_section(analysis_data['ou_by_edge_consensus'])
    
    html_output = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} Model Performance - {week_start_str} to {week_end_str}</title>
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
        .report-type {{
            color: #4a5568;
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 5px;
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
            <p class="report-type">{report_title}</p>
            <p class="week-range">Week of {week_range_display}</p>
            <p class="timestamp">Generated: {html.escape(timestamp)}</p>
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
        html_output += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{html.escape(row['tier'])}</span>
                                        <span>{html.escape(row['record'])}</span>
                                        <span>{html.escape(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html_output += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>2. Model Spread Performance by Edge (Consensus Only) ({} games)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Edge Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''.format(section2_count)
    for row in analysis_data['spread_by_edge_consensus']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html_output += f'''                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details>
                                <summary>
                                    <div class="summary-content">
                                        <span>{html.escape(row['tier'])}</span>
                                        <span>{html.escape(row['record'])}</span>
                                        <span>{html.escape(row['pct'])}</span>
                                    </div>
                                </summary>
                                <div class="game-details">
                                    {games_html}
                                </div>
                            </details>
                        </td>
                    </tr>
'''
    html_output += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>3. Model Spread Performance by Point Spread Ranges ({} games)</h2>
            <div class="subsection">
                <h3>Favorites (opening_spread &lt; 0)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Point Spread Range</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''.format(section3_count)
    for row in analysis_data['spread_by_point_spread']['favorites']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='spread')
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['range'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Underdogs (opening_spread &gt; 0)</h3>
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
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['range'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>4. Model Over/Under Performance by Edge (All Games) ({} games)</h2>
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
'''.format(section4_count)
    for row in analysis_data['ou_by_edge_all']['overs']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['tier'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
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
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['tier'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>5. Model Over/Under Performance by Edge (Consensus Only) ({} games)</h2>
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
'''.format(section5_count)
    for row in analysis_data['ou_by_edge_consensus']['overs']:
        games_html = generate_game_details_html(row.get('games', []), bet_type='total')
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['tier'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
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
        html_output += f'''                        <tr>
                            <td colspan="3" style="padding: 0;">
                                <details>
                                    <summary>
                                        <div class="summary-content">
                                            <span>{html.escape(row['tier'])}</span>
                                            <span>{html.escape(row['record'])}</span>
                                            <span>{html.escape(row['pct'])}</span>
                                        </div>
                                    </summary>
                                    <div class="game-details">
                                        {games_html}
                                    </div>
                                </details>
                            </td>
                        </tr>
'''
    html_output += '''                    </tbody>
                </table>
            </div>
        </section>

        <footer>
            <p>Weekly report generated automatically by GitHub Actions</p>
        </footer>
    </div>
</body>
</html>
'''
    return html_output


def process_week(df, week_start_str, output_type):
    """Main workflow for a single week's report generation"""
    week_end = parse_date(week_start_str) + timedelta(days=6)
    week_end_str = week_end.strftime('%Y-%m-%d')
    
    html_path = CURRENT_WEEK_HTML if output_type == 'current' else PREVIOUS_WEEK_HTML
    csv_path = CURRENT_WEEK_CSV if output_type == 'current' else PREVIOUS_WEEK_CSV
    
    print(f"\n--- Processing {output_type.upper()} Week: {week_start_str} to {week_end_str} ---")
    
    df_week = filter_by_week(df, week_start_str)
    os.makedirs(WEEKLY_DIR, exist_ok=True)
    df_week.to_csv(csv_path, index=False)
    
    # Run analysis using shared functions from analyze_model_performance
    analysis = {
        'spread_by_edge_all': deduplicate_tier_results(collect_spread_performance_by_edge(df_week, False)),
        'spread_by_edge_consensus': deduplicate_tier_results(collect_spread_performance_by_edge(df_week, True)),
        'spread_by_point_spread': {
            'favorites': deduplicate_tier_results(collect_spread_performance_by_point_spread(df_week)['favorites']),
            'underdogs': deduplicate_tier_results(collect_spread_performance_by_point_spread(df_week)['underdogs'])
        },
        'ou_by_edge_all': {
            'overs': deduplicate_tier_results(collect_over_under_performance_by_edge(df_week, False)['overs']),
            'unders': deduplicate_tier_results(collect_over_under_performance_by_edge(df_week, False)['unders'])
        },
        'ou_by_edge_consensus': {
            'overs': deduplicate_tier_results(collect_over_under_performance_by_edge(df_week, True)['overs']),
            'unders': deduplicate_tier_results(collect_over_under_performance_by_edge(df_week, True)['unders'])
        }
    }
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html_content = generate_weekly_html(analysis, week_start_str, week_end_str, timestamp, len(df_week), output_type)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ {output_type.capitalize()} report saved: {html_path}")


def main():
    args = parse_arguments()
    df = fetch_graded_results_from_github()
    
    if df is None:
        print("Error: Could not load data.")
        sys.exit(1)

    # Current Week
    if args.output in ['current', 'both']:
        process_week(df, args.week_start, 'current')
    
    # Previous Week (Automatically calculate 7 days prior)
    if args.output in ['previous', 'both']:
        prev_start = (parse_date(args.week_start) - timedelta(days=7)).strftime('%Y-%m-%d')
        process_week(df, prev_start, 'previous')


if __name__ == "__main__":
    main()

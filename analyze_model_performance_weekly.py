#!/usr/bin/env python3
"""
Weekly Model Performance Analysis Script

This script:
1. Fetches graded_results.csv from trashduty/cbb repository
2. Filters data for the current week (Monday-Sunday)
3. Creates the docs/weekly/ and docs/weekly/historical/ directories
4. Generates current_week.html and current_week.csv files
5. Archives previous weeks to historical/ directory
"""

import os
import csv
import shutil
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import urllib.request
import urllib.error

# Configuration
GITHUB_RAW_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/graded_results.csv"
OUTPUT_DIR = "docs/weekly"
HISTORICAL_DIR = "docs/weekly/historical"
CURRENT_WEEK_HTML = "current_week.html"
CURRENT_WEEK_CSV = "current_week.csv"

# Date column names to check (in priority order)
POSSIBLE_DATE_COLUMNS = ['game_date', 'date', 'Date', 'GameDate']

# Date formats to try when parsing dates
DATE_FORMATS = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%m/%d/%y']


def fetch_graded_results_from_github():
    """
    Fetch graded_results.csv from the trashduty/cbb repository.
    
    Returns:
        list: List of dictionaries containing the CSV data
    """
    print(f"Fetching data from {GITHUB_RAW_URL}...")
    
    try:
        with urllib.request.urlopen(GITHUB_RAW_URL) as response:
            content = response.read().decode('utf-8')
            
        # Parse CSV content
        csv_reader = csv.DictReader(content.splitlines())
        data = list(csv_reader)
        
        print(f"Successfully fetched {len(data)} records")
        return data
    
    except urllib.error.URLError as e:
        print(f"Error fetching data: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def get_week_range(date=None):
    """
    Get the Monday-Sunday range for a given date's week.
    
    Args:
        date: datetime object (defaults to today)
        
    Returns:
        tuple: (monday_date, sunday_date) as datetime objects
    """
    if date is None:
        date = datetime.now()
    
    # Get the Monday of the week
    monday = date - timedelta(days=date.weekday())
    # Get the Sunday of the week
    sunday = monday + timedelta(days=6)
    
    # Set times to start and end of day
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return monday, sunday


def filter_data_by_week(data, week_start=None, week_end=None):
    """
    Filter data for a specific week (Monday-Sunday).
    
    Args:
        data: List of dictionaries from CSV
        week_start: Start of week (Monday) as datetime
        week_end: End of week (Sunday) as datetime
        
    Returns:
        list: Filtered data for the specified week
    """
    if week_start is None or week_end is None:
        week_start, week_end = get_week_range()
    
    print(f"Filtering data for week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    
    # Try to find the date column from the first row
    date_column_found = None
    
    if data:
        for col_name in POSSIBLE_DATE_COLUMNS:
            col_value = data[0].get(col_name, '')
            # Check if the column exists and has a non-empty string value
            if col_value and str(col_value).strip():
                date_column_found = col_name
                print(f"Using date column: '{date_column_found}'")
                break
    
    if not date_column_found:
        print("Warning: No recognized date column found in data")
        return []
    
    filtered_data = []
    skipped_rows = 0
    
    for row in data:
        try:
            # Parse the date field
            game_date_str = row.get(date_column_found, '')
            if not game_date_str:
                skipped_rows += 1
                continue
            
            # Try different date formats
            game_date = None
            for fmt in DATE_FORMATS:
                try:
                    game_date = datetime.strptime(game_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if game_date is None:
                skipped_rows += 1
                continue
            
            # Check if date is in the week range
            if week_start <= game_date <= week_end:
                filtered_data.append(row)
        
        except Exception as e:
            print(f"Error processing row: {e}")
            skipped_rows += 1
            continue
    
    print(f"Found {len(filtered_data)} records for the current week (skipped {skipped_rows} rows)")
    return filtered_data


def collect_spread_performance_by_edge(data):
    """
    Collect spread performance statistics grouped by edge bucket.
    
    Args:
        data: List of dictionaries from filtered CSV
        
    Returns:
        dict: Performance statistics by edge bucket
    """
    # Edge buckets
    edge_buckets = [
        (0, 2, "0-2"),
        (2, 4, "2-4"),
        (4, 6, "4-6"),
        (6, 8, "6-8"),
        (8, 10, "8-10"),
        (10, float('inf'), "10+")
    ]
    
    performance = defaultdict(lambda: {
        'total': 0,
        'correct': 0,
        'win_rate': 0.0,
        'edge_range': ''
    })
    
    for row in data:
        try:
            edge = float(row.get('edge', 0))
            result = row.get('result', '').strip().lower()
            
            # Determine which bucket this edge falls into
            for min_edge, max_edge, label in edge_buckets:
                if min_edge <= abs(edge) < max_edge:
                    performance[label]['total'] += 1
                    performance[label]['edge_range'] = label
                    
                    if result in ['correct', 'win', 'w', '1']:
                        performance[label]['correct'] += 1
                    
                    break
        
        except (ValueError, TypeError):
            continue
    
    # Calculate win rates
    for label in performance:
        if performance[label]['total'] > 0:
            performance[label]['win_rate'] = (
                performance[label]['correct'] / performance[label]['total']
            ) * 100
    
    return dict(performance)


def collect_overall_statistics(data):
    """
    Collect overall performance statistics.
    
    Args:
        data: List of dictionaries from filtered CSV
        
    Returns:
        dict: Overall statistics
    """
    total_games = len(data)
    correct = 0
    total_edge = 0.0
    
    for row in data:
        try:
            result = row.get('result', '').strip().lower()
            if result in ['correct', 'win', 'w', '1']:
                correct += 1
            
            edge = float(row.get('edge', 0))
            total_edge += abs(edge)
        
        except (ValueError, TypeError):
            continue
    
    win_rate = (correct / total_games * 100) if total_games > 0 else 0.0
    avg_edge = (total_edge / total_games) if total_games > 0 else 0.0
    
    return {
        'total_games': total_games,
        'correct': correct,
        'incorrect': total_games - correct,
        'win_rate': win_rate,
        'avg_edge': avg_edge
    }


def generate_weekly_html(data, week_start, week_end, output_path):
    """
    Generate HTML report for weekly performance.
    
    Args:
        data: List of dictionaries from filtered CSV
        week_start: Start of week as datetime
        week_end: End of week as datetime
        output_path: Path to save the HTML file
    """
    overall_stats = collect_overall_statistics(data)
    spread_performance = collect_spread_performance_by_edge(data)
    
    # Sort edge buckets
    edge_order = ["0-2", "2-4", "4-6", "6-8", "8-10", "10+"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Model Performance - {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        h1, h2 {{
            color: #333;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            margin: 0;
            color: white;
        }}
        
        .week-range {{
            font-size: 1.2em;
            margin-top: 10px;
            opacity: 0.9;
        }}
        
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background-color: #667eea;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .win-rate-good {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .win-rate-bad {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Weekly Model Performance Report</h1>
        <div class="week-range">
            Week of {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}
        </div>
    </div>
    
    <div class="stats-container">
        <div class="stat-card">
            <h3>Total Games</h3>
            <div class="stat-value">{overall_stats['total_games']}</div>
        </div>
        <div class="stat-card">
            <h3>Win Rate</h3>
            <div class="stat-value">{overall_stats['win_rate']:.1f}%</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {overall_stats['win_rate']:.1f}%"></div>
            </div>
        </div>
        <div class="stat-card">
            <h3>Correct Predictions</h3>
            <div class="stat-value">{overall_stats['correct']}</div>
        </div>
        <div class="stat-card">
            <h3>Average Edge</h3>
            <div class="stat-value">{overall_stats['avg_edge']:.2f}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Spread Performance by Edge</h2>
        <table>
            <thead>
                <tr>
                    <th>Edge Range</th>
                    <th>Total Games</th>
                    <th>Correct</th>
                    <th>Incorrect</th>
                    <th>Win Rate</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add rows for each edge bucket
    for edge_label in edge_order:
        if edge_label in spread_performance:
            perf = spread_performance[edge_label]
            incorrect = perf['total'] - perf['correct']
            win_rate_class = 'win-rate-good' if perf['win_rate'] >= 52.4 else 'win-rate-bad'
            
            html_content += f"""                <tr>
                    <td><strong>{edge_label}</strong></td>
                    <td>{perf['total']}</td>
                    <td>{perf['correct']}</td>
                    <td>{incorrect}</td>
                    <td class="{win_rate_class}">{perf['win_rate']:.1f}%</td>
                </tr>
"""
    
    html_content += """            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
        <p>Data source: trashduty/cbb/graded_results.csv</p>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated HTML report: {output_path}")


def generate_weekly_csv(data, output_path):
    """
    Generate CSV file for weekly data.
    
    Args:
        data: List of dictionaries from filtered CSV
        output_path: Path to save the CSV file
    """
    if not data:
        print("No data to write to CSV")
        return
    
    # Get all unique field names from the data
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated CSV file: {output_path}")


def archive_previous_week():
    """
    Archive previous week's files to the historical directory.
    """
    current_week_html_path = os.path.join(OUTPUT_DIR, CURRENT_WEEK_HTML)
    current_week_csv_path = os.path.join(OUTPUT_DIR, CURRENT_WEEK_CSV)
    
    # Check if current week files exist
    if not os.path.exists(current_week_html_path):
        print("No previous week files to archive")
        return
    
    # Get the previous week's date range from the HTML file
    # For simplicity, use the file's modification time
    try:
        file_mtime = os.path.getmtime(current_week_html_path)
        file_date = datetime.fromtimestamp(file_mtime)
        week_start, week_end = get_week_range(file_date)
        
        # Create archive filename
        archive_prefix = f"{week_start.strftime('%Y-%m-%d')}_to_{week_end.strftime('%Y-%m-%d')}"
        
        # Ensure historical directory exists
        os.makedirs(HISTORICAL_DIR, exist_ok=True)
        
        # Move files to historical directory
        if os.path.exists(current_week_html_path):
            archive_html_path = os.path.join(HISTORICAL_DIR, f"{archive_prefix}.html")
            shutil.move(current_week_html_path, archive_html_path)
            print(f"Archived HTML to: {archive_html_path}")
        
        if os.path.exists(current_week_csv_path):
            archive_csv_path = os.path.join(HISTORICAL_DIR, f"{archive_prefix}.csv")
            shutil.move(current_week_csv_path, archive_csv_path)
            print(f"Archived CSV to: {archive_csv_path}")
    
    except Exception as e:
        print(f"Error archiving previous week: {e}")


def ensure_directories():
    """
    Ensure required directories exist.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(HISTORICAL_DIR, exist_ok=True)
    print(f"Ensured directories exist: {OUTPUT_DIR}, {HISTORICAL_DIR}")


def main():
    """
    Main execution function.
    """
    print("=" * 60)
    print("Weekly Model Performance Analysis")
    print("=" * 60)
    print()
    
    # Step 1: Ensure directories exist
    ensure_directories()
    
    # Step 2: Fetch data from GitHub
    all_data = fetch_graded_results_from_github()
    
    if not all_data:
        print("Error: No data fetched. Exiting.")
        return
    
    # Step 3: Get current week range
    week_start, week_end = get_week_range()
    print(f"\nCurrent week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    
    # Step 4: Filter data for current week
    weekly_data = filter_data_by_week(all_data, week_start, week_end)
    
    if not weekly_data:
        print("ERROR: No data found for the current week. Exiting with error status.")
        print(f"Week range: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        print(f"Total records in source data: {len(all_data)}")
        sys.exit(1)
    
    # Step 5: Archive previous week's files
    print("\nArchiving previous week's files...")
    archive_previous_week()
    
    # Step 6: Generate current week's HTML report
    print("\nGenerating current week's reports...")
    html_output_path = os.path.join(OUTPUT_DIR, CURRENT_WEEK_HTML)
    generate_weekly_html(weekly_data, week_start, week_end, html_output_path)
    
    # Step 7: Generate current week's CSV file
    csv_output_path = os.path.join(OUTPUT_DIR, CURRENT_WEEK_CSV)
    generate_weekly_csv(weekly_data, csv_output_path)
    
    print()
    print("=" * 60)
    print("Weekly analysis complete!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  - {html_output_path}")
    print(f"  - {csv_output_path}")
    print(f"\nHistorical files: {HISTORICAL_DIR}")


if __name__ == "__main__":
    main()

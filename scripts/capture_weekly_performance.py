#!/usr/bin/env python3
"""
Capture weekly model performance for tracking betting edges.

This script fetches CBB_Output.csv, applies threshold checks, and saves
qualifying games to weekly CSV files for performance tracking.
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from io import StringIO
import requests

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PERFORMANCE_DIR = os.path.join(PROJECT_ROOT, 'performance_tracking')
CAPTURED_EDGES_FILE = os.path.join(PROJECT_ROOT, 'captured_edges.json')

# CSV source
CBB_OUTPUT_URL = 'https://raw.githubusercontent.com/trashduty/cbb/main/CBB_Output.csv'

# Thresholds
SPREAD_THRESHOLD = 0.01  # 1%
TOTAL_THRESHOLD = 0.01   # 1%
MONEYLINE_THRESHOLD = 0.50  # 50%

# Capture window (in hours from Opening Odds Time)
CAPTURE_WINDOW_HOURS = 2


def load_captured_edges():
    """Load the set of previously captured edges."""
    if not os.path.exists(CAPTURED_EDGES_FILE):
        return {}
    
    try:
        with open(CAPTURED_EDGES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load captured edges: {e}")
        return {}


def save_captured_edges(captured_edges):
    """Save the set of captured edges."""
    try:
        with open(CAPTURED_EDGES_FILE, 'w') as f:
            json.dump(captured_edges, f, indent=2)
        print(f"Updated {CAPTURED_EDGES_FILE}")
    except Exception as e:
        print(f"Error saving captured edges: {e}")


def create_game_team_id(row, edge_type):
    """Create unique identifier for game-team-edge combination (for spreads/ML)."""
    return f"{row['Game']}|{row['Team']}|{edge_type}"


def create_game_id(row, edge_type):
    """Create unique identifier for game-edge combination (for totals)."""
    return f"{row['Game']}|{edge_type}"


def parse_opening_odds_time(opening_time_str):
    """Parse Opening Odds Time string to datetime object."""
    if pd.isna(opening_time_str) or opening_time_str == "N/A":
        return None
    
    try:
        # Format: "2025-12-26 18:25:07 UTC"
        dt_utc = datetime.strptime(opening_time_str, "%Y-%m-%d %H:%M:%S UTC")
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc
    except Exception as e:
        print(f"Warning: Could not parse opening odds time '{opening_time_str}': {e}")
        return None


def is_within_capture_window(opening_time_str):
    """Check if current time is within capture window from opening odds time."""
    opening_time = parse_opening_odds_time(opening_time_str)
    if opening_time is None:
        return False
    
    now = datetime.now(timezone.utc)
    time_since_opening = now - opening_time
    hours_since_opening = time_since_opening.total_seconds() / 3600
    
    # Don't capture if opening time is in the future
    if hours_since_opening < 0:
        return False
    
    # Don't capture if more than CAPTURE_WINDOW_HOURS have passed
    if hours_since_opening > CAPTURE_WINDOW_HOURS:
        return False
    
    return True


def get_iso_week_string(dt):
    """Get ISO week string in format YYYY_Www (e.g., 2025_W52)."""
    iso_calendar = dt.isocalendar()
    return f"{iso_calendar.year}_W{iso_calendar.week:02d}"


def fetch_cbb_data():
    """Fetch CBB_Output.csv from GitHub."""
    print(f"Fetching data from {CBB_OUTPUT_URL}...")
    try:
        response = requests.get(CBB_OUTPUT_URL)
        response.raise_for_status()
        
        # Read CSV directly from response text
        df = pd.read_csv(StringIO(response.text))
        print(f"Loaded {len(df)} rows from CSV")
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)


def capture_edges():
    """Main function to capture qualifying edges and save to weekly CSV files."""
    print("=" * 60)
    print("Weekly Performance Capture")
    print("=" * 60)
    
    # Create performance directory if it doesn't exist
    os.makedirs(PERFORMANCE_DIR, exist_ok=True)
    
    # Load previously captured edges
    captured_edges = load_captured_edges()
    print(f"Previously captured: {len(captured_edges)} edge opportunities")
    
    # Fetch data
    df = fetch_cbb_data()
    
    # Track new captures
    new_captures = []
    new_captured_ids = {}
    
    # Process each row
    for idx, row in df.iterrows():
        # Check if within capture window
        if not is_within_capture_window(row.get('Opening Odds Time')):
            continue
        
        # Check Spread Edge
        if (pd.notna(row.get('Edge For Covering Spread')) and 
            row['Edge For Covering Spread'] >= SPREAD_THRESHOLD):
            
            game_id = create_game_team_id(row, 'spread')
            
            # Only capture if not already captured (check both persistent and current session)
            if game_id not in captured_edges and game_id not in new_captured_ids:
                capture_record = {
                    'Capture Time': datetime.now(timezone.utc).isoformat(),
                    'Game': row['Game'],
                    'Team': row['Team'],
                    'Game Time': row['Game Time'],
                    'Opening Odds Time': row.get('Opening Odds Time', 'N/A'),
                    'Edge Type': 'Spread',
                    'Edge Value': row['Edge For Covering Spread'],
                    'Predicted Outcome': row.get('Predicted Outcome', 'N/A'),
                    'Probability': row.get('Spread Cover Probability', 'N/A'),
                    'Opening Line': row.get('Opening Spread', 'N/A'),
                    'Current Line': row.get('market_spread', 'N/A'),
                    'Model Projection': row.get('model_spread', 'N/A')
                }
                new_captures.append(capture_record)
                new_captured_ids[game_id] = {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'edge_type': 'spread'
                }
                print(f"✓ Captured spread edge: {row['Team']} ({row['Edge For Covering Spread']:.2%})")
        
        # Check Moneyline Edge (using win probability >= 50%)
        if (pd.notna(row.get('Moneyline Win Probability')) and 
            row['Moneyline Win Probability'] >= MONEYLINE_THRESHOLD):
            
            game_id = create_game_team_id(row, 'moneyline')
            
            # Only capture if not already captured (check both persistent and current session)
            if game_id not in captured_edges and game_id not in new_captured_ids:
                capture_record = {
                    'Capture Time': datetime.now(timezone.utc).isoformat(),
                    'Game': row['Game'],
                    'Team': row['Team'],
                    'Game Time': row['Game Time'],
                    'Opening Odds Time': row.get('Opening Odds Time', 'N/A'),
                    'Edge Type': 'Moneyline',
                    'Edge Value': row.get('Moneyline Edge', 'N/A'),
                    'Predicted Outcome': 'Win',
                    'Probability': row['Moneyline Win Probability'],
                    'Opening Line': row.get('Opening Moneyline', 'N/A'),
                    'Current Line': row.get('Current Moneyline', 'N/A'),
                    'Model Projection': row.get('Moneyline Win Probability', 'N/A')
                }
                new_captures.append(capture_record)
                new_captured_ids[game_id] = {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'edge_type': 'moneyline'
                }
                print(f"✓ Captured moneyline edge: {row['Team']} ({row['Moneyline Win Probability']:.2%})")
        
        # Check Over Total Edge
        if (pd.notna(row.get('Over Total Edge')) and 
            row['Over Total Edge'] >= TOTAL_THRESHOLD):
            
            game_id = create_game_id(row, 'over')
            
            # Only capture if not already captured (check both persistent and current session)
            if game_id not in captured_edges and game_id not in new_captured_ids:
                capture_record = {
                    'Capture Time': datetime.now(timezone.utc).isoformat(),
                    'Game': row['Game'],
                    'Team': 'N/A',  # Totals are not team-specific
                    'Game Time': row['Game Time'],
                    'Opening Odds Time': row.get('Opening Odds Time', 'N/A'),
                    'Edge Type': 'Over',
                    'Edge Value': row['Over Total Edge'],
                    'Predicted Outcome': 'Over',
                    'Probability': row.get('Over Cover Probability', 'N/A'),
                    'Opening Line': row.get('Opening Total', 'N/A'),
                    'Current Line': row.get('market_total', 'N/A'),
                    'Model Projection': row.get('model_total', 'N/A')
                }
                new_captures.append(capture_record)
                new_captured_ids[game_id] = {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'edge_type': 'over'
                }
                print(f"✓ Captured over edge: {row['Game']} ({row['Over Total Edge']:.2%})")
        
        # Check Under Total Edge
        if (pd.notna(row.get('Under Total Edge')) and 
            row['Under Total Edge'] >= TOTAL_THRESHOLD):
            
            game_id = create_game_id(row, 'under')
            
            # Only capture if not already captured (check both persistent and current session)
            if game_id not in captured_edges and game_id not in new_captured_ids:
                capture_record = {
                    'Capture Time': datetime.now(timezone.utc).isoformat(),
                    'Game': row['Game'],
                    'Team': 'N/A',  # Totals are not team-specific
                    'Game Time': row['Game Time'],
                    'Opening Odds Time': row.get('Opening Odds Time', 'N/A'),
                    'Edge Type': 'Under',
                    'Edge Value': row['Under Total Edge'],
                    'Predicted Outcome': 'Under',
                    'Probability': row.get('Under Cover Probability', 'N/A'),
                    'Opening Line': row.get('Opening Total', 'N/A'),
                    'Current Line': row.get('market_total', 'N/A'),
                    'Model Projection': row.get('model_total', 'N/A')
                }
                new_captures.append(capture_record)
                new_captured_ids[game_id] = {
                    'captured_at': datetime.now(timezone.utc).isoformat(),
                    'edge_type': 'under'
                }
                print(f"✓ Captured under edge: {row['Game']} ({row['Under Total Edge']:.2%})")
    
    # Save new captures to weekly CSV files
    if new_captures:
        # Group captures by ISO week
        captures_by_week = {}
        for capture in new_captures:
            # Parse capture time to get ISO week
            # The isoformat() method produces strings that fromisoformat() can parse
            capture_time = datetime.fromisoformat(capture['Capture Time'])
            week_string = get_iso_week_string(capture_time)
            
            if week_string not in captures_by_week:
                captures_by_week[week_string] = []
            captures_by_week[week_string].append(capture)
        
        # Write each week's captures to its CSV file
        for week_string, week_captures in captures_by_week.items():
            csv_filename = os.path.join(PERFORMANCE_DIR, f'weekly_performance_{week_string}.csv')
            
            # Check if file exists to determine if we need to write header
            file_exists = os.path.exists(csv_filename)
            
            # Convert to DataFrame and append to CSV
            df_captures = pd.DataFrame(week_captures)
            
            # Append to existing file or create new one
            df_captures.to_csv(
                csv_filename,
                mode='a' if file_exists else 'w',
                header=not file_exists,
                index=False
            )
            
            print(f"📝 Saved {len(week_captures)} captures to {csv_filename}")
        
        # Update captured edges tracker
        captured_edges.update(new_captured_ids)
        save_captured_edges(captured_edges)
    
    # Summary
    print("=" * 60)
    print(f"Summary:")
    print(f"  - Rows checked: {len(df)}")
    print(f"  - New captures: {len(new_captures)}")
    print(f"  - Total tracked edges: {len(captured_edges)}")
    print("=" * 60)
    
    return len(new_captures)


if __name__ == "__main__":
    try:
        new_captures = capture_edges()
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

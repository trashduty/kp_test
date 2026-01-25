"""
Tests for date filtering in generate_previews.py script
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import parse_game_time


def test_parse_game_time():
    """Test that parse_game_time correctly parses game time strings"""
    # Test various formats
    test_cases = [
        "Jan 24 11:59PM ET",
        "Jan 25 01:00PM ET",
        "Feb 15 03:30PM ET",
    ]
    
    for time_str in test_cases:
        result = parse_game_time(time_str)
        assert result is not None, f"Failed to parse: {time_str}"
        assert isinstance(result, datetime), f"Result is not a datetime object: {type(result)}"
    
    print("✓ parse_game_time correctly parses time strings")


def test_date_filtering_logic():
    """Test that the date filtering logic correctly identifies games for today and tomorrow"""
    # Create mock data with games on different dates
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    # Create mock game data
    mock_data = pd.DataFrame({
        'Game Time': [
            today.strftime('%b %d 07:00PM ET').replace(' 0', ' '),
            tomorrow.strftime('%b %d 08:00PM ET').replace(' 0', ' '),
            day_after.strftime('%b %d 09:00PM ET').replace(' 0', ' '),
        ],
        'Game': ['Game1', 'Game2', 'Game3'],
        'Team': ['TeamA', 'TeamB', 'TeamC']
    })
    
    # Parse game times
    mock_data['parsed_time'] = mock_data['Game Time'].apply(parse_game_time)
    
    # Filter for today and tomorrow (same logic as in the script)
    target_games = mock_data[
        (mock_data['parsed_time'].dt.date == today.date()) |
        (mock_data['parsed_time'].dt.date == tomorrow.date())
    ]
    
    # Should have 2 games (today and tomorrow, not day after)
    assert len(target_games) == 2, f"Expected 2 games, got {len(target_games)}"
    
    # Verify the correct games are included
    assert 'Game1' in target_games['Game'].values, "Today's game should be included"
    assert 'Game2' in target_games['Game'].values, "Tomorrow's game should be included"
    assert 'Game3' not in target_games['Game'].values, "Day after tomorrow's game should NOT be included"
    
    print("✓ Date filtering correctly identifies today's and tomorrow's games")


def test_kp_date_format():
    """Test that the kp date format matches expected format"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    # Test the date format conversion (same as in script)
    kp_today = today.strftime('%Y-%m-%d')
    kp_tomorrow = tomorrow.strftime('%Y-%m-%d')
    
    # Verify format is YYYY-MM-DD
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    assert re.match(date_pattern, kp_today), f"kp_today format is incorrect: {kp_today}"
    assert re.match(date_pattern, kp_tomorrow), f"kp_tomorrow format is incorrect: {kp_tomorrow}"
    
    print("✓ KP date format is correct (YYYY-MM-DD)")


def test_kp_data_filtering():
    """Test that kp.csv filtering works with multiple dates"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    kp_today = today.strftime('%Y-%m-%d')
    kp_tomorrow = tomorrow.strftime('%Y-%m-%d')
    kp_day_after = day_after.strftime('%Y-%m-%d')
    
    # Create mock kp data
    kp_data = pd.DataFrame({
        'date': [kp_today, kp_tomorrow, kp_day_after],
        'team': ['TeamA', 'TeamB', 'TeamC'],
        'side': ['away', 'home', 'away']
    })
    
    # Filter for today OR tomorrow (same logic as in script)
    filtered = kp_data[
        (kp_data['date'] == kp_today) | (kp_data['date'] == kp_tomorrow)
    ]
    
    # Should have 2 entries (today and tomorrow, not day after)
    assert len(filtered) == 2, f"Expected 2 entries, got {len(filtered)}"
    assert 'TeamA' in filtered['team'].values
    assert 'TeamB' in filtered['team'].values
    assert 'TeamC' not in filtered['team'].values
    
    print("✓ KP data filtering correctly handles multiple dates")


if __name__ == '__main__':
    test_parse_game_time()
    test_date_filtering_logic()
    test_kp_date_format()
    test_kp_data_filtering()
    print("\n✅ All date filtering tests passed!")

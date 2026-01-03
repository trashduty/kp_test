"""
Test to verify game counts are properly calculated and displayed in section titles.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import functions we need to test
from scripts.generate_weekly_report import count_games_in_section


def test_count_games_in_section():
    """Test that count_games_in_section works correctly"""
    
    print("=" * 80)
    print("Test: count_games_in_section function")
    print("=" * 80)
    
    # Test with a list of tier results (like spread_by_edge_all)
    list_data = [
        {'tier': '0-0.9%', 'record': '2-1', 'pct': '66.7%', 'games': [{'game': 1}, {'game': 2}, {'game': 3}]},
        {'tier': '1-1.9%', 'record': '1-1', 'pct': '50.0%', 'games': [{'game': 4}, {'game': 5}]},
        {'tier': '2-2.9%', 'record': '0-0', 'pct': '0.0%', 'games': []},
    ]
    
    count = count_games_in_section(list_data)
    print(f"List data count: {count}")
    assert count == 5, f"Expected 5 games, got {count}"
    print("✓ List data count is correct (5 games)")
    
    # Test with a dict structure (like spread_by_point_spread)
    dict_data = {
        'favorites': [
            {'range': '0-4.5', 'record': '1-0', 'pct': '100.0%', 'games': [{'game': 1}]},
            {'range': '5-9.5', 'record': '2-1', 'pct': '66.7%', 'games': [{'game': 2}, {'game': 3}, {'game': 4}]},
        ],
        'underdogs': [
            {'range': '0-4.5', 'record': '0-2', 'pct': '0.0%', 'games': [{'game': 5}, {'game': 6}]},
        ]
    }
    
    count = count_games_in_section(dict_data)
    print(f"Dict data count: {count}")
    assert count == 6, f"Expected 6 games, got {count}"
    print("✓ Dict data count is correct (6 games)")
    
    # Test with a dict structure with different keys (like ou_by_edge_all)
    dict_data2 = {
        'overs': [
            {'tier': '0-0.9%', 'record': '3-2', 'pct': '60.0%', 'games': [{'game': 1}, {'game': 2}, {'game': 3}, {'game': 4}, {'game': 5}]},
        ],
        'unders': [
            {'tier': '0-0.9%', 'record': '1-1', 'pct': '50.0%', 'games': [{'game': 6}, {'game': 7}]},
        ]
    }
    
    count = count_games_in_section(dict_data2)
    print(f"Dict data (overs/unders) count: {count}")
    assert count == 7, f"Expected 7 games, got {count}"
    print("✓ Dict data (overs/unders) count is correct (7 games)")
    
    # Test with empty data
    empty_list = []
    count = count_games_in_section(empty_list)
    print(f"Empty list count: {count}")
    assert count == 0, f"Expected 0 games, got {count}"
    print("✓ Empty list count is correct (0 games)")
    
    print()
    print("=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ count_games_in_section correctly counts games in list structures")
    print("  ✓ count_games_in_section correctly counts games in dict structures")
    print("  ✓ count_games_in_section handles empty data")


if __name__ == "__main__":
    try:
        test_count_games_in_section()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

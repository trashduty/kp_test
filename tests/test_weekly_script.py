"""
Test to verify the analyze_model_performance_weekly.py script handles
different date column names and formats correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to Python path to import the module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the functions we want to test
from analyze_model_performance_weekly import filter_data_by_week, get_week_range


def test_filter_with_date_column():
    """Test filtering with 'date' column name (most common)"""
    print("=" * 80)
    print("Test 1: Filter data with 'date' column")
    print("=" * 80)
    
    # Get current week range
    week_start, week_end = get_week_range()
    
    # Create test data with 'date' column (like the actual data)
    test_data = [
        {'date': week_start.strftime('%Y-%m-%d'), 'edge': 5.0, 'result': 'correct'},
        {'date': (week_start + timedelta(days=1)).strftime('%Y-%m-%d'), 'edge': 3.0, 'result': 'incorrect'},
        {'date': (week_start - timedelta(days=7)).strftime('%Y-%m-%d'), 'edge': 2.0, 'result': 'correct'},  # Previous week
        {'date': (week_end + timedelta(days=1)).strftime('%Y-%m-%d'), 'edge': 4.0, 'result': 'correct'},  # Next week
    ]
    
    filtered = filter_data_by_week(test_data, week_start, week_end)
    
    # Should find 2 records (first two are within the week)
    assert len(filtered) == 2, f"Expected 2 records, got {len(filtered)}"
    print(f"✓ Correctly filtered {len(filtered)} records with 'date' column")
    print()
    return True


def test_filter_with_game_date_column():
    """Test filtering with 'game_date' column name"""
    print("=" * 80)
    print("Test 2: Filter data with 'game_date' column")
    print("=" * 80)
    
    week_start, week_end = get_week_range()
    
    # Create test data with 'game_date' column
    test_data = [
        {'game_date': week_start.strftime('%Y-%m-%d'), 'edge': 5.0, 'result': 'correct'},
        {'game_date': (week_start + timedelta(days=2)).strftime('%Y-%m-%d'), 'edge': 3.0, 'result': 'incorrect'},
    ]
    
    filtered = filter_data_by_week(test_data, week_start, week_end)
    
    # Should find 2 records
    assert len(filtered) == 2, f"Expected 2 records, got {len(filtered)}"
    print(f"✓ Correctly filtered {len(filtered)} records with 'game_date' column")
    print()
    return True


def test_multiple_date_formats():
    """Test filtering with different date formats"""
    print("=" * 80)
    print("Test 3: Filter data with multiple date formats")
    print("=" * 80)
    
    week_start, week_end = get_week_range()
    
    # Create test data with different date formats
    test_data = [
        {'date': week_start.strftime('%Y-%m-%d'), 'edge': 5.0},  # YYYY-MM-DD
        {'date': (week_start + timedelta(days=1)).strftime('%m/%d/%Y'), 'edge': 3.0},  # MM/DD/YYYY
        {'date': (week_start + timedelta(days=2)).strftime('%Y/%m/%d'), 'edge': 4.0},  # YYYY/MM/DD
        {'date': (week_start + timedelta(days=3)).strftime('%m/%d/%y'), 'edge': 2.0},  # MM/DD/YY (2-digit year)
    ]
    
    filtered = filter_data_by_week(test_data, week_start, week_end)
    
    # Should find all 4 records
    assert len(filtered) == 4, f"Expected 4 records, got {len(filtered)}"
    print(f"✓ Correctly filtered {len(filtered)} records with multiple date formats")
    print()
    return True


def test_empty_data():
    """Test filtering with no matching data"""
    print("=" * 80)
    print("Test 4: Filter data with no matches (future week)")
    print("=" * 80)
    
    # Use a future week
    future_start = datetime.now() + timedelta(days=365)
    future_end = future_start + timedelta(days=6)
    
    # Create test data with current dates
    week_start, week_end = get_week_range()
    test_data = [
        {'date': week_start.strftime('%Y-%m-%d'), 'edge': 5.0, 'result': 'correct'},
        {'date': (week_start + timedelta(days=1)).strftime('%Y-%m-%d'), 'edge': 3.0, 'result': 'incorrect'},
    ]
    
    filtered = filter_data_by_week(test_data, future_start, future_end)
    
    # Should find 0 records
    assert len(filtered) == 0, f"Expected 0 records, got {len(filtered)}"
    print(f"✓ Correctly filtered {len(filtered)} records (empty result)")
    print()
    return True


def test_missing_date_column():
    """Test filtering with missing date columns"""
    print("=" * 80)
    print("Test 5: Filter data with missing date columns")
    print("=" * 80)
    
    week_start, week_end = get_week_range()
    
    # Create test data without any date columns
    test_data = [
        {'edge': 5.0, 'result': 'correct'},
        {'edge': 3.0, 'result': 'incorrect'},
    ]
    
    filtered = filter_data_by_week(test_data, week_start, week_end)
    
    # Should find 0 records
    assert len(filtered) == 0, f"Expected 0 records, got {len(filtered)}"
    print(f"✓ Correctly handled missing date columns ({len(filtered)} records)")
    print()
    return True


def test_case_sensitive_columns():
    """Test filtering with different case variations of date columns"""
    print("=" * 80)
    print("Test 6: Filter data with case variations (Date, GameDate)")
    print("=" * 80)
    
    week_start, week_end = get_week_range()
    
    # Create test data with 'Date' (capitalized)
    test_data1 = [
        {'Date': week_start.strftime('%Y-%m-%d'), 'edge': 5.0},
    ]
    
    filtered1 = filter_data_by_week(test_data1, week_start, week_end)
    assert len(filtered1) == 1, f"Expected 1 record with 'Date', got {len(filtered1)}"
    print(f"✓ Correctly filtered {len(filtered1)} records with 'Date' column")
    
    # Create test data with 'GameDate'
    test_data2 = [
        {'GameDate': week_start.strftime('%Y-%m-%d'), 'edge': 5.0},
    ]
    
    filtered2 = filter_data_by_week(test_data2, week_start, week_end)
    assert len(filtered2) == 1, f"Expected 1 record with 'GameDate', got {len(filtered2)}"
    print(f"✓ Correctly filtered {len(filtered2)} records with 'GameDate' column")
    print()
    return True


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("Testing Weekly Script Date Column and Format Handling")
    print("=" * 80)
    print()
    
    tests = [
        test_filter_with_date_column,
        test_filter_with_game_date_column,
        test_multiple_date_formats,
        test_empty_data,
        test_missing_date_column,
        test_case_sensitive_columns,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 80)
    if all(results):
        print(f"✓ All {len(results)} tests passed!")
        print("=" * 80)
        print()
        print("Verification Summary:")
        print("  ✓ Multiple date column names are supported (date, game_date, Date, GameDate)")
        print("  ✓ Multiple date formats are supported (YYYY-MM-DD, MM/DD/YYYY, YYYY/MM/DD, MM/DD/YY)")
        print("  ✓ Empty results are handled correctly")
        print("  ✓ Missing date columns are handled gracefully")
        print("  ✓ Date filtering works correctly for week ranges")
        return 0
    else:
        print(f"✗ {len([r for r in results if not r])} out of {len(results)} tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

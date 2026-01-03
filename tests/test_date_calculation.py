"""
Test to verify the date calculation logic for the weekly report matches
the GitHub Actions workflow implementation.
"""

import sys
from datetime import datetime, timedelta


def calculate_monday_of_current_week(test_date=None):
    """
    Calculate the Monday of the current week using the same logic as the workflow.
    
    Args:
        test_date: Optional datetime object for testing. If None, uses current date.
    
    Returns:
        datetime object representing Monday of the week
    """
    today = test_date if test_date else datetime.now()
    # Calculate days since Monday (0=Monday, 6=Sunday)
    days_since_monday = today.weekday()
    # Subtract those days to get to Monday
    monday = today - timedelta(days=days_since_monday)
    return monday


def test_monday_calculation():
    """Test that Monday calculation works correctly for various days of the week"""
    print("=" * 80)
    print("Test 1: Monday calculation for different days of the week")
    print("=" * 80)
    
    # Test for a Monday (should return the same date)
    monday_date = datetime(2025, 12, 29)  # This is a Monday
    result = calculate_monday_of_current_week(monday_date)
    assert result.date() == monday_date.date(), f"Monday test failed: expected {monday_date.date()}, got {result.date()}"
    print(f"✓ Monday (2025-12-29): Returns {result.strftime('%Y-%m-%d')} (same day)")
    
    # Test for a Tuesday
    tuesday_date = datetime(2025, 12, 30)  # Tuesday
    result = calculate_monday_of_current_week(tuesday_date)
    assert result.date() == monday_date.date(), f"Tuesday test failed: expected {monday_date.date()}, got {result.date()}"
    print(f"✓ Tuesday (2025-12-30): Returns {result.strftime('%Y-%m-%d')} (previous Monday)")
    
    # Test for a Friday (current date scenario)
    friday_date = datetime(2026, 1, 2)  # Friday
    result = calculate_monday_of_current_week(friday_date)
    assert result.date() == monday_date.date(), f"Friday test failed: expected {monday_date.date()}, got {result.date()}"
    print(f"✓ Friday (2026-01-02): Returns {result.strftime('%Y-%m-%d')} (previous Monday)")
    
    # Test for a Saturday (today's scenario)
    saturday_date = datetime(2026, 1, 3)  # Saturday
    result = calculate_monday_of_current_week(saturday_date)
    assert result.date() == monday_date.date(), f"Saturday test failed: expected {monday_date.date()}, got {result.date()}"
    print(f"✓ Saturday (2026-01-03): Returns {result.strftime('%Y-%m-%d')} (previous Monday)")
    
    # Test for a Sunday
    sunday_date = datetime(2026, 1, 4)  # Sunday
    result = calculate_monday_of_current_week(sunday_date)
    assert result.date() == monday_date.date(), f"Sunday test failed: expected {monday_date.date()}, got {result.date()}"
    print(f"✓ Sunday (2026-01-04): Returns {result.strftime('%Y-%m-%d')} (previous Monday)")
    
    print()
    return True


def test_next_week_calculation():
    """Test that the calculation automatically switches to next week on Monday"""
    print("=" * 80)
    print("Test 2: Next week Monday calculation")
    print("=" * 80)
    
    # Test for next Monday (should return a different week)
    next_monday = datetime(2026, 1, 5)  # Next Monday
    result = calculate_monday_of_current_week(next_monday)
    expected = datetime(2026, 1, 5)
    assert result.date() == expected.date(), f"Next Monday test failed: expected {expected.date()}, got {result.date()}"
    print(f"✓ Next Monday (2026-01-05): Returns {result.strftime('%Y-%m-%d')} (new week)")
    
    # Test for following Monday
    following_monday = datetime(2026, 1, 12)  # Following Monday
    result = calculate_monday_of_current_week(following_monday)
    expected = datetime(2026, 1, 12)
    assert result.date() == expected.date(), f"Following Monday test failed: expected {expected.date()}, got {result.date()}"
    print(f"✓ Following Monday (2026-01-12): Returns {result.strftime('%Y-%m-%d')} (new week)")
    
    print()
    return True


def test_week_range_calculation():
    """Test that the week range calculation produces correct start and end dates"""
    print("=" * 80)
    print("Test 3: Week range calculation (Monday to Sunday)")
    print("=" * 80)
    
    # Test current week
    saturday_date = datetime(2026, 1, 3)
    monday = calculate_monday_of_current_week(saturday_date)
    sunday = monday + timedelta(days=6)
    
    assert monday.strftime('%Y-%m-%d') == '2025-12-29', f"Week start incorrect: expected 2025-12-29, got {monday.strftime('%Y-%m-%d')}"
    assert sunday.strftime('%Y-%m-%d') == '2026-01-04', f"Week end incorrect: expected 2026-01-04, got {sunday.strftime('%Y-%m-%d')}"
    print(f"✓ Current week: {monday.strftime('%Y-%m-%d')} to {sunday.strftime('%Y-%m-%d')}")
    
    # Test next week
    next_monday_date = datetime(2026, 1, 5)
    monday = calculate_monday_of_current_week(next_monday_date)
    sunday = monday + timedelta(days=6)
    
    assert monday.strftime('%Y-%m-%d') == '2026-01-05', f"Next week start incorrect: expected 2026-01-05, got {monday.strftime('%Y-%m-%d')}"
    assert sunday.strftime('%Y-%m-%d') == '2026-01-11', f"Next week end incorrect: expected 2026-01-11, got {sunday.strftime('%Y-%m-%d')}"
    print(f"✓ Next week: {monday.strftime('%Y-%m-%d')} to {sunday.strftime('%Y-%m-%d')}")
    
    print()
    return True


def test_edge_cases():
    """Test edge cases like year boundaries"""
    print("=" * 80)
    print("Test 4: Edge cases (year boundaries)")
    print("=" * 80)
    
    # Test a date at year boundary
    new_years_day = datetime(2026, 1, 1)  # Thursday, January 1, 2026
    monday = calculate_monday_of_current_week(new_years_day)
    
    # The Monday of this week should be December 29, 2025
    assert monday.strftime('%Y-%m-%d') == '2025-12-29', f"Year boundary test failed: expected 2025-12-29, got {monday.strftime('%Y-%m-%d')}"
    print(f"✓ January 1, 2026 (Thursday): Returns {monday.strftime('%Y-%m-%d')} (previous year)")
    
    print()
    return True


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("Testing Date Calculation Logic for Weekly Report")
    print("=" * 80)
    print()
    
    tests = [
        test_monday_calculation,
        test_next_week_calculation,
        test_week_range_calculation,
        test_edge_cases,
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
    
    print("=" * 80)
    if all(results):
        print(f"✓ All {len(results)} tests passed!")
        print("=" * 80)
        print()
        print("Verification Summary:")
        print("  ✓ Monday calculation works correctly for all days of the week")
        print("  ✓ Week range spans Monday to Sunday (7 days)")
        print("  ✓ Automatic transition to new week on Monday")
        print("  ✓ Year boundary handling works correctly")
        print()
        print("Expected behavior:")
        print("  - Today (Jan 3, 2026): Report for December 29, 2025 - January 4, 2026")
        print("  - Next Monday (Jan 5, 2026): Report for January 5, 2026 - January 11, 2026")
        return 0
    else:
        print(f"✗ {len([r for r in results if not r])} out of {len(results)} tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

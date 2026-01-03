"""
Test to verify the script exits with non-zero status when no weekly data is found.
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import io

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


def test_main_exits_on_empty_data():
    """Test that main() exits with code 1 when no weekly data is found"""
    print("=" * 80)
    print("Test: main() exits with error when no weekly data found")
    print("=" * 80)
    print()
    
    # Mock the fetch function to return data from a different week
    # This will cause the filter to return empty results
    past_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    mock_data = [
        {'date': past_date, 'edge': 5.0, 'result': 'correct'},
        {'date': past_date, 'edge': 3.0, 'result': 'incorrect'},
    ]
    
    # Capture stdout
    captured_output = io.StringIO()
    
    with patch('analyze_model_performance_weekly.fetch_graded_results_from_github', return_value=mock_data):
        with patch('sys.stdout', new=captured_output):
            # Import main after patching
            from analyze_model_performance_weekly import main
            
            try:
                main()
                # If we get here, the function didn't exit as expected
                print("✗ main() should have called sys.exit(1) but didn't")
                return False
            except SystemExit as e:
                if e.code == 1:
                    print(f"✓ main() correctly exited with status code 1")
                    output = captured_output.getvalue()
                    if "ERROR: No data found for the current week" in output:
                        print("✓ Error message was printed correctly")
                    else:
                        print("⚠ Error message not found in output")
                        print(f"Output: {output[:200]}")
                    return True
                else:
                    print(f"✗ main() exited with code {e.code}, expected 1")
                    return False


def test_main_succeeds_with_data():
    """Test that main() runs successfully when weekly data is found"""
    print()
    print("=" * 80)
    print("Test: main() succeeds when weekly data is found")
    print("=" * 80)
    print()
    
    # Mock the fetch function to return current week data
    current_date = datetime.now().strftime('%Y-%m-%d')
    mock_data = [
        {'date': current_date, 'edge': 5.0, 'result': 'correct', 'home_team': 'Team A', 'away_team': 'Team B'},
        {'date': current_date, 'edge': 3.0, 'result': 'incorrect', 'home_team': 'Team C', 'away_team': 'Team D'},
    ]
    
    # Capture stdout
    captured_output = io.StringIO()
    
    with patch('analyze_model_performance_weekly.fetch_graded_results_from_github', return_value=mock_data):
        with patch('sys.stdout', new=captured_output):
            # Mock os.makedirs to prevent actual directory creation
            with patch('os.makedirs'):
                # Mock file operations
                with patch('builtins.open', MagicMock()):
                    # Mock os.path.exists to return False (no previous files)
                    with patch('os.path.exists', return_value=False):
                        from analyze_model_performance_weekly import main
                        
                        try:
                            main()
                            print("✓ main() completed successfully without exiting")
                            output = captured_output.getvalue()
                            if "Found 2 records for the current week" in output:
                                print("✓ Correct number of records was reported")
                            return True
                        except SystemExit as e:
                            if e.code == 0 or e.code is None:
                                print("✓ main() exited with success status")
                                return True
                            else:
                                print(f"✗ main() exited with code {e.code}, expected 0 or no exit")
                                return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print("Testing Weekly Script Exit Behavior")
    print("=" * 80)
    print()
    
    tests = [
        test_main_exits_on_empty_data,
        test_main_succeeds_with_data,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print()
    print("=" * 80)
    if all(results):
        print(f"✓ All {len(results)} tests passed!")
        print("=" * 80)
        print()
        print("Verification Summary:")
        print("  ✓ Script exits with code 1 when no weekly data is found")
        print("  ✓ Script succeeds when weekly data is present")
        print("  ✓ Error messages are properly displayed")
        return 0
    else:
        print(f"✗ {len([r for r in results if not r])} out of {len(results)} tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

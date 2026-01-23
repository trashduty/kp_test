#!/usr/bin/env python3
"""
Test to verify the ratings endpoint configuration is correct.
This test validates that the script is configured to call the 'ratings' endpoint
which should include the RankAdjEM field needed for proper rankings.
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set dummy API key for testing
os.environ['KENPOM_API_KEY'] = 'dummy_key_for_testing'

# Import the module to check its configuration
import scrape_kenpom_stats


def test_endpoint_configuration():
    """
    Test that the script is configured to use the 'ratings' endpoint.
    """
    print("=" * 80)
    print("Test: Verify Ratings Endpoint Configuration")
    print("=" * 80)
    print()
    
    # Verify the function exists and has the correct name
    assert hasattr(scrape_kenpom_stats, 'fetch_ratings'), \
        "fetch_ratings function not found in scrape_kenpom_stats module"
    print("✓ fetch_ratings function exists")
    
    # Verify the old function name is removed
    assert not hasattr(scrape_kenpom_stats, 'fetch_four_factors'), \
        "fetch_four_factors function still exists (should be renamed to fetch_ratings)"
    print("✓ fetch_four_factors function removed (renamed to fetch_ratings)")
    
    # Check the function source to verify it uses 'ratings' endpoint
    import inspect
    source = inspect.getsource(scrape_kenpom_stats.fetch_ratings)
    
    assert '"ratings"' in source or "'ratings'" in source, \
        "fetch_ratings function does not specify 'ratings' endpoint"
    print("✓ fetch_ratings function uses 'ratings' endpoint")
    
    assert '"four-factors"' not in source and "'four-factors'" not in source, \
        "fetch_ratings function still references 'four-factors' endpoint"
    print("✓ fetch_ratings function does not reference 'four-factors' endpoint")
    
    # Verify the function is called in main
    with open(os.path.join(parent_dir, 'scrape_kenpom_stats.py'), 'r') as f:
        script_content = f.read()
    
    assert 'fetch_ratings()' in script_content, \
        "fetch_ratings() not called in main section"
    print("✓ fetch_ratings() is called in main section")
    
    assert 'fetch_four_factors()' not in script_content, \
        "fetch_four_factors() still called in main section"
    print("✓ fetch_four_factors() is not called in main section")
    
    print()
    print("=" * 80)
    print("✅ TEST PASSED: Script correctly configured for 'ratings' endpoint")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ Function renamed from fetch_four_factors to fetch_ratings")
    print("  ✓ Endpoint changed from 'four-factors' to 'ratings'")
    print("  ✓ Main section updated to call fetch_ratings()")
    print()
    print("Expected behavior:")
    print("  • The 'ratings' endpoint should include RankAdjEM field")
    print("  • Rankings should reflect KenPom's AdjEM rankings")
    print("  • Teams should NOT be in alphabetical order")
    print()


if __name__ == "__main__":
    try:
        test_endpoint_configuration()
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

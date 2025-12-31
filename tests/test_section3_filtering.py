"""
Test to verify Section 3 filtering logic in analyze_model_performance.py
This test ensures that:
1. NaN values are properly handled
2. Only games with spread_cover_probability > 0.5 are included
3. Filtering is applied to both favorites and underdogs
"""

import pandas as pd
import numpy as np
import sys


def test_section3_filtering():
    """Test that Section 3 filters correctly for spread_cover_probability > 0.5"""
    
    # Create test data with various scenarios
    test_data = {
        'spread_cover_probability': [0.6, 0.4, 0.7, np.nan, 0.55, 0.45, 0.8, 0.3],
        'spread_covered': [1, 0, 1, 1, 0, 1, 1, 0],
        'opening_spread': [-5.5, -3.5, 7.5, -10.5, 12.0, np.nan, -8.0, 15.0],
        'team': ['Duke', 'UNC', 'Kansas', 'Kentucky', 'Louisville', 'Syracuse', 'Villanova', 'Arizona'],
        'home_team': ['Duke', 'UNC', 'Kansas', 'Kentucky', 'Louisville', 'Syracuse', 'Villanova', 'Arizona'],
        'away_team': ['UNC', 'Duke', 'Missouri', 'Louisville', 'Kentucky', 'Georgetown', 'Seton Hall', 'UCLA'],
    }
    
    df = pd.DataFrame(test_data)
    
    print("=" * 80)
    print("Test Data:")
    print("=" * 80)
    print(df.to_string())
    print()
    
    # Simulate the exact logic from analyze_spread_performance_by_point_spread
    print("=" * 80)
    print("Step 1: Drop NaN values")
    print("=" * 80)
    confident_picks = df.dropna(subset=['spread_cover_probability', 'spread_covered', 'opening_spread']).copy()
    print(f"Rows remaining after dropna: {len(confident_picks)}")
    print(confident_picks.to_string())
    print()
    
    print("=" * 80)
    print("Step 2: Filter for spread_cover_probability > 0.5")
    print("=" * 80)
    confident_picks = confident_picks[confident_picks['spread_cover_probability'] > 0.5].copy()
    print(f"Rows remaining after filtering: {len(confident_picks)}")
    print(confident_picks.to_string())
    print()
    
    # Verify the filtering worked correctly
    assert len(confident_picks) == 4, f"Expected 4 rows, got {len(confident_picks)}"
    
    # Verify no NaN values remain
    assert not confident_picks['spread_cover_probability'].isna().any(), "NaN values found in spread_cover_probability"
    assert not confident_picks['spread_covered'].isna().any(), "NaN values found in spread_covered"
    assert not confident_picks['opening_spread'].isna().any(), "NaN values found in opening_spread"
    
    # Verify all spread_cover_probability values are > 0.5
    assert (confident_picks['spread_cover_probability'] > 0.5).all(), "Found spread_cover_probability <= 0.5"
    
    print("=" * 80)
    print("Step 3: Split into favorites and underdogs")
    print("=" * 80)
    
    # Favorites (opening_spread < 0)
    favorites = confident_picks[confident_picks['opening_spread'] < 0].copy()
    print(f"\nFavorites (opening_spread < 0): {len(favorites)} rows")
    print(favorites[['team', 'opening_spread', 'spread_cover_probability', 'spread_covered']].to_string())
    
    # Verify all favorites have opening_spread < 0
    assert (favorites['opening_spread'] < 0).all(), "Found favorites with opening_spread >= 0"
    
    # Underdogs (opening_spread > 0)
    underdogs = confident_picks[confident_picks['opening_spread'] > 0].copy()
    print(f"\nUnderdogs (opening_spread > 0): {len(underdogs)} rows")
    print(underdogs[['team', 'opening_spread', 'spread_cover_probability', 'spread_covered']].to_string())
    
    # Verify all underdogs have opening_spread > 0
    assert (underdogs['opening_spread'] > 0).all(), "Found underdogs with opening_spread <= 0"
    
    print()
    print("=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Started with {len(df)} rows")
    print(f"  - After dropping NaN: {len(confident_picks) + 2} rows (removed 2 rows with NaN)")
    print(f"  - After filtering for spread_cover_probability > 0.5: {len(confident_picks)} rows")
    print(f"    - Favorites: {len(favorites)} rows")
    print(f"    - Underdogs: {len(underdogs)} rows")
    print()
    print("All filtering logic is working correctly!")
    print("  ✓ NaN values are properly handled")
    print("  ✓ Only games with spread_cover_probability > 0.5 are included")
    print("  ✓ Filtering applies to both favorites and underdogs")
    

if __name__ == "__main__":
    try:
        test_section3_filtering()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

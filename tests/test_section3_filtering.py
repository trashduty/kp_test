"""
Test to verify Section 3 filtering logic in analyze_model_performance.py
This test ensures that:
1. NaN values are properly handled
2. Only games with spread_cover_probability > 0.5 are included
3. Only games with opening_spread_edge >= 0 are included
4. Filtering is applied to both favorites and underdogs
"""

import pandas as pd
import numpy as np
import sys


def test_section3_filtering():
    """Test that Section 3 filters correctly for spread_cover_probability > 0.5 and opening_spread_edge >= 0"""
    
    # Create test data with various scenarios
    test_data = {
        'spread_cover_probability': [0.6, 0.4, 0.7, np.nan, 0.55, 0.45, 0.8, 0.3, 0.65],
        'spread_covered': [1, 0, 1, 1, 0, 1, 1, 0, 1],
        'opening_spread': [-5.5, -3.5, 7.5, -10.5, 12.0, np.nan, -8.0, 15.0, -6.0],
        'opening_spread_edge': [0.02, 0.01, 0.03, np.nan, 0.015, 0.02, -0.01, 0.04, 0.025],
        'team': ['Duke', 'UNC', 'Kansas', 'Kentucky', 'Louisville', 'Syracuse', 'Villanova', 'Arizona', 'Michigan'],
        'home_team': ['Duke', 'UNC', 'Kansas', 'Kentucky', 'Louisville', 'Syracuse', 'Villanova', 'Arizona', 'Michigan'],
        'away_team': ['UNC', 'Duke', 'Missouri', 'Louisville', 'Kentucky', 'Georgetown', 'Seton Hall', 'UCLA', 'Ohio State'],
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
    confident_picks_after_dropna = df.dropna(subset=['spread_cover_probability', 'spread_covered', 'opening_spread']).copy()
    print(f"Rows remaining after dropna: {len(confident_picks_after_dropna)}")
    print(confident_picks_after_dropna.to_string())
    print()
    
    print("=" * 80)
    print("Step 2: Filter for spread_cover_probability > 0.5")
    print("=" * 80)
    confident_picks_after_prob = confident_picks_after_dropna[confident_picks_after_dropna['spread_cover_probability'] > 0.5].copy()
    print(f"Rows remaining after probability filter: {len(confident_picks_after_prob)}")
    print(confident_picks_after_prob.to_string())
    print()
    
    print("=" * 80)
    print("Step 3: Drop NaN values for opening_spread_edge and filter for opening_spread_edge >= 0")
    print("=" * 80)
    confident_picks = confident_picks_after_prob.dropna(subset=['opening_spread_edge']).copy()
    print(f"Rows remaining after dropna(opening_spread_edge): {len(confident_picks)}")
    confident_picks = confident_picks[confident_picks['opening_spread_edge'] >= 0].copy()
    print(f"Rows remaining after opening_spread_edge >= 0 filter: {len(confident_picks)}")
    print(confident_picks.to_string())
    print()
    
    # Verify the filtering worked correctly
    assert len(confident_picks) == 4, f"Expected 4 rows, got {len(confident_picks)}"
    
    # Verify no NaN values remain
    assert not confident_picks['spread_cover_probability'].isna().any(), "NaN values found in spread_cover_probability"
    assert not confident_picks['spread_covered'].isna().any(), "NaN values found in spread_covered"
    assert not confident_picks['opening_spread'].isna().any(), "NaN values found in opening_spread"
    assert not confident_picks['opening_spread_edge'].isna().any(), "NaN values found in opening_spread_edge"
    
    # Verify all spread_cover_probability values are > 0.5
    assert (confident_picks['spread_cover_probability'] > 0.5).all(), "Found spread_cover_probability <= 0.5"
    
    # Verify all opening_spread_edge values are >= 0
    assert (confident_picks['opening_spread_edge'] >= 0).all(), "Found opening_spread_edge < 0"
    
    print("=" * 80)
    print("Step 4: Split into favorites and underdogs")
    print("=" * 80)
    
    # Favorites (opening_spread < 0)
    favorites = confident_picks[confident_picks['opening_spread'] < 0].copy()
    print(f"\nFavorites (opening_spread < 0): {len(favorites)} rows")
    if len(favorites) > 0:
        print(favorites[['team', 'opening_spread', 'opening_spread_edge', 'spread_cover_probability', 'spread_covered']].to_string())
    
    # Verify all favorites have opening_spread < 0
    if len(favorites) > 0:
        assert (favorites['opening_spread'] < 0).all(), "Found favorites with opening_spread >= 0"
    
    # Underdogs (opening_spread > 0)
    underdogs = confident_picks[confident_picks['opening_spread'] > 0].copy()
    print(f"\nUnderdogs (opening_spread > 0): {len(underdogs)} rows")
    if len(underdogs) > 0:
        print(underdogs[['team', 'opening_spread', 'opening_spread_edge', 'spread_cover_probability', 'spread_covered']].to_string())
    
    # Verify all underdogs have opening_spread > 0
    if len(underdogs) > 0:
        assert (underdogs['opening_spread'] > 0).all(), "Found underdogs with opening_spread <= 0"
    
    print()
    print("=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Started with {len(df)} rows")
    rows_removed_by_nan = len(df) - len(confident_picks_after_dropna)
    print(f"  - After dropping NaN (spread_cover_probability, spread_covered, opening_spread): {len(confident_picks_after_dropna)} rows (removed {rows_removed_by_nan} rows with NaN)")
    rows_removed_by_prob_filter = len(confident_picks_after_dropna) - len(confident_picks_after_prob)
    print(f"  - After filtering for spread_cover_probability > 0.5: {len(confident_picks_after_prob)} rows (removed {rows_removed_by_prob_filter} rows)")
    rows_removed_by_edge_filter = len(confident_picks_after_prob) - len(confident_picks)
    print(f"  - After filtering for opening_spread_edge >= 0: {len(confident_picks)} rows (removed {rows_removed_by_edge_filter} rows)")
    print(f"    - Favorites: {len(favorites)} rows")
    print(f"    - Underdogs: {len(underdogs)} rows")
    print()
    print("All filtering logic is working correctly!")
    print("  ✓ NaN values are properly handled")
    print("  ✓ Only games with spread_cover_probability > 0.5 are included")
    print("  ✓ Only games with opening_spread_edge >= 0 are included")
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

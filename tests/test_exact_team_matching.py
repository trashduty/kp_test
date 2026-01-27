"""
Tests for exact team name matching in generate_previews.py

This test validates that team names are matched exactly and not using fuzzy/partial matching.
For example, "Ohio State" should match "Ohio St." (not "Ohio"), and "Penn State" should 
match "Penn St." (not "Penn").
"""
import sys
import os
import pandas as pd

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import find_team_in_kenpom, normalize_team_name


def test_exact_matching_ohio():
    """Test that 'Ohio State' matches 'Ohio St.' via normalization, not 'Ohio' via partial matching"""
    # Create mock dataframe with both Ohio and Ohio St.
    kenpom_df = pd.DataFrame({
        'Team': ['Ohio', 'Ohio St.', 'Arizona', 'Duke'],
        'Rk': [229, 38, 1, 3],
        'Coach': ['Jeff Boals', 'Jake Diebler', 'Tommy Lloyd', 'Jon Scheyer']
    })
    
    # Test Ohio State (should normalize to "Ohio St." and match)
    result = find_team_in_kenpom('Ohio State', kenpom_df)
    assert result is not None and result['Team'] == 'Ohio St.', \
        f"'Ohio State' should normalize to 'Ohio St.' and match, got '{result['Team'] if result is not None else 'None'}'"
    assert result['Rk'] == 38, "Should match Ohio St. (Rank 38), not Ohio (Rank 229)"
    
    # Test Ohio St. (exact match)
    result = find_team_in_kenpom('Ohio St.', kenpom_df)
    assert result is not None and result['Team'] == 'Ohio St.', \
        f"'Ohio St.' should match exactly"
    assert result['Rk'] == 38, "Should match Ohio St. (Rank 38), not Ohio (Rank 229)"
    
    # Test Ohio (exact match)
    result = find_team_in_kenpom('Ohio', kenpom_df)
    assert result is not None and result['Team'] == 'Ohio', \
        f"'Ohio' should match exactly to Ohio"
    assert result['Rk'] == 229, "Should match Ohio (Rank 229)"
    
    print("✓ Ohio/Ohio St. matching works correctly with exact matching")


def test_exact_matching_penn():
    """Test that 'Penn State' matches 'Penn St.' via normalization, not 'Penn' via partial matching"""
    # Create mock dataframe with both Penn and Penn St.
    kenpom_df = pd.DataFrame({
        'Team': ['Penn', 'Penn St.', 'Arizona', 'Duke'],
        'Rk': [193, 133, 1, 3],
        'Coach': ['Steve Donahue', 'Mike Rhoades', 'Tommy Lloyd', 'Jon Scheyer']
    })
    
    # Test Penn State (should normalize to "Penn St." and match)
    result = find_team_in_kenpom('Penn State', kenpom_df)
    assert result is not None and result['Team'] == 'Penn St.', \
        f"'Penn State' should normalize to 'Penn St.' and match, got '{result['Team'] if result is not None else 'None'}'"
    assert result['Rk'] == 133, "Should match Penn St. (Rank 133), not Penn (Rank 193)"
    
    # Test Penn St. (exact match)
    result = find_team_in_kenpom('Penn St.', kenpom_df)
    assert result is not None and result['Team'] == 'Penn St.', \
        f"'Penn St.' should match exactly"
    assert result['Rk'] == 133, "Should match Penn St. (Rank 133), not Penn (Rank 193)"
    
    # Test Penn (exact match)
    result = find_team_in_kenpom('Penn', kenpom_df)
    assert result is not None and result['Team'] == 'Penn', \
        f"'Penn' should match exactly to Penn"
    assert result['Rk'] == 193, "Should match Penn (Rank 193)"
    
    print("✓ Penn/Penn St. matching works correctly with exact matching")


def test_normalize_team_name_st_variations():
    """Test that normalize_team_name handles 'St' vs 'St.' and 'State' variations"""
    # Test "St" -> "St." at end
    assert normalize_team_name('Ohio St') == 'Ohio St.'
    assert normalize_team_name('Penn St') == 'Penn St.'
    
    # Test "St." stays "St."
    assert normalize_team_name('Ohio St.') == 'Ohio St.'
    assert normalize_team_name('Penn St.') == 'Penn St.'
    
    # Test "State" -> "St."
    assert normalize_team_name('Ohio State') == 'Ohio St.'
    assert normalize_team_name('Penn State') == 'Penn St.'
    assert normalize_team_name('Arizona State') == 'Arizona St.'
    
    print("✓ normalize_team_name handles St/State variations correctly")


def test_no_partial_matching():
    """Test that partial matching is disabled"""
    # Create mock dataframe
    kenpom_df = pd.DataFrame({
        'Team': ['Arizona', 'Arizona St.', 'Michigan', 'Michigan St.'],
        'Rk': [1, 50, 2, 25],
        'Coach': ['Tommy Lloyd', 'Bobby Hurley', 'Dusty May', 'Tom Izzo']
    })
    
    # "Arizona State" should normalize to "Arizona St." and match
    result = find_team_in_kenpom('Arizona State', kenpom_df)
    assert result is not None and result['Team'] == 'Arizona St.', \
        f"'Arizona State' should normalize and match 'Arizona St.', got '{result['Team'] if result is not None else 'None'}'"
    
    # Partial string should NOT match via partial matching
    result = find_team_in_kenpom('Mich', kenpom_df)
    assert result is None, \
        f"Partial string 'Mich' should not match any team"
    
    print("✓ Partial matching is correctly disabled")


def test_exact_match_priority():
    """Test that exact matches are found first"""
    kenpom_df = pd.DataFrame({
        'Team': ['Duke', 'Arizona', 'Michigan'],
        'Rk': [3, 1, 2],
        'Coach': ['Jon Scheyer', 'Tommy Lloyd', 'Dusty May']
    })
    
    result = find_team_in_kenpom('Duke', kenpom_df)
    assert result is not None and result['Team'] == 'Duke'
    assert result['Rk'] == 3
    
    result = find_team_in_kenpom('Arizona', kenpom_df)
    assert result is not None and result['Team'] == 'Arizona'
    assert result['Rk'] == 1
    
    print("✓ Exact matches are found correctly")


if __name__ == '__main__':
    test_exact_matching_ohio()
    test_exact_matching_penn()
    test_normalize_team_name_st_variations()
    test_no_partial_matching()
    test_exact_match_priority()
    print("\n✅ All exact team matching tests passed!")

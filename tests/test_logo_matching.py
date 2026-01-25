"""
Tests for logo matching functionality in generate_previews.py
"""
import sys
import os
import pandas as pd

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import find_team_logo


def test_find_team_logo_exact_match():
    """Test that find_team_logo finds exact matches on 'name' column"""
    # Create mock logos dataframe matching remote logos.csv structure
    logos_df = pd.DataFrame({
        'name': [
            'South Carolina State Bulldogs',
            'Delaware State Hornets',
            'Duke Blue Devils',
            'Wisconsin Badgers'
        ],
        'ncaa_name': [
            'South Carolina St.',
            'Delaware St.',
            'Duke',
            'Wisconsin'
        ],
        'logos': [
            'https://example.com/sc-state.svg',
            'https://example.com/delaware-state.svg',
            'https://example.com/duke.svg',
            'https://example.com/wisconsin.svg'
        ]
    })
    
    # Test exact match
    result = find_team_logo('South Carolina State Bulldogs', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo, got: {result}"
    
    result = find_team_logo('Delaware State Hornets', logos_df)
    assert result == 'https://example.com/delaware-state.svg', f"Expected Delaware State logo, got: {result}"
    
    print("✓ Exact match on 'name' column works")


def test_find_team_logo_case_insensitive():
    """Test that find_team_logo handles case-insensitive matches"""
    logos_df = pd.DataFrame({
        'name': [
            'South Carolina State Bulldogs',
            'Delaware State Hornets'
        ],
        'ncaa_name': [
            'South Carolina St.',
            'Delaware St.'
        ],
        'logos': [
            'https://example.com/sc-state.svg',
            'https://example.com/delaware-state.svg'
        ]
    })
    
    # Test case-insensitive match
    result = find_team_logo('south carolina state bulldogs', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo, got: {result}"
    
    result = find_team_logo('DELAWARE STATE HORNETS', logos_df)
    assert result == 'https://example.com/delaware-state.svg', f"Expected Delaware State logo, got: {result}"
    
    print("✓ Case-insensitive match works")


def test_find_team_logo_no_match():
    """Test that find_team_logo returns placeholder when no match found"""
    logos_df = pd.DataFrame({
        'name': ['Duke Blue Devils', 'Wisconsin Badgers'],
        'ncaa_name': ['Duke', 'Wisconsin'],
        'logos': [
            'https://example.com/duke.svg',
            'https://example.com/wisconsin.svg'
        ]
    })
    
    # Test no match
    result = find_team_logo('Unknown Team', logos_df)
    assert result == 'https://via.placeholder.com/150', f"Expected placeholder, got: {result}"
    
    print("✓ Placeholder returned for no match")


def test_find_team_logo_uses_multiple_columns():
    """Test that find_team_logo uses 'name', 'ncaa_name', and other columns for matching"""
    # Create logos with different values in name vs ncaa_name
    logos_df = pd.DataFrame({
        'name': ['South Carolina State Bulldogs'],
        'ncaa_name': ['South Carolina St.'],
        'reference_name': ['South Carolina State'],
        'logos': ['https://example.com/sc-state.svg']
    })
    
    # This should match using 'name' column
    result = find_team_logo('South Carolina State Bulldogs', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo, got: {result}"
    
    # This should now match using 'ncaa_name' column
    result = find_team_logo('South Carolina St.', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo for ncaa_name match, got: {result}"
    
    # This should also match using 'reference_name' column
    result = find_team_logo('South Carolina State', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo for reference_name match, got: {result}"
    
    print("✓ Uses 'name', 'ncaa_name', and 'reference_name' columns for matching")


def test_find_team_logo_returns_from_logos_column():
    """Test that find_team_logo returns URL from 'logos' column"""
    logos_df = pd.DataFrame({
        'name': ['Duke Blue Devils'],
        'ncaa_name': ['Duke'],
        'logos': ['https://example.com/duke-correct.svg'],
        'logo': ['https://example.com/duke-wrong.svg']  # Different column
    })
    
    result = find_team_logo('Duke Blue Devils', logos_df)
    assert result == 'https://example.com/duke-correct.svg', f"Expected URL from 'logos' column, got: {result}"
    
    print("✓ Returns URL from 'logos' column")


def test_find_team_logo_strips_mascot():
    """Test that find_team_logo can strip mascot and match on ncaa_name"""
    # Test the exact scenario from the problem statement
    logos_df = pd.DataFrame({
        'name': ['South Carolina State Bulldogs', 'Delaware State Hornets'],
        'ncaa_name': ['South Carolina St.', 'Delaware St.'],
        'reference_name': ['South Carolina State', 'Delaware State'],
        'logos': [
            'https://example.com/sc-state.svg',
            'https://example.com/delaware-state.svg'
        ]
    })
    
    # These team names should match by stripping the mascot (Bulldogs/Hornets)
    # and adding a period to match ncaa_name
    result = find_team_logo('South Carolina St Bulldogs', logos_df)
    assert result == 'https://example.com/sc-state.svg', \
        f"Expected SC State logo for 'South Carolina St Bulldogs', got: {result}"
    
    result = find_team_logo('Delaware St Hornets', logos_df)
    assert result == 'https://example.com/delaware-state.svg', \
        f"Expected Delaware State logo for 'Delaware St Hornets', got: {result}"
    
    print("✓ Strips mascot and matches on ncaa_name column")


if __name__ == '__main__':
    test_find_team_logo_exact_match()
    test_find_team_logo_case_insensitive()
    test_find_team_logo_no_match()
    test_find_team_logo_uses_multiple_columns()
    test_find_team_logo_returns_from_logos_column()
    test_find_team_logo_strips_mascot()
    print("\n✅ All logo matching tests passed!")

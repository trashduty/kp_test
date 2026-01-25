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


def test_find_team_logo_uses_name_not_ncaa_name():
    """Test that find_team_logo uses 'name' column, not 'ncaa_name' column"""
    # Create logos with different values in name vs ncaa_name
    logos_df = pd.DataFrame({
        'name': ['South Carolina State Bulldogs'],
        'ncaa_name': ['South Carolina St.'],
        'logos': ['https://example.com/sc-state.svg']
    })
    
    # This should match using 'name' column
    result = find_team_logo('South Carolina State Bulldogs', logos_df)
    assert result == 'https://example.com/sc-state.svg', f"Expected SC State logo, got: {result}"
    
    # This should NOT match (ncaa_name is not used for matching)
    result = find_team_logo('South Carolina St.', logos_df)
    assert result == 'https://via.placeholder.com/150', f"Expected placeholder for ncaa_name, got: {result}"
    
    print("✓ Uses 'name' column, not 'ncaa_name' column")


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


if __name__ == '__main__':
    test_find_team_logo_exact_match()
    test_find_team_logo_case_insensitive()
    test_find_team_logo_no_match()
    test_find_team_logo_uses_name_not_ncaa_name()
    test_find_team_logo_returns_from_logos_column()
    print("\n✅ All logo matching tests passed!")

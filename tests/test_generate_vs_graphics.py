"""
Tests for generate_vs_graphics.py script
"""
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path to import generate_vs_graphics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_vs_graphics import (
    slugify,
    match_team_logo,
    get_target_dates,
    create_placeholder_logo,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    LOGO_SIZE
)


def test_slugify():
    """Test that slugify converts team names correctly"""
    assert slugify("Arizona") == "arizona"
    assert slugify("Texas A&M") == "texas-am"
    assert slugify("St. John's") == "st-johns"
    assert slugify("UNC Wilmington") == "unc-wilmington"
    assert slugify("UT Rio Grande Valley") == "ut-rio-grande-valley"
    print("✓ slugify converts team names correctly")


def test_match_team_logo_exact_match():
    """Test exact team name matching with logos"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke', 'Kansas'],
        'logos': ['http://example.com/arizona.png', 
                  'http://example.com/duke.png',
                  'http://example.com/kansas.png']
    })
    
    result = match_team_logo('Arizona', logos_df)
    assert result == 'http://example.com/arizona.png'
    print("✓ Exact team name matching works")


def test_match_team_logo_case_insensitive():
    """Test case-insensitive team name matching"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    result = match_team_logo('ARIZONA', logos_df)
    assert result == 'http://example.com/arizona.png'
    print("✓ Case-insensitive matching works")


def test_match_team_logo_no_match():
    """Test that None is returned when no match is found"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    result = match_team_logo('NonexistentTeam', logos_df)
    assert result is None
    print("✓ Returns None for non-existent teams")


def test_get_target_dates():
    """Test that target dates returns today and tomorrow in correct format"""
    dates = get_target_dates()
    
    # Should return 2 dates
    assert len(dates) == 2
    
    # Should be in YYYYMMDD format
    for date in dates:
        assert len(date) == 8
        assert date.isdigit()
        # Should be parseable as date
        datetime.strptime(date, '%Y%m%d')
    
    print("✓ Target dates are in correct format")


def test_image_dimensions_constants():
    """Test that image dimension constants are set correctly"""
    assert IMAGE_WIDTH == 1200
    assert IMAGE_HEIGHT == 600
    assert LOGO_SIZE == 300
    print("✓ Image dimensions are set correctly")


def test_create_placeholder_logo():
    """Test that placeholder logo is created with correct dimensions"""
    logo = create_placeholder_logo(LOGO_SIZE)
    assert logo.size == (LOGO_SIZE, LOGO_SIZE)
    assert logo.mode == 'RGBA'
    print("✓ Placeholder logo created with correct dimensions")


if __name__ == '__main__':
    test_slugify()
    test_match_team_logo_exact_match()
    test_match_team_logo_case_insensitive()
    test_match_team_logo_no_match()
    test_get_target_dates()
    test_image_dimensions_constants()
    test_create_placeholder_logo()
    print("\n✅ All tests passed!")

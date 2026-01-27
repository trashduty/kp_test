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
    find_team_logo,
    convert_api_to_kenpom_name,
    get_target_dates,
    parse_game_time_to_date,
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


def test_find_team_logo_exact_match():
    """Test exact team name matching with logos"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke', 'Kansas'],
        'logos': ['http://example.com/arizona.png', 
                  'http://example.com/duke.png',
                  'http://example.com/kansas.png']
    })
    
    result = find_team_logo('Arizona', logos_df)
    assert result == 'http://example.com/arizona.png'
    print("✓ Exact team name matching works")


def test_find_team_logo_case_sensitive():
    """Test that matching is case-sensitive (exact match only)"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    # Should NOT match with different case (exact match only)
    result = find_team_logo('ARIZONA', logos_df)
    assert result is None
    print("✓ Case-sensitive matching works (no fallback)")


def test_find_team_logo_no_match():
    """Test that None is returned when no match is found"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    result = find_team_logo('NonexistentTeam', logos_df)
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


def test_convert_api_to_kenpom_name_found():
    """Test crosswalk conversion when team is found"""
    crosswalk_df = pd.DataFrame({
        'API': ['Miami FL', 'Miami OH', 'VCU'],
        'kenpom': ['Miami', 'Miami Ohio', 'VCU']
    })
    
    result = convert_api_to_kenpom_name('Miami FL', crosswalk_df)
    assert result == 'Miami'
    print("✓ Crosswalk conversion works for found teams")


def test_convert_api_to_kenpom_name_not_found():
    """Test crosswalk conversion when team is not found"""
    crosswalk_df = pd.DataFrame({
        'API': ['Miami FL', 'Miami OH'],
        'kenpom': ['Miami', 'Miami Ohio']
    })
    
    result = convert_api_to_kenpom_name('Duke', crosswalk_df)
    assert result == 'Duke'
    print("✓ Crosswalk returns original name when not found")


def test_convert_api_to_kenpom_name_case_insensitive():
    """Test that crosswalk lookup is case-insensitive"""
    crosswalk_df = pd.DataFrame({
        'API': ['Miami FL', 'VCU'],
        'kenpom': ['Miami', 'VCU']
    })
    
    result = convert_api_to_kenpom_name('MIAMI FL', crosswalk_df)
    assert result == 'Miami'
    print("✓ Crosswalk lookup is case-insensitive")


def test_convert_api_to_kenpom_name_empty_df():
    """Test crosswalk conversion with empty DataFrame"""
    crosswalk_df = pd.DataFrame()
    
    result = convert_api_to_kenpom_name('Duke', crosswalk_df)
    assert result == 'Duke'
    print("✓ Crosswalk returns original name with empty DataFrame")


def test_parse_game_time_to_date():
    """Test parsing game time strings to date format"""
    # Test valid game time string
    result = parse_game_time_to_date('Jan 27 02:00PM ET')
    assert result is not None
    assert len(result) == 8
    assert result.isdigit()
    
    # Verify it's the correct format (YYYYMMDD)
    date_obj = datetime.strptime(result, '%Y%m%d')
    assert date_obj.month == 1
    assert date_obj.day == 27
    
    # Test another date
    result2 = parse_game_time_to_date('Dec 15 11:30PM ET')
    assert result2 is not None
    date_obj2 = datetime.strptime(result2, '%Y%m%d')
    assert date_obj2.month == 12
    assert date_obj2.day == 15
    
    print("✓ Game time parsing to date format works correctly")


def test_parse_game_time_to_date_invalid():
    """Test that invalid game time strings return None"""
    result = parse_game_time_to_date('Invalid Date')
    assert result is None
    print("✓ Invalid game time strings return None")


if __name__ == '__main__':
    test_slugify()
    test_find_team_logo_exact_match()
    test_find_team_logo_case_sensitive()
    test_find_team_logo_no_match()
    test_get_target_dates()
    test_image_dimensions_constants()
    test_create_placeholder_logo()
    test_convert_api_to_kenpom_name_found()
    test_convert_api_to_kenpom_name_not_found()
    test_convert_api_to_kenpom_name_case_insensitive()
    test_convert_api_to_kenpom_name_empty_df()
    test_parse_game_time_to_date()
    test_parse_game_time_to_date_invalid()
    print("\n✅ All tests passed!")

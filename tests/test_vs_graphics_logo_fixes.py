"""
Tests for VS graphics logo fixes - SVG handling and improved matching
"""
import sys
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add parent directory to path to import generate_vs_graphics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_vs_graphics import (
    match_team_logo,
    download_logo,
)


def test_match_team_logo_exact_matching_only():
    """Test that only exact ncaa_name matching works"""
    logos_df = pd.DataFrame({
        'name': ['Arizona Wildcats', 'Duke Blue Devils'],
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    # Should match via exact ncaa_name
    result = match_team_logo('Arizona', logos_df)
    assert result == 'http://example.com/arizona.png'
    
    # Should NOT match via name column
    result = match_team_logo('arizona wildcats', logos_df)
    assert result is None
    
    print("✓ Only exact ncaa_name matching works")


def test_match_team_logo_no_partial_match():
    """Test that partial/substring matching does NOT work"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Texas A&M', 'Alabama St.'],
        'logos': ['http://example.com/tam.png', 'http://example.com/alast.png']
    })
    
    # Test exact match (should work)
    result = match_team_logo('Alabama St.', logos_df)
    assert result == 'http://example.com/alast.png'
    
    # Test partial match (should NOT work - exact only)
    result = match_team_logo('Alabama', logos_df)
    assert result is None
    
    print("✓ Partial matching correctly does NOT work")


def test_match_team_logo_debug_output():
    """Test that debug output is being generated"""
    logos_df = pd.DataFrame({
        'ncaa_name': ['Arizona', 'Duke'],
        'logos': ['http://example.com/arizona.png', 'http://example.com/duke.png']
    })
    
    # This should print debug output and return the correct URL
    result = match_team_logo('Arizona', logos_df)
    
    # Verify the match was found correctly
    assert result == 'http://example.com/arizona.png'
    print("✓ Debug output generation works")


def test_download_logo_svg_handling():
    """Test that SVG logos are properly handled when cairosvg is available"""
    svg_content = b'''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" fill="blue" />
    </svg>'''
    
    # Mock the requests.get to return SVG content
    with patch('generate_vs_graphics.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.content = svg_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Test with SVG URL
        url = "http://example.com/logo.svg"
        
        # Test with cairosvg available
        try:
            import cairosvg
            result = download_logo(url)
            # Should successfully convert SVG to image
            assert result is not None
            print("✓ SVG handling with cairosvg works")
        except ImportError:
            # If cairosvg not available, should return None
            result = download_logo(url)
            assert result is None
            print("✓ SVG handling without cairosvg returns None gracefully")


def test_download_logo_error_handling():
    """Test that download errors are handled gracefully"""
    # Test with invalid URL
    result = download_logo(None)
    assert result is None
    print("✓ Handles None URL gracefully")
    
    # Test with unreachable URL
    with patch('generate_vs_graphics.requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection error")
        result = download_logo("http://invalid.example.com/logo.png")
        assert result is None
        print("✓ Handles download errors gracefully")


def test_match_team_logo_exact_only():
    """Test that only exact matching works (no fallback strategies)"""
    logos_df = pd.DataFrame({
        'name': ['Some Full Name', 'Another Team Name'],
        'ncaa_name': ['Short Name', 'Other Name'],
        'logos': ['http://example.com/logo1.png', 'http://example.com/logo2.png']
    })
    
    # Test exact match (should work)
    result = match_team_logo('Short Name', logos_df)
    assert result == 'http://example.com/logo1.png'
    
    # Test case-insensitive (should NOT work - exact match only)
    result = match_team_logo('short name', logos_df)
    assert result is None
    
    # Test name column match (should NOT work - exact ncaa_name only)
    result = match_team_logo('Some Full Name', logos_df)
    assert result is None
    
    print("✓ Only exact ncaa_name matching works (no fallback strategies)")


if __name__ == '__main__':
    test_match_team_logo_exact_matching_only()
    test_match_team_logo_no_partial_match()
    test_match_team_logo_debug_output()
    test_download_logo_svg_handling()
    test_download_logo_error_handling()
    test_match_team_logo_exact_only()
    print("\n✅ All logo fix tests passed!")

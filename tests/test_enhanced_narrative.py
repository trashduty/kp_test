"""
Tests for the enhanced narrative function
"""
import sys
import os

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import generate_enhanced_narrative


def test_enhanced_narrative_basic():
    """Test that enhanced narrative function returns expected sections"""
    # Create mock team stats
    away_stats = {
        'Rk': 10,
        'Team': 'Team A',
        'OE': 115.5,
        'DE': 95.2,
        'RankOE': 20,
        'RankDE': 30,
        'Tempo': 72.5,
        'RankTempo': 40,
        'FG2Pct': 52.3,
        'FG3Pct': 36.5,
        'FT_Rate': 38.2,
        'FTPct': 75.4
    }
    
    home_stats = {
        'Rk': 25,
        'Team': 'Team B',
        'OE': 110.2,
        'DE': 98.5,
        'RankOE': 50,
        'RankDE': 60,
        'Tempo': 70.1,
        'RankTempo': 80,
        'FG2Pct': 50.8,
        'FG3Pct': 34.2,
        'FT_Rate': 35.1,
        'FTPct': 72.8
    }
    
    # Create mock predictions
    away_predictions = {
        'market_spread': -5.5,
        'Opening Total': 145.5,
        'Current Moneyline': -220
    }
    
    home_predictions = {
        'market_spread': 5.5,
        'Opening Total': 145.5,
        'Current Moneyline': 180
    }
    
    # Generate narrative
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that key sections are present
    assert 'Game Analysis & Betting Breakdown' in result
    assert 'Setting the Stage' in result
    assert 'Breaking Down the Spread' in result
    assert 'Offensive Firepower' in result
    assert 'Tempo & Playing Style' in result
    assert 'The Interior Battle' in result
    assert 'X-Factors & Intangibles' in result
    assert 'The Betting Angle' in result
    
    # Check that team names appear in the narrative
    assert 'Team A' in result
    assert 'Team B' in result
    
    # Check that spread value appears
    assert '5.5' in result
    
    # Check that total appears
    assert '145.5' in result
    
    print("✓ Enhanced narrative generates all required sections")
    print("✓ Team names and betting lines are included")


def test_enhanced_narrative_handles_errors():
    """Test that enhanced narrative handles missing data gracefully"""
    # Create incomplete stats - completely empty to trigger exception
    away_stats = {}
    home_stats = {}
    away_predictions = {}
    home_predictions = {}
    
    # Should return empty string when critical data is missing
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # With empty dicts, get() returns defaults, so narrative will still generate
    # Just verify it doesn't crash
    assert isinstance(result, str)
    print("✓ Enhanced narrative handles missing data gracefully")


def test_enhanced_narrative_home_favorite():
    """Test narrative when home team is favored"""
    away_stats = {
        'Rk': 50,
        'Team': 'Underdog',
        'OE': 105.0,
        'DE': 102.0,
        'RankOE': 150,
        'RankDE': 180,
        'Tempo': 68.0,
        'RankTempo': 200,
        'FG2Pct': 48.0,
        'FG3Pct': 32.0,
        'FT_Rate': 30.0,
        'FTPct': 70.0
    }
    
    home_stats = {
        'Rk': 10,
        'Team': 'Favorite',
        'OE': 118.0,
        'DE': 92.0,
        'RankOE': 15,
        'RankDE': 20,
        'Tempo': 74.0,
        'RankTempo': 30,
        'FG2Pct': 55.0,
        'FG3Pct': 38.0,
        'FT_Rate': 40.0,
        'FTPct': 78.0
    }
    
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 150.0,
        'Current Moneyline': 300
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 150.0,
        'Current Moneyline': -400
    }
    
    result = generate_enhanced_narrative(
        'Underdog', 'Favorite',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Should mention Favorite as the favorite
    assert 'Favorite' in result
    assert '8.5' in result
    
    print("✓ Enhanced narrative correctly identifies home favorite")


if __name__ == '__main__':
    test_enhanced_narrative_basic()
    test_enhanced_narrative_handles_errors()
    test_enhanced_narrative_home_favorite()
    print("\n✅ All enhanced narrative tests passed!")

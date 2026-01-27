"""
Tests to verify the fixes in grade_spread_predictions.py match generate_previews.py
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grade_spread_predictions import generate_enhanced_narrative, generate_predictions_section


def test_grade_spread_predictions_uses_market_spread():
    """Test that grade_spread_predictions.py uses market_spread"""
    
    away_predictions = {
        'market_spread': -6.5,
        'Predicted Outcome': -4.0,
        'Edge For Covering Spread': 0.18,
        'Moneyline Win Probability': 0.70,
        'average_total': 148.5,
        'Over Total Edge': 0.12,
        'Under Total Edge': -0.08
    }
    
    home_predictions = {
        'market_spread': 6.5,
        'Predicted Outcome': 4.0,
        'Edge For Covering Spread': -0.18,
        'Moneyline Win Probability': 0.30,
        'average_total': 148.5,
        'Over Total Edge': 0.12,
        'Under Total Edge': -0.08
    }
    
    result = generate_predictions_section('Away Team', 'Home Team', away_predictions, home_predictions)
    
    assert '-6.5' in result or '-6.50' in result, "Away market_spread should appear"
    assert '6.5' in result or '6.50' in result, "Home market_spread should appear"
    
    print("✓ grade_spread_predictions.py uses market_spread correctly")


def test_grade_no_betting_angle():
    """Test that grade_spread_predictions.py has no Betting Angle section"""
    
    away_stats = {
        'Rk': 15, 'Team': 'Team A', 'OE': 114.5, 'DE': 97.2,
        'RankOE': 40, 'RankDE': 50, 'Tempo': 72.5, 'RankTempo': 45,
        'FG2Pct': 53.3, 'FG3Pct': 37.5, 'FT_Rate': 39.2, 'FTPct': 76.4,
        'Wins': 16, 'Losses': 6, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats = {
        'Rk': 35, 'Team': 'Team B', 'OE': 109.2, 'DE': 101.5,
        'RankOE': 85, 'RankDE': 105, 'Tempo': 69.1, 'RankTempo': 100,
        'FG2Pct': 50.8, 'FG3Pct': 33.2, 'FT_Rate': 34.1, 'FTPct': 71.8,
        'Wins': 12, 'Losses': 9, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    away_predictions = {
        'market_spread': -5.5,
        'Opening Total': 147.5,
        'Current Moneyline': -220
    }
    
    home_predictions = {
        'market_spread': 5.5,
        'Opening Total': 147.5,
        'Current Moneyline': 180
    }
    
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    assert '#### The Betting Angle' not in result
    assert 'sharp play' not in result
    
    print("✓ grade_spread_predictions.py has no Betting Angle section")


def test_grade_no_field_goal():
    """Test that grade_spread_predictions.py doesn't use 'field goal'"""
    
    away_stats = {
        'Rk': 25, 'Team': 'Team A', 'OE': 111.5, 'DE': 99.2,
        'RankOE': 70, 'RankDE': 90, 'Tempo': 71.5, 'RankTempo': 70,
        'FG2Pct': 51.3, 'FG3Pct': 35.5, 'FT_Rate': 36.2, 'FTPct': 74.4,
        'Wins': 13, 'Losses': 8, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats = {
        'Rk': 30, 'Team': 'Team B', 'OE': 109.2, 'DE': 100.5,
        'RankOE': 80, 'RankDE': 100, 'Tempo': 70.1, 'RankTempo': 90,
        'FG2Pct': 50.8, 'FG3Pct': 34.2, 'FT_Rate': 35.1, 'FTPct': 72.8,
        'Wins': 12, 'Losses': 9, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    away_predictions = {
        'market_spread': -2.5,
        'Opening Total': 145.5,
        'Current Moneyline': -145
    }
    
    home_predictions = {
        'market_spread': 2.5,
        'Opening Total': 145.5,
        'Current Moneyline': 125
    }
    
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    assert 'field goal' not in result.lower()
    assert '3 points' in result
    
    print("✓ grade_spread_predictions.py doesn't use 'field goal'")


if __name__ == '__main__':
    print("Running tests for grade_spread_predictions.py fixes...\n")
    
    test_grade_spread_predictions_uses_market_spread()
    test_grade_no_betting_angle()
    test_grade_no_field_goal()
    
    print("\n✅ All grade_spread_predictions.py tests passed!")

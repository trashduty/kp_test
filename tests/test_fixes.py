"""
Tests to verify the fixes for spread value mismatch and templated sayings issues
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import generate_enhanced_narrative, generate_predictions_section


def test_spread_value_uses_market_spread():
    """Test that generate_predictions_section uses market_spread instead of Predicted Outcome"""
    
    away_predictions = {
        'market_spread': -5.5,
        'Predicted Outcome': -3.0,  # Different value to ensure market_spread is used
        'Edge For Covering Spread': 0.15,
        'Moneyline Win Probability': 0.65,
        'average_total': 145.5,
        'Over Total Edge': 0.10,
        'Under Total Edge': -0.05
    }
    
    home_predictions = {
        'market_spread': 5.5,
        'Predicted Outcome': 3.0,  # Different value to ensure market_spread is used
        'Edge For Covering Spread': -0.15,
        'Moneyline Win Probability': 0.35,
        'average_total': 145.5,
        'Over Total Edge': 0.10,
        'Under Total Edge': -0.05
    }
    
    result = generate_predictions_section('Team A', 'Team B', away_predictions, home_predictions)
    
    # Check that market_spread values appear in result
    assert '-5.5' in result or '-5.50' in result, "Away market_spread should appear in predictions"
    assert '5.5' in result or '5.50' in result, "Home market_spread should appear in predictions"
    
    # Check that Predicted Outcome values do NOT appear
    assert '-3.0' not in result and '-3.00' not in result, "Predicted Outcome should not appear"
    # Note: We can't check for '3.0' or '3.00' as they might appear in other contexts
    
    print("✓ Spread values use market_spread instead of Predicted Outcome")


def test_significant_talent_gap_only_for_large_spreads():
    """Test that 'significant talent gap' only appears when spread >= 6"""
    
    # Test with small spread (< 6)
    away_stats_small = {
        'Rk': 10, 'Team': 'Team A', 'OE': 115.5, 'DE': 95.2,
        'RankOE': 20, 'RankDE': 30, 'Tempo': 72.5, 'RankTempo': 40,
        'FG2Pct': 52.3, 'FG3Pct': 36.5, 'FT_Rate': 38.2, 'FTPct': 75.4,
        'Wins': 15, 'Losses': 5, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats_small = {
        'Rk': 50, 'Team': 'Team B', 'OE': 110.2, 'DE': 98.5,
        'RankOE': 50, 'RankDE': 60, 'Tempo': 70.1, 'RankTempo': 80,
        'FG2Pct': 50.8, 'FG3Pct': 34.2, 'FT_Rate': 35.1, 'FTPct': 72.8,
        'Wins': 10, 'Losses': 10, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    away_predictions_small = {
        'market_spread': -2.5,  # Small spread
        'Opening Total': 145.5,
        'Current Moneyline': -150
    }
    
    home_predictions_small = {
        'market_spread': 2.5,
        'Opening Total': 145.5,
        'Current Moneyline': 130
    }
    
    result_small = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats_small, home_stats_small,
        away_predictions_small, home_predictions_small
    )
    
    # Should NOT contain "significant talent gap" for small spread
    assert 'significant talent gap' not in result_small, \
        "Should not use 'significant talent gap' for spreads < 6"
    
    # Test with large spread (>= 6)
    away_predictions_large = {
        'market_spread': -7.5,  # Large spread
        'Opening Total': 145.5,
        'Current Moneyline': -300
    }
    
    home_predictions_large = {
        'market_spread': 7.5,
        'Opening Total': 145.5,
        'Current Moneyline': 250
    }
    
    result_large = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats_small, home_stats_small,
        away_predictions_large, home_predictions_large
    )
    
    # SHOULD contain "significant talent gap" for large spread
    assert 'significant talent gap' in result_large, \
        "Should use 'significant talent gap' for spreads >= 6"
    
    print("✓ 'Significant talent gap' only appears for spreads >= 6")


def test_no_field_goal_reference():
    """Test that 'field goal' is not used in basketball context"""
    
    away_stats = {
        'Rk': 20, 'Team': 'Team A', 'OE': 110.5, 'DE': 100.2,
        'RankOE': 80, 'RankDE': 100, 'Tempo': 70.5, 'RankTempo': 100,
        'FG2Pct': 50.3, 'FG3Pct': 34.5, 'FT_Rate': 35.2, 'FTPct': 73.4,
        'Wins': 12, 'Losses': 8, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats = {
        'Rk': 25, 'Team': 'Team B', 'OE': 108.2, 'DE': 102.5,
        'RankOE': 90, 'RankDE': 110, 'Tempo': 69.1, 'RankTempo': 120,
        'FG2Pct': 49.8, 'FG3Pct': 33.2, 'FT_Rate': 34.1, 'FTPct': 71.8,
        'Wins': 11, 'Losses': 9, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    # Small spread to trigger the relevant code path
    away_predictions = {
        'market_spread': -2.0,
        'Opening Total': 145.5,
        'Current Moneyline': -140
    }
    
    home_predictions = {
        'market_spread': 2.0,
        'Opening Total': 145.5,
        'Current Moneyline': 120
    }
    
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Should NOT contain "field goal"
    assert 'field goal' not in result.lower(), \
        "Should not use football term 'field goal' in basketball content"
    
    # Should contain "3 points" instead
    assert '3 points' in result, \
        "Should use '3 points' instead of 'field goal'"
    
    print("✓ No 'field goal' references found, using '3 points' instead")


def test_offensive_defensive_matchup_logic():
    """Test that offensive/defensive matchups are correctly described"""
    
    # Create scenario where away team has elite offense vs weak home defense
    away_stats = {
        'Rk': 10, 'Team': 'Team A', 'OE': 120.5, 'DE': 100.2,
        'RankOE': 15, 'RankDE': 150, 'Tempo': 72.5, 'RankTempo': 40,
        'FG2Pct': 55.3, 'FG3Pct': 38.5, 'FT_Rate': 40.2, 'FTPct': 78.4,
        'Wins': 18, 'Losses': 3, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats = {
        'Rk': 50, 'Team': 'Team B', 'OE': 108.2, 'DE': 105.5,
        'RankOE': 100, 'RankDE': 220, 'Tempo': 70.1, 'RankTempo': 80,
        'FG2Pct': 50.8, 'FG3Pct': 33.2, 'FT_Rate': 33.1, 'FTPct': 70.8,
        'Wins': 10, 'Losses': 11, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    away_predictions = {
        'market_spread': -8.5,
        'Opening Total': 150.5,
        'Current Moneyline': -350
    }
    
    home_predictions = {
        'market_spread': 8.5,
        'Opening Total': 150.5,
        'Current Moneyline': 280
    }
    
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Should mention Team A's offense vs Team B's defense
    assert "Team A's offense" in result, \
        "Should mention away team's offense"
    assert "Team B's weaker defense" in result or "Team B's defensive vulnerabilities" in result, \
        "Should mention home team's defense"
    
    # Should NOT mention defensive efficiency comparing defenses
    assert "defensive efficiency) should have success against" not in result, \
        "Should not compare defense vs defense incorrectly"
    
    print("✓ Offensive/defensive matchup logic is correct")


def test_betting_angle_section_removed():
    """Test that 'The Betting Angle' section is not present"""
    
    away_stats = {
        'Rk': 20, 'Team': 'Team A', 'OE': 112.5, 'DE': 98.2,
        'RankOE': 60, 'RankDE': 80, 'Tempo': 71.5, 'RankTempo': 60,
        'FG2Pct': 52.3, 'FG3Pct': 35.5, 'FT_Rate': 36.2, 'FTPct': 74.4,
        'Wins': 14, 'Losses': 7, 'Coach': 'Coach A', 'Arena': 'Arena A'
    }
    
    home_stats = {
        'Rk': 30, 'Team': 'Team B', 'OE': 110.2, 'DE': 100.5,
        'RankOE': 75, 'RankDE': 95, 'Tempo': 70.1, 'RankTempo': 85,
        'FG2Pct': 51.8, 'FG3Pct': 34.2, 'FT_Rate': 35.1, 'FTPct': 72.8,
        'Wins': 13, 'Losses': 8, 'Coach': 'Coach B', 'Arena': 'Arena B'
    }
    
    away_predictions = {
        'market_spread': -4.5,
        'Opening Total': 145.5,
        'Current Moneyline': -180
    }
    
    home_predictions = {
        'market_spread': 4.5,
        'Opening Total': 145.5,
        'Current Moneyline': 160
    }
    
    result = generate_enhanced_narrative(
        'Team A', 'Team B',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Should NOT contain "The Betting Angle" section
    assert '#### The Betting Angle' not in result, \
        "'The Betting Angle' section should be removed"
    
    # Should NOT contain betting angle specific phrases
    assert 'sharp play' not in result, \
        "Betting angle content should be removed"
    assert 'line movement' not in result, \
        "Betting angle content should be removed"
    assert 'Laying the points makes sense' not in result, \
        "Betting angle content should be removed"
    
    print("✓ 'The Betting Angle' section has been removed")


if __name__ == '__main__':
    print("Running tests for spread value mismatch and templated sayings fixes...\n")
    
    test_spread_value_uses_market_spread()
    test_significant_talent_gap_only_for_large_spreads()
    test_no_field_goal_reference()
    test_offensive_defensive_matchup_logic()
    test_betting_angle_section_removed()
    
    print("\n✅ All tests passed!")

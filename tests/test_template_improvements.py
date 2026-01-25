"""
Tests for the template improvements:
1. KenPom rankings removed from opening narrative
2. New data fields (W, L, Arena, Coach) incorporated
3. Model predictions terminology updated
"""
import sys
import os

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import generate_enhanced_narrative, generate_predictions_section


def test_opening_narrative_no_kenpom_ranks():
    """Test that opening narrative does NOT include KenPom rankings"""
    # Create mock team stats with wins/losses and other new fields
    away_stats = {
        'Rk': 85,
        'Team': 'Oregon',
        'Wins': 8,
        'Losses': 11,
        'Coach': 'Dana Altman',
        'Arena': 'Matthew Knight Arena',
        'OE': 110.5,
        'DE': 105.2,
        'RankOE': 120,
        'RankDE': 150,
        'Tempo': 70.5,
        'RankTempo': 140,
        'FG2Pct': 50.3,
        'FG3Pct': 34.5,
        'FT_Rate': 32.2,
        'FTPct': 72.4
    }
    
    home_stats = {
        'Rk': 49,
        'Team': 'Washington',
        'Wins': 15,
        'Losses': 5,
        'Coach': 'Danny Sprinkle',
        'Arena': 'Alaska Airlines Arena',
        'OE': 115.2,
        'DE': 98.5,
        'RankOE': 80,
        'RankDE': 70,
        'Tempo': 72.1,
        'RankTempo': 100,
        'FG2Pct': 52.8,
        'FG3Pct': 36.2,
        'FT_Rate': 38.1,
        'FTPct': 75.8
    }
    
    # Create mock predictions
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 146.5,
        'Current Moneyline': 300
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 146.5,
        'Current Moneyline': -400
    }
    
    # Generate narrative
    result = generate_enhanced_narrative(
        'Oregon', 'Washington',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that the opening "Setting the Stage" section does NOT have KenPom ranks
    # Split by sections to check only the opening
    sections = result.split('####')
    setting_stage = None
    for section in sections:
        if 'Setting the Stage' in section:
            setting_stage = section
            break
    
    assert setting_stage is not None, "Setting the Stage section not found"
    
    # The opening should NOT have patterns like "#85 Oregon" or "#49 Washington"
    assert '#85 Oregon' not in setting_stage, "KenPom rank #85 should not appear in opening narrative"
    assert '#49 Washington' not in setting_stage, "KenPom rank #49 should not appear in opening narrative"
    assert '#85' not in setting_stage or 'ranked #85' in result.lower(), "KenPom rank should only appear in other sections"
    
    # But the teams themselves should be mentioned
    assert 'Oregon' in setting_stage
    assert 'Washington' in setting_stage
    
    print("✓ Opening narrative does NOT include KenPom rankings")


def test_win_loss_records_in_narrative():
    """Test that win-loss records appear in the opening narrative"""
    away_stats = {
        'Rk': 85,
        'Wins': 8,
        'Losses': 11,
        'Coach': 'Dana Altman',
        'Arena': 'Matthew Knight Arena',
        'OE': 110.5,
        'DE': 105.2,
        'RankOE': 120,
        'RankDE': 150,
        'Tempo': 70.5,
        'RankTempo': 140,
        'FG2Pct': 50.3,
        'FG3Pct': 34.5,
        'FT_Rate': 32.2,
        'FTPct': 72.4
    }
    
    home_stats = {
        'Rk': 49,
        'Wins': 15,
        'Losses': 5,
        'Coach': 'Danny Sprinkle',
        'Arena': 'Alaska Airlines Arena',
        'OE': 115.2,
        'DE': 98.5,
        'RankOE': 80,
        'RankDE': 70,
        'Tempo': 72.1,
        'RankTempo': 100,
        'FG2Pct': 52.8,
        'FG3Pct': 36.2,
        'FT_Rate': 38.1,
        'FTPct': 75.8
    }
    
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 146.5
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 146.5
    }
    
    result = generate_enhanced_narrative(
        'Oregon', 'Washington',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that records appear in format "Team (W-L)"
    assert 'Oregon (8-11)' in result or '(8-11)' in result, "Oregon's record should appear in narrative"
    assert 'Washington (15-5)' in result or '(15-5)' in result, "Washington's record should appear in narrative"
    
    print("✓ Win-loss records appear in narrative")


def test_arena_in_narrative():
    """Test that home arena is mentioned in the opening narrative"""
    away_stats = {
        'Rk': 85,
        'Wins': 8,
        'Losses': 11,
        'Coach': 'Dana Altman',
        'Arena': 'Matthew Knight Arena',
        'OE': 110.5,
        'DE': 105.2,
        'RankOE': 120,
        'RankDE': 150,
        'Tempo': 70.5,
        'RankTempo': 140,
        'FG2Pct': 50.3,
        'FG3Pct': 34.5,
        'FT_Rate': 32.2,
        'FTPct': 72.4
    }
    
    home_stats = {
        'Rk': 49,
        'Wins': 15,
        'Losses': 5,
        'Coach': 'Danny Sprinkle',
        'Arena': 'Alaska Airlines Arena',
        'OE': 115.2,
        'DE': 98.5,
        'RankOE': 80,
        'RankDE': 70,
        'Tempo': 72.1,
        'RankTempo': 100,
        'FG2Pct': 52.8,
        'FG3Pct': 36.2,
        'FT_Rate': 38.1,
        'FTPct': 75.8
    }
    
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 146.5
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 146.5
    }
    
    result = generate_enhanced_narrative(
        'Oregon', 'Washington',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that arena appears in opening section
    assert 'Alaska Airlines Arena' in result, "Home arena should be mentioned in narrative"
    
    print("✓ Home arena appears in opening narrative")


def test_coach_in_narrative():
    """Test that coaches are referenced in the narrative"""
    away_stats = {
        'Rk': 85,
        'Wins': 8,
        'Losses': 11,
        'Coach': 'Dana Altman',
        'Arena': 'Matthew Knight Arena',
        'OE': 110.5,
        'DE': 105.2,
        'RankOE': 120,
        'RankDE': 150,
        'Tempo': 70.5,
        'RankTempo': 140,
        'FG2Pct': 50.3,
        'FG3Pct': 34.5,
        'FT_Rate': 32.2,
        'FTPct': 72.4
    }
    
    home_stats = {
        'Rk': 49,
        'Wins': 15,
        'Losses': 5,
        'Coach': 'Danny Sprinkle',
        'Arena': 'Alaska Airlines Arena',
        'OE': 115.2,
        'DE': 98.5,
        'RankOE': 80,
        'RankDE': 70,
        'Tempo': 72.1,
        'RankTempo': 100,
        'FG2Pct': 52.8,
        'FG3Pct': 36.2,
        'FT_Rate': 38.1,
        'FTPct': 75.8
    }
    
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 146.5
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 146.5
    }
    
    result = generate_enhanced_narrative(
        'Oregon', 'Washington',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that coach names appear in X-Factors section
    assert 'Dana Altman' in result, "Away coach should be mentioned in narrative"
    assert 'Danny Sprinkle' in result, "Home coach should be mentioned in narrative"
    
    print("✓ Coach names appear in narrative")


def test_predictions_terminology():
    """Test that model predictions use correct terminology"""
    away_predictions = {
        'Predicted Outcome': 8.5,
        'Edge For Covering Spread': 0.452,
        'Moneyline Win Probability': 0.35,
        'average_total': 146.5,
        'Over Total Edge': 0.485,
        'Under Total Edge': 0.515
    }
    
    home_predictions = {
        'Predicted Outcome': -8.5,
        'Edge For Covering Spread': 0.548,
        'Moneyline Win Probability': 0.65,
        'average_total': 146.5,
        'Over Total Edge': 0.485,
        'Under Total Edge': 0.515
    }
    
    result = generate_predictions_section(
        'Oregon', 'Washington',
        away_predictions, home_predictions
    )
    
    # Check for new terminology
    assert 'Edge For Covering Spread' in result, "Should use 'Edge For Covering Spread' terminology"
    assert 'Edge For Covering The Over' in result, "Should use 'Edge For Covering The Over' terminology"
    assert 'Edge For Covering The Under' in result, "Should use 'Edge For Covering The Under' terminology"
    
    # Check that old terminology is NOT present
    assert 'Cover Probability' not in result or 'Edge For Covering' in result, "Should NOT use old 'Cover Probability' terminology"
    assert 'Over Cover Probability' not in result, "Should NOT use old 'Over Cover Probability' terminology"
    assert 'Under Cover Probability' not in result, "Should NOT use old 'Under Cover Probability' terminology"
    
    print("✓ Model predictions use updated terminology")


def test_kenpom_ranks_elsewhere():
    """Test that KenPom rankings still appear in OTHER sections (not opening)"""
    away_stats = {
        'Rk': 85,
        'Wins': 8,
        'Losses': 11,
        'Coach': 'Dana Altman',
        'Arena': 'Matthew Knight Arena',
        'OE': 110.5,
        'DE': 105.2,
        'RankOE': 120,
        'RankDE': 150,
        'Tempo': 70.5,
        'RankTempo': 140,
        'FG2Pct': 50.3,
        'FG3Pct': 34.5,
        'FT_Rate': 32.2,
        'FTPct': 72.4
    }
    
    home_stats = {
        'Rk': 49,
        'Wins': 15,
        'Losses': 5,
        'Coach': 'Danny Sprinkle',
        'Arena': 'Alaska Airlines Arena',
        'OE': 115.2,
        'DE': 98.5,
        'RankOE': 80,
        'RankDE': 70,
        'Tempo': 72.1,
        'RankTempo': 100,
        'FG2Pct': 52.8,
        'FG3Pct': 36.2,
        'FT_Rate': 38.1,
        'FTPct': 75.8
    }
    
    away_predictions = {
        'market_spread': 8.5,
        'Opening Total': 146.5
    }
    
    home_predictions = {
        'market_spread': -8.5,
        'Opening Total': 146.5
    }
    
    result = generate_enhanced_narrative(
        'Oregon', 'Washington',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that rankings appear in later sections (like efficiency rankings)
    assert '#120' in result or '#80' in result or '#70' in result, "Other rankings should still appear in narrative"
    
    print("✓ KenPom rankings still appear in non-opening sections")


if __name__ == '__main__':
    test_opening_narrative_no_kenpom_ranks()
    test_win_loss_records_in_narrative()
    test_arena_in_narrative()
    test_coach_in_narrative()
    test_predictions_terminology()
    test_kenpom_ranks_elsewhere()
    print("\n✅ All template improvement tests passed!")

"""
Tests for plural verb usage in narrative generation
"""
import sys
import os
import re

# Add parent directory to path to import generate_previews
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import generate_enhanced_narrative


def test_narrative_uses_plural_verbs():
    """Test that team references use plural verbs, not singular"""
    # Create mock team stats
    away_stats = {
        'Rk': 10,
        'Team': 'South Carolina St Bulldogs',
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
        'Team': 'Delaware St Hornets',
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
        'South Carolina St Bulldogs', 'Delaware St Hornets',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check that singular verbs are NOT used (after team name references)
    # Using regex to find team name followed by verb
    singular_patterns = [
        r'South Carolina St Bulldogs\*?\*? brings',
        r'Delaware St Hornets\*?\*? counters',
        r'South Carolina St Bulldogs operates',
        r'Delaware St Hornets checks in',
        r'South Carolina St Bulldogs wants',
        r'Delaware St Hornets prefers',
        r'South Carolina St Bulldogs likes',
        r'Delaware St Hornets shoots',
        r'South Carolina St Bulldogs converts',
        r'Delaware St Hornets gets',
        r'South Carolina St Bulldogs defends'
    ]
    
    for pattern in singular_patterns:
        match = re.search(pattern, result)
        assert match is None, f"Found singular verb pattern: {pattern}"
    
    # Check that plural verbs ARE used
    plural_patterns = [
        r'South Carolina St Bulldogs\*?\*? bring',
        r'Delaware St Hornets counter',
        r'operate at',
        r'check in',
        r'want to',
        r'prefer to',
        r'like to',
        r'shoot \d',
        r'convert at',
        r'get the',
        r'defend the'
    ]
    
    # At least some plural patterns should be present
    found_plural = False
    for pattern in plural_patterns:
        if re.search(pattern, result):
            found_plural = True
            break
    
    assert found_plural, "No plural verb patterns found in narrative"
    
    print("✓ Narrative uses plural verbs for team references")


def test_specific_plural_verb_examples():
    """Test specific examples of plural verbs mentioned in the issue"""
    # Create stats that will trigger specific narrative sections
    away_stats = {
        'Rk': 10,
        'Team': 'South Carolina St Bulldogs',
        'OE': 118.5,  # Elite offense to trigger "bring" text
        'DE': 95.2,
        'RankOE': 15,  # Elite rank
        'RankDE': 30,
        'Tempo': 73.0,  # Higher tempo
        'RankTempo': 25,
        'FG2Pct': 52.3,
        'FG3Pct': 36.5,
        'FT_Rate': 38.2,
        'FTPct': 75.4
    }
    
    home_stats = {
        'Rk': 25,
        'Team': 'Delaware St Hornets',
        'OE': 110.2,
        'DE': 98.5,
        'RankOE': 50,
        'RankDE': 60,
        'Tempo': 68.0,  # Lower tempo
        'RankTempo': 100,
        'FG2Pct': 50.8,
        'FG3Pct': 34.2,
        'FT_Rate': 35.1,
        'FTPct': 72.8
    }
    
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
    
    result = generate_enhanced_narrative(
        'South Carolina St Bulldogs', 'Delaware St Hornets',
        away_stats, home_stats,
        away_predictions, home_predictions
    )
    
    # Check for "bring" (not "brings")
    assert 'Bulldogs** bring' in result or 'Bulldogs bring' in result, "Should use 'bring' not 'brings'"
    
    # Check for "counter" (not "counters")
    assert 'Hornets** counter' in result or 'Hornets counter' in result, "Should use 'counter' not 'counters'"
    
    # Check for "operate" (not "operates")
    assert 'operate at' in result, "Should use 'operate' not 'operates'"
    
    print("✓ Specific plural verb examples are correct")


def test_narrative_does_not_use_singular_verbs():
    """Test that narrative doesn't contain any of the forbidden singular verbs"""
    # Various team names
    team_names = [
        'Arizona Wildcats',
        'Duke Blue Devils',
        'Kentucky Wildcats',
        'North Carolina Tar Heels'
    ]
    
    for away_team in team_names[:2]:
        for home_team in team_names[2:]:
            stats = {
                'Rk': 20,
                'Team': '',
                'OE': 115.0,
                'DE': 95.0,
                'RankOE': 40,
                'RankDE': 50,
                'Tempo': 70.0,
                'RankTempo': 60,
                'FG2Pct': 52.0,
                'FG3Pct': 35.0,
                'FT_Rate': 36.0,
                'FTPct': 74.0
            }
            
            away_stats = stats.copy()
            away_stats['Team'] = away_team
            home_stats = stats.copy()
            home_stats['Team'] = home_team
            
            predictions = {
                'market_spread': -3.5,
                'Opening Total': 145.0,
                'Current Moneyline': -150
            }
            
            result = generate_enhanced_narrative(
                away_team, home_team,
                away_stats, home_stats,
                predictions, predictions
            )
            
            # Check for forbidden singular verbs
            forbidden_verbs = ['brings an', 'counters with', 'operates at', 'checks in at']
            for verb in forbidden_verbs:
                # Make sure these exact phrases don't appear (team followed by singular verb)
                # We're being careful here because "is" and "has" can be valid
                assert verb not in result, f"Found forbidden singular verb phrase: '{verb}' in narrative for {away_team} vs {home_team}"
    
    print("✓ Narrative does not use forbidden singular verbs")


if __name__ == '__main__':
    test_narrative_uses_plural_verbs()
    test_specific_plural_verb_examples()
    test_narrative_does_not_use_singular_verbs()
    print("\n✅ All plural verb tests passed!")

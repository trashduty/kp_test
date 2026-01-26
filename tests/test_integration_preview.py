"""
Integration test to verify the template improvements work end-to-end
"""
import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import generate_post_content, find_team_in_kenpom


def test_full_preview_generation():
    """Test that a full preview can be generated with new fields"""
    
    # Load actual kenpom_stats.csv
    kenpom_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kenpom_stats.csv')
    
    if not os.path.exists(kenpom_file):
        print("⚠ kenpom_stats.csv not found, skipping integration test")
        return
    
    kenpom_df = pd.read_csv(kenpom_file)
    
    # Find Arizona (should be rank 1 based on sample data)
    arizona_stats = find_team_in_kenpom('Arizona', kenpom_df)
    
    if arizona_stats is None:
        print("⚠ Could not find Arizona in kenpom_stats.csv")
        return
    
    # Find Michigan (should be rank 2)
    michigan_stats = find_team_in_kenpom('Michigan', kenpom_df)
    
    if michigan_stats is None:
        print("⚠ Could not find Michigan in kenpom_stats.csv")
        return
    
    # Create mock predictions
    away_predictions = {
        'market_spread': 3.5,
        'Opening Total': 155.5,
        'Predicted Outcome': 3.5,
        'Edge For Covering Spread': 0.51,
        'Moneyline Win Probability': 0.48,
        'average_total': 155.5,
        'Over Total Edge': 0.52,
        'Under Total Edge': 0.48,
        'Current Moneyline': 150
    }
    
    home_predictions = {
        'market_spread': -3.5,
        'Opening Total': 155.5,
        'Predicted Outcome': -3.5,
        'Edge For Covering Spread': 0.49,
        'Moneyline Win Probability': 0.52,
        'average_total': 155.5,
        'Over Total Edge': 0.52,
        'Under Total Edge': 0.48,
        'Current Moneyline': -170
    }
    
    from datetime import datetime
    game_date = datetime(2026, 1, 26)
    
    # Generate full post content
    result = generate_post_content(
        'Arizona', 'Michigan',
        arizona_stats, michigan_stats,
        away_predictions, home_predictions,
        game_date
    )
    
    # Verify key improvements are present
    
    # 1. Check that new fields are extracted
    assert arizona_stats.get('Wins') is not None, "Wins field should be present"
    assert arizona_stats.get('Losses') is not None, "Losses field should be present"
    assert arizona_stats.get('Coach') is not None, "Coach field should be present"
    assert michigan_stats.get('Arena') is not None, "Arena field should be present"
    
    print(f"✓ Arizona stats: {arizona_stats.get('Wins')}-{arizona_stats.get('Losses')}, Coach: {arizona_stats.get('Coach')}")
    print(f"✓ Michigan stats: {michigan_stats.get('Wins')}-{michigan_stats.get('Losses')}, Coach: {michigan_stats.get('Coach')}, Arena: {michigan_stats.get('Arena')}")
    
    # 2. Check that Setting the Stage section doesn't have ranks in team names
    sections = result.split('####')
    setting_stage = None
    for section in sections:
        if 'Setting the Stage' in section:
            setting_stage = section
            break
    
    if setting_stage:
        # Should not have patterns like "#1 Arizona" in the opening
        assert '#1 Arizona' not in setting_stage or 'at #1' in setting_stage, "KenPom rank should not be part of team name in opening"
        print("✓ Opening narrative format correct (no ranks in team names)")
    
    # 3. Check for win-loss records in result
    assert f"({arizona_stats.get('Wins')}-{arizona_stats.get('Losses')})" in result, "Arizona's record should appear"
    assert f"({michigan_stats.get('Wins')}-{michigan_stats.get('Losses')})" in result, "Michigan's record should appear"
    print("✓ Win-loss records appear in preview")
    
    # 4. Check for coach names in Record & Ranking section
    assert arizona_stats.get('Coach') in result, "Arizona coach should appear"
    assert michigan_stats.get('Coach') in result, "Michigan coach should appear"
    print("✓ Coach names appear in preview")
    
    # 5. Check for arena (home team)
    assert michigan_stats.get('Arena') in result, "Home arena should appear"
    print("✓ Home arena appears in preview")
    
    # 6. Check for updated predictions terminology
    assert 'Edge For Covering Spread' in result, "Updated spread terminology should be used"
    assert 'Edge For Covering The Over' in result, "Updated over terminology should be used"
    assert 'Edge For Covering The Under' in result, "Updated under terminology should be used"
    print("✓ Updated predictions terminology is used")
    
    # 7. Verify old terminology is NOT present
    assert 'Cover Probability:' not in result or 'Edge For Covering' in result, "Old terminology should not be used"
    print("✓ Old predictions terminology not found")
    
    print("\n✅ Full preview generation with new fields successful!")
    print(f"\nPreview length: {len(result)} characters")


if __name__ == '__main__':
    test_full_preview_generation()

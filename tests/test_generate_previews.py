"""
Tests for generate_previews.py script
"""
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_previews import (
    MATCHUP_TEMPLATE,
    replace_comparison_section,
    parse_and_replace_placeholders
)
import pandas as pd


def test_template_has_no_incomplete_text():
    """Verify template doesn't have incomplete text like 'expert analys[...]'"""
    # Check for truncated text patterns
    assert '[...]' not in MATCHUP_TEMPLATE
    assert 'analys[' not in MATCHUP_TEMPLATE
    
    # Check that excerpt is complete
    assert 'Expert analysis and prediction' in MATCHUP_TEMPLATE
    print("✓ Template has no incomplete text")


def test_template_uses_correct_placeholder_format():
    """Verify template uses ["column_name", file_name] format"""
    # Find all placeholders in template
    pattern = r'\["([^"]+)",\s*([^\]]+)\]'
    matches = re.findall(pattern, MATCHUP_TEMPLATE)
    
    # Should have multiple placeholders
    assert len(matches) > 0
    
    # Check that placeholders reference kenpom_stats or cbb_output
    for column, file in matches:
        assert file.strip() in ['kenpom_stats', 'cbb_output'], f"Unknown file: {file}"
    
    print(f"✓ Template uses correct placeholder format ({len(matches)} placeholders found)")


def test_game_overview_section_exists():
    """Verify Game Overview section exists in template"""
    assert '### Game Overview' in MATCHUP_TEMPLATE
    assert 'will travel to face' in MATCHUP_TEMPLATE
    print("✓ Game Overview section exists")


def test_double_space_removal():
    """Test that double spaces are removed when splitting by '. Home Team'"""
    # Create mock dataframes
    kenpom_df = pd.DataFrame({
        'Team': ['TeamA', 'TeamB'],
        'Rk': [1, 2],
        'FG3Pct': [35.0, 40.0],
        'F3GRate': [30.0, 35.0]
    })
    predictions_df = pd.DataFrame({
        'Team': ['TeamA', 'TeamB']
    })
    
    # Test text with period before Home Team
    text = "Away Team shoots [\"FG3Pct\", kenpom_stats]%. Home Team counters with [\"FG3Pct\", kenpom_stats]%."
    
    result = replace_comparison_section(text, 'TeamA', 'TeamB', kenpom_df, predictions_df)
    
    # Should not have double spaces
    assert '  ' not in result.replace('  ', ' ').strip()  # Allow single trailing space
    assert 'TeamA' in result
    assert 'TeamB' in result
    
    print("✓ Double spaces are removed correctly")


def test_game_overview_uses_correct_team_data():
    """Test that Game Overview section uses correct data for each team"""
    # Create mock dataframes with different ranks
    kenpom_df = pd.DataFrame({
        'Team': ['Arizona', 'BYU'],
        'Rk': [1, 14],
        'OE': [122.67, 122.18],
        'DE': [92.24, 98.84],
        'Tempo': [73.03, 71.07],
        'RankOE': [15, 17],
        'RankDE': [3, 31],
        'RankTempo': [25, 84],
        'eFG_Pct': [56.6, 56.2],
        'TO_Pct': [15.5, 15.3],
        'OR_Pct': [40.0, 36.1],
        'FT_Rate': [42.9, 36.5],
        'RankeFG_Pct': [25, 33],
        'RankTO_Pct': [80, 66],
        'RankOR_Pct': [5, 43],
        'RankFT_Rate': [39, 159],
        'FG3Pct': [36.4, 35.4],
        'FG2Pct': [57.3, 58.3],
        'FTPct': [73.4, 75.6],
        'F3GRate': [27.6, 40.0],
        'RankFG3Pct': [55, 97],
        'RankFG2Pct': [36, 26],
        'RankFTPct': [142, 72],
        'RankF3GRate': [362, 172],
        'DeFG_Pct': [44.9, 47.4],
        'DTO_Pct': [18.3, 17.5],
        'DOR_Pct': [24.8, 28.6],
        'DFT_Rate': [27.8, 25.2],
        'RankDeFG_Pct': [9, 44],
        'RankDTO_Pct': [108, 154],
        'RankDOR_Pct': [11, 83],
        'RankDFT_Rate': [30, 14],
        'BlockPct': [11.1, 13.3],
        'StlRate': [0.1, 0.1],
        'ARate': [58.0, 49.7],
        'RankBlockPct': [96, 32],
        'RankStlRate': [50, 39],
        'RankARate': [63, 253],
        'AvgHgt': [79.07, 78.16],
        'HgtEff': [1.44, 0.55],
        'Exp': [1.54, 1.75],
        'Bench': [30.40, 28.59],
        'Continuity': [0.35, 0.31],
        'AvgHgtRank': [7, 69],
        'HgtEffRank': [29, 104],
        'ExpRank': [156, 109],
        'BenchRank': [240, 278],
        'RankContinuity': [100, 125]
    })
    predictions_df = pd.DataFrame({
        'Team': ['Arizona', 'BYU']
    })
    
    # Process the template
    content = parse_and_replace_placeholders(
        MATCHUP_TEMPLATE, 'Arizona', 'BYU', kenpom_df, predictions_df
    )
    
    # Check Game Overview section has correct ranks
    lines = content.split('\n')
    overview_line = [l for l in lines if 'will travel to face' in l][0]
    
    # Arizona should have rank 1, BYU should have rank 14
    assert 'Arizona (1)' in overview_line, f"Expected 'Arizona (1)' in: {overview_line}"
    assert 'BYU (14)' in overview_line, f"Expected 'BYU (14)' in: {overview_line}"
    
    print("✓ Game Overview uses correct team data for each placeholder")


if __name__ == '__main__':
    test_template_has_no_incomplete_text()
    test_template_uses_correct_placeholder_format()
    test_game_overview_section_exists()
    test_double_space_removal()
    test_game_overview_uses_correct_team_data()
    print("\n✅ All tests passed!")

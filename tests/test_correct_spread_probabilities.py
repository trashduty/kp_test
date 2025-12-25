import os
import sys
import pytest
import pandas as pd
import numpy as np
from io import StringIO

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from correct_spread_probabilities import (
    round_spread,
    check_probability_match,
    correct_spread_probabilities,
    PROBABILITY_TOLERANCE
)


class TestRoundSpread:
    """Test the round_spread function."""
    
    def test_round_to_half_point(self):
        """Test rounding to half-point increments."""
        assert round_spread(-7.5) == -7.5
        assert round_spread(-7.0) == -7.0
        assert round_spread(-6.5) == -6.5
    
    def test_round_with_float_noise(self):
        """Test rounding with floating point noise."""
        assert round_spread(-7.50001) == -7.5
        assert round_spread(-7.49999) == -7.5
        assert round_spread(-6.999999) == -7.0
        assert round_spread(-7.000001) == -7.0
    
    def test_round_positive_values(self):
        """Test rounding positive values."""
        assert round_spread(3.5) == 3.5
        assert round_spread(3.0) == 3.0
        assert round_spread(2.50001) == 2.5
    
    def test_round_nan(self):
        """Test that NaN values stay as NaN."""
        result = round_spread(np.nan)
        assert pd.isna(result)


class TestCheckProbabilityMatch:
    """Test the check_probability_match function."""
    
    def test_exact_match(self):
        """Test exact probability matches."""
        assert check_probability_match(0.5, 0.5) == 1
        assert check_probability_match(0.0, 0.0) == 1
        assert check_probability_match(1.0, 1.0) == 1
    
    def test_match_within_tolerance(self):
        """Test matches within tolerance."""
        assert check_probability_match(0.5, 0.5 + PROBABILITY_TOLERANCE / 2) == 1
        assert check_probability_match(0.5, 0.5 - PROBABILITY_TOLERANCE / 2) == 1
        # Just at the boundary
        assert check_probability_match(0.5, 0.5 + PROBABILITY_TOLERANCE) == 1
    
    def test_no_match_outside_tolerance(self):
        """Test no match when outside tolerance."""
        assert check_probability_match(0.5, 0.6) == 0
        assert check_probability_match(0.5, 0.4) == 0
        # Slightly outside tolerance
        assert check_probability_match(0.5, 0.5 + PROBABILITY_TOLERANCE * 2) == 0
    
    def test_nan_handling(self):
        """Test that NaN values result in no match."""
        assert check_probability_match(0.5, np.nan) == 0
        assert check_probability_match(np.nan, 0.5) == 0
        assert check_probability_match(np.nan, np.nan) == 0


class TestCorrectSpreadProbabilities:
    """Test the correct_spread_probabilities function."""
    
    @pytest.fixture
    def sample_lookup_table(self):
        """Create a sample lookup table."""
        data = {
            'total_category': [1, 1, 1, 1],
            'market_spread': [-7.5, -7.5, -7.0, -6.5],
            'model_spread': [-7.5, -7.0, -7.0, -6.5],
            'cover_prob': [0.5000, 0.4800, 0.5200, 0.5100],
            'push_prob': [0.0347, 0.0345, 0.0350, 0.0340],
            'not_cover_prob': [0.4653, 0.4855, 0.4450, 0.4560]
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_graded_results(self):
        """Create a sample graded results file."""
        data = {
            'team': ['Duke', 'UNC', 'Kentucky', 'Kansas'],
            'home_team': ['Duke', 'Duke', 'Kentucky', 'Kentucky'],
            'opening_spread': [-7.5, -7.5, -7.0, -6.5],
            'predicted_outcome': [-7.5, -7.0, -7.0, -6.5],
            'spread_cover_probability': [0.5000, 0.4800, 0.5200, 0.6000],
            'other_column': ['A', 'B', 'C', 'D']
        }
        return pd.DataFrame(data)
    
    def test_exact_match(self, sample_graded_results, sample_lookup_table):
        """Test correction with exact matches."""
        result = correct_spread_probabilities(sample_graded_results, sample_lookup_table)
        
        # Check that new columns were added
        assert 'spread_cover_probability_confirmed' in result.columns
        assert 'spread_cover_probability_match_flag' in result.columns
        
        # Check that all rows were matched
        assert result['spread_cover_probability_confirmed'].notna().all()
        
        # Check confirmed values
        assert result.loc[0, 'spread_cover_probability_confirmed'] == 0.5000
        assert result.loc[1, 'spread_cover_probability_confirmed'] == 0.4800
        assert result.loc[2, 'spread_cover_probability_confirmed'] == 0.5200
        assert result.loc[3, 'spread_cover_probability_confirmed'] == 0.5100
    
    def test_match_flags(self, sample_graded_results, sample_lookup_table):
        """Test that match flags are set correctly."""
        result = correct_spread_probabilities(sample_graded_results, sample_lookup_table)
        
        # Rows 0, 1, 2 should match (flag=1)
        assert result.loc[0, 'spread_cover_probability_match_flag'] == 1
        assert result.loc[1, 'spread_cover_probability_match_flag'] == 1
        assert result.loc[2, 'spread_cover_probability_match_flag'] == 1
        
        # Row 3 should not match (flag=0) - 0.6000 vs 0.5100
        assert result.loc[3, 'spread_cover_probability_match_flag'] == 0
    
    def test_unmatched_rows(self, sample_lookup_table):
        """Test handling of rows that don't match lookup table."""
        # Create results with a spread not in lookup
        data = {
            'team': ['Duke', 'UNC'],
            'opening_spread': [-7.5, -99.0],  # -99.0 not in lookup
            'predicted_outcome': [-7.5, -99.0],
            'spread_cover_probability': [0.5000, 0.5000],
        }
        results = pd.DataFrame(data)
        
        result = correct_spread_probabilities(results, sample_lookup_table)
        
        # First row should match
        assert result.loc[0, 'spread_cover_probability_confirmed'] == 0.5000
        assert result.loc[0, 'spread_cover_probability_match_flag'] == 1
        
        # Second row should not match (NaN)
        assert pd.isna(result.loc[1, 'spread_cover_probability_confirmed'])
        assert result.loc[1, 'spread_cover_probability_match_flag'] == 0
    
    def test_preserves_existing_columns(self, sample_graded_results, sample_lookup_table):
        """Test that all existing columns are preserved."""
        original_columns = set(sample_graded_results.columns)
        result = correct_spread_probabilities(sample_graded_results, sample_lookup_table)
        
        # All original columns should still be present
        for col in original_columns:
            assert col in result.columns
        
        # Check that specific column wasn't lost
        assert 'other_column' in result.columns
        assert list(result['other_column']) == ['A', 'B', 'C', 'D']
    
    def test_float_rounding(self, sample_lookup_table):
        """Test that float rounding works correctly."""
        # Create results with float noise
        data = {
            'team': ['Duke'],
            'opening_spread': [-7.50001],  # Should round to -7.5
            'predicted_outcome': [-7.49999],  # Should round to -7.5
            'spread_cover_probability': [0.5000],
        }
        results = pd.DataFrame(data)
        
        result = correct_spread_probabilities(results, sample_lookup_table)
        
        # Should match to -7.5, -7.5 in lookup
        assert result.loc[0, 'spread_cover_probability_confirmed'] == 0.5000
        assert result.loc[0, 'spread_cover_probability_match_flag'] == 1
    
    def test_missing_original_probability_column(self, sample_lookup_table):
        """Test behavior when original spread_cover_probability column doesn't exist."""
        data = {
            'team': ['Duke'],
            'opening_spread': [-7.5],
            'predicted_outcome': [-7.5],
        }
        results = pd.DataFrame(data)
        
        result = correct_spread_probabilities(results, sample_lookup_table)
        
        # Should still add confirmed column
        assert 'spread_cover_probability_confirmed' in result.columns
        assert result.loc[0, 'spread_cover_probability_confirmed'] == 0.5000
        
        # Match flag should be 0 (no original to compare)
        assert result.loc[0, 'spread_cover_probability_match_flag'] == 0


def test_integration_with_files(tmp_path):
    """Integration test using actual CSV files."""
    # Create temporary lookup table
    lookup_data = """total_category,market_spread,model_spread,cover_prob,push_prob,not_cover_prob
1,-7.5,-7.5,0.5000,0.0347,0.4653
1,-7.5,-7.0,0.4800,0.0345,0.4855
1,-7.0,-7.0,0.5200,0.0350,0.4450
"""
    lookup_path = tmp_path / "lookup.csv"
    lookup_path.write_text(lookup_data)
    
    # Create temporary graded results
    results_data = """team,opening_spread,predicted_outcome,spread_cover_probability
Duke,-7.5,-7.5,0.5000
UNC,-7.5,-7.0,0.4800
Kentucky,-7.0,-7.0,0.5200
"""
    results_path = tmp_path / "results.csv"
    results_path.write_text(results_data)
    
    # Load and process
    from correct_spread_probabilities import load_lookup_table, load_graded_results
    
    lookup_df = load_lookup_table(str(lookup_path))
    results_df = load_graded_results(str(results_path))
    corrected_df = correct_spread_probabilities(results_df, lookup_df)
    
    # Verify results
    assert len(corrected_df) == 3
    assert 'spread_cover_probability_confirmed' in corrected_df.columns
    assert 'spread_cover_probability_match_flag' in corrected_df.columns
    
    # All should match
    assert (corrected_df['spread_cover_probability_match_flag'] == 1).all()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

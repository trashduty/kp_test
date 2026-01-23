"""
Test to verify the Rk column is properly populated in kenpom_stats.csv
even when RankAdjEM field is missing from the API response.
"""

import sys
import os
import csv
import tempfile

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set a dummy API key to allow import of scrape_kenpom_stats module
# This is only used for unit testing the save_to_csv function and doesn't make any API calls
if 'KENPOM_API_KEY' not in os.environ:
    os.environ['KENPOM_API_KEY'] = 'dummy_key_for_unit_tests_only'

# Import the function we need to test
from scrape_kenpom_stats import save_to_csv


def test_save_to_csv_with_rank_field():
    """Test that Rk column is populated when RankAdjEM exists"""
    
    print("=" * 80)
    print("Test: save_to_csv with RankAdjEM field present")
    print("=" * 80)
    
    # Mock data with RankAdjEM field
    mock_data = [
        {
            'TeamName': 'Duke',
            'RankAdjEM': 1,
            'AdjOE': 120.5,
            'RankAdjOE': 5,
            'AdjDE': 95.2,
            'RankAdjDE': 10
        },
        {
            'TeamName': 'Kentucky',
            'RankAdjEM': 2,
            'AdjOE': 119.8,
            'RankAdjOE': 7,
            'AdjDE': 96.1,
            'RankAdjDE': 15
        },
        {
            'TeamName': 'Kansas',
            'RankAdjEM': 3,
            'AdjOE': 118.9,
            'RankAdjOE': 10,
            'AdjDE': 97.0,
            'RankAdjDE': 20
        }
    ]
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_file = f.name
    
    try:
        # Save to CSV
        save_to_csv(mock_data, temp_file)
        
        # Read back and verify
        with open(temp_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print(f"✓ CSV created with {len(rows)} rows")
            
            # Verify Rk column exists and has correct values
            for idx, row in enumerate(rows):
                team = row['Team']
                rk = row['Rk']
                expected_rk = str(idx + 1)
                
                print(f"  Team: {team}, Rk: {rk}")
                
                assert rk, f"Rk column is empty for {team}"
                assert rk == expected_rk, f"Expected Rk={expected_rk} for {team}, got {rk}"
            
            print("✓ All teams have correct Rk values")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("=" * 80)
    print()


def test_save_to_csv_without_rank_field():
    """Test that Rk column is populated via enumeration when RankAdjEM is missing"""
    
    print("=" * 80)
    print("Test: save_to_csv WITHOUT RankAdjEM field (enumeration fallback)")
    print("=" * 80)
    
    # Mock data WITHOUT RankAdjEM field (simulating the bug)
    mock_data = [
        {
            'TeamName': 'Duke',
            'AdjOE': 120.5,
            'RankAdjOE': 5,
            'AdjDE': 95.2,
            'RankAdjDE': 10
        },
        {
            'TeamName': 'Kentucky',
            'AdjOE': 119.8,
            'RankAdjOE': 7,
            'AdjDE': 96.1,
            'RankAdjDE': 15
        },
        {
            'TeamName': 'Kansas',
            'AdjOE': 118.9,
            'RankAdjOE': 10,
            'AdjDE': 97.0,
            'RankAdjDE': 20
        }
    ]
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_file = f.name
    
    try:
        # Save to CSV
        save_to_csv(mock_data, temp_file)
        
        # Read back and verify
        with open(temp_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print(f"✓ CSV created with {len(rows)} rows")
            
            # Verify Rk column exists and has enumerated values (1, 2, 3...)
            for idx, row in enumerate(rows):
                team = row['Team']
                rk = row['Rk']
                expected_rk = str(idx + 1)
                
                print(f"  Team: {team}, Rk: {rk} (enumerated)")
                
                assert rk, f"Rk column is empty for {team}"
                assert rk == expected_rk, f"Expected Rk={expected_rk} for {team}, got {rk}"
            
            print("✓ All teams have enumerated Rk values (1, 2, 3...)")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("=" * 80)
    print()


def test_save_to_csv_with_empty_rank_field():
    """Test that Rk column is populated via enumeration when RankAdjEM exists but is empty"""
    
    print("=" * 80)
    print("Test: save_to_csv with EMPTY RankAdjEM field (enumeration fallback)")
    print("=" * 80)
    
    # Mock data with RankAdjEM field but empty values
    mock_data = [
        {
            'TeamName': 'Duke',
            'RankAdjEM': '',  # Empty string
            'AdjOE': 120.5,
            'RankAdjOE': 5
        },
        {
            'TeamName': 'Kentucky',
            'RankAdjEM': None,  # None value
            'AdjOE': 119.8,
            'RankAdjOE': 7
        },
        {
            'TeamName': 'Kansas',
            'RankAdjEM': '',  # Empty string
            'AdjOE': 118.9,
            'RankAdjOE': 10
        }
    ]
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_file = f.name
    
    try:
        # Save to CSV
        save_to_csv(mock_data, temp_file)
        
        # Read back and verify
        with open(temp_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print(f"✓ CSV created with {len(rows)} rows")
            
            # Verify Rk column exists and has enumerated values (1, 2, 3...)
            for idx, row in enumerate(rows):
                team = row['Team']
                rk = row['Rk']
                expected_rk = str(idx + 1)
                
                print(f"  Team: {team}, Rk: {rk} (enumerated due to empty RankAdjEM)")
                
                assert rk, f"Rk column is empty for {team}"
                assert rk == expected_rk, f"Expected Rk={expected_rk} for {team}, got {rk}"
            
            print("✓ All teams have enumerated Rk values despite empty RankAdjEM")
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        test_save_to_csv_with_rank_field()
        test_save_to_csv_without_rank_field()
        test_save_to_csv_with_empty_rank_field()
        
        print()
        print("=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ save_to_csv correctly uses RankAdjEM when present")
        print("  ✓ save_to_csv falls back to enumeration when RankAdjEM is missing")
        print("  ✓ save_to_csv falls back to enumeration when RankAdjEM is empty")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

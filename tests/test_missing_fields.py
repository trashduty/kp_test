#!/usr/bin/env python3
"""
Test to verify that the missing fields (Coach, Wins, Losses, Arena, ArenaCity, ArenaState)
are now included in the kenpom_stats.csv header and rows.
"""

import sys
import os
import csv
import tempfile

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set a dummy API key to allow import of scrape_kenpom_stats module
if 'KENPOM_API_KEY' not in os.environ:
    os.environ['KENPOM_API_KEY'] = 'dummy_key_for_unit_tests_only'

# Import the function we need to test
from scrape_kenpom_stats import save_to_csv


def test_missing_fields_in_header():
    """Test that Coach, Wins, Losses, Arena, ArenaCity, ArenaState are in header"""
    
    print("=" * 80)
    print("Test: Verify missing fields are now included in CSV")
    print("=" * 80)
    print()
    
    # Mock data with the new fields
    mock_data = [
        {
            'TeamName': 'Duke',
            'RankAdjEM': 1,
            'AdjOE': 120.5,
            'RankAdjOE': 5,
            'AdjDE': 95.2,
            'RankAdjDE': 15,
            'Coach': 'Jon Scheyer',
            'Wins': 20,
            'Losses': 3,
            'Arena': 'Cameron Indoor Stadium',
            'ArenaCity': 'Durham',
            'ArenaState': 'NC'
        },
        {
            'TeamName': 'Kentucky',
            'RankAdjEM': 2,
            'AdjOE': 119.8,
            'RankAdjOE': 7,
            'AdjDE': 96.1,
            'RankAdjDE': 20,
            'Coach': 'Mark Pope',
            'Wins': 18,
            'Losses': 4,
            'Arena': 'Rupp Arena',
            'ArenaCity': 'Lexington',
            'ArenaState': 'KY'
        }
    ]
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
    
    try:
        # Call save_to_csv with mock data
        save_to_csv(mock_data, tmp_filename)
        
        # Read the CSV and verify header contains the new fields
        with open(tmp_filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            
            # Check that the new fields are in the header
            required_fields = ['Coach', 'Wins', 'Losses', 'Arena', 'ArenaCity', 'ArenaState']
            
            print("Checking for required fields in CSV header...")
            missing_fields = []
            for field in required_fields:
                if field in header:
                    print(f"  ✓ {field} is in header")
                else:
                    print(f"  ✗ {field} is MISSING from header")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"\n❌ Test FAILED: Missing fields: {missing_fields}")
                sys.exit(1)
            
            print("\n✅ All required fields are in the header")
            
            # Verify data is populated
            print("\nVerifying data is populated in rows...")
            rows = list(reader)
            
            if len(rows) < 2:
                print(f"❌ Expected 2 rows, got {len(rows)}")
                sys.exit(1)
            
            # Check first team
            first_team = rows[0]
            print(f"\nFirst team data:")
            print(f"  Team: {first_team.get('Team')}")
            print(f"  Coach: {first_team.get('Coach')}")
            print(f"  Wins: {first_team.get('Wins')}")
            print(f"  Losses: {first_team.get('Losses')}")
            print(f"  Arena: {first_team.get('Arena')}")
            print(f"  ArenaCity: {first_team.get('ArenaCity')}")
            print(f"  ArenaState: {first_team.get('ArenaState')}")
            
            # Verify the values match expected
            if first_team.get('Coach') != 'Jon Scheyer':
                print(f"❌ Expected Coach='Jon Scheyer', got '{first_team.get('Coach')}'")
                sys.exit(1)
            
            if first_team.get('Wins') != '20':
                print(f"❌ Expected Wins='20', got '{first_team.get('Wins')}'")
                sys.exit(1)
                
            if first_team.get('Arena') != 'Cameron Indoor Stadium':
                print(f"❌ Expected Arena='Cameron Indoor Stadium', got '{first_team.get('Arena')}'")
                sys.exit(1)
            
            print("\n✅ Data is correctly populated in rows")
            
    finally:
        # Clean up temp file
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
    
    print()
    print("=" * 80)
    print("✅ TEST PASSED: All required fields are included and populated")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        test_missing_fields_in_header()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

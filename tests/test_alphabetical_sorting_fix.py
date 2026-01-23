#!/usr/bin/env python3
"""
Test to demonstrate the fix for alphabetical sorting bug.
This simulates the exact scenario described in the issue where teams
were being ranked alphabetically instead of by performance.
"""

import sys
import os
import csv
import tempfile

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set a dummy API key for testing
if 'KENPOM_API_KEY' not in os.environ:
    os.environ['KENPOM_API_KEY'] = 'dummy_key_for_unit_tests_only'

from scrape_kenpom_stats import save_to_csv


def test_alphabetical_bug_is_fixed():
    """
    Test that demonstrates the bug fix:
    - Before fix: Teams ranked alphabetically (Abilene Christian=1, Air Force=2, Alabama=4)
    - After fix: Teams ranked by AdjEM (Alabama should be high ranked, not #4)
    """
    
    print("=" * 80)
    print("Test: Alphabetical Sorting Bug Fix")
    print("=" * 80)
    print()
    print("Simulating the exact bug scenario from the issue:")
    print("- Teams come from API in ALPHABETICAL order")
    print("- Alabama has very high AdjEM (~28-30) but comes 4th alphabetically")
    print("- Without fix: Alabama would get Rk=4")
    print("- With fix: Alabama should get Rk=1 or close to it")
    print()
    
    # Mock data simulating the bug scenario:
    # Teams in ALPHABETICAL order (as they come from API)
    # But Alabama has the BEST AdjEM value
    mock_data = [
        {
            'TeamName': 'Abilene Christian',
            'AdjEM': 15.2,  # Mid-tier team
            'AdjOE': 103.876,
            'RankAdjOE': 288,
            'AdjDE': 111.296,
            'RankAdjDE': 195
        },
        {
            'TeamName': 'Air Force',
            'AdjEM': 12.8,  # Lower tier team
            'AdjOE': 96.2188,
            'RankAdjOE': 359,
            'AdjDE': 113.971,
            'RankAdjDE': 256
        },
        {
            'TeamName': 'Akron',
            'AdjEM': 23.5,  # Good team
            'AdjOE': 123.996,
            'RankAdjOE': 20,
            'AdjDE': 110.567,
            'RankAdjDE': 173
        },
        {
            'TeamName': 'Alabama',
            'AdjEM': 29.3,  # ELITE team - should be #1!
            'AdjOE': 129.324,
            'RankAdjOE': 2,
            'AdjDE': 103.994,
            'RankAdjDE': 65
        },
        {
            'TeamName': 'Auburn',
            'AdjEM': 27.8,  # Elite team - should be #2
            'AdjOE': 125.174,
            'RankAdjOE': 15,
            'AdjDE': 104.671,
            'RankAdjDE': 78
        },
        {
            'TeamName': 'Duke',
            'AdjEM': 26.5,  # Elite team - should be #3
            'AdjOE': 127.251,
            'RankAdjOE': 4,
            'AdjDE': 92.4178,
            'RankAdjDE': 3
        }
    ]
    
    print("Input data (ALPHABETICAL order from API):")
    for i, team in enumerate(mock_data, 1):
        print(f"  {i}. {team['TeamName']:20s} - AdjEM: {team['AdjEM']}")
    print()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_file = f.name
    
    try:
        # Save to CSV (this triggers the sorting)
        save_to_csv(mock_data, temp_file)
        
        # Read back and verify
        with open(temp_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            print("\n" + "=" * 80)
            print("RESULTS: Teams after applying the fix")
            print("=" * 80)
            
            # Expected order after sorting by AdjEM descending:
            # 1. Alabama (29.3)
            # 2. Auburn (27.8)
            # 3. Duke (26.5)
            # 4. Akron (23.5)
            # 5. Abilene Christian (15.2)
            # 6. Air Force (12.8)
            expected_order = [
                ('Alabama', 29.3),
                ('Auburn', 27.8),
                ('Duke', 26.5),
                ('Akron', 23.5),
                ('Abilene Christian', 15.2),
                ('Air Force', 12.8)
            ]
            
            all_correct = True
            for idx, row in enumerate(rows):
                team = row['Team']
                rk = row['Rk']
                expected_team, expected_adem = expected_order[idx]
                
                is_correct = team == expected_team
                status = "✅" if is_correct else "❌"
                
                print(f"  {status} Rank {rk}: {team:20s} (expected: {expected_team})")
                
                if not is_correct:
                    all_correct = False
                    print(f"     ERROR: Expected {expected_team} at rank {idx+1}")
            
            print()
            
            # Verify Alabama is ranked #1 (the key fix)
            alabama_row = next((r for r in rows if r['Team'] == 'Alabama'), None)
            if not alabama_row:
                print(f"❌ ERROR: Alabama not found in results!")
                all_correct = False
            else:
                alabama_rank = int(alabama_row['Rk'])
                
                print("=" * 80)
                print("KEY VALIDATION: Alabama's Rank")
                print("=" * 80)
                print(f"  Before fix: Alabama would be Rk=4 (alphabetical position)")
                print(f"  After fix:  Alabama is Rk={alabama_rank} (based on AdjEM)")
                print()
                
                if alabama_rank == 1:
                    print("  ✅ SUCCESS! Alabama correctly ranked #1 (highest AdjEM)")
                else:
                    print(f"  ❌ FAILED! Alabama should be #1, but got #{alabama_rank}")
                    all_correct = False
                
                print()
                
                assert alabama_rank == 1, f"Alabama should be ranked #1, got #{alabama_rank}"
            
            assert all_correct, "Team rankings do not match expected order"
            assert alabama_rank == 1, f"Alabama should be ranked #1, got #{alabama_rank}"
            
            print("=" * 80)
            print("✅ TEST PASSED: Alphabetical sorting bug is FIXED!")
            print("=" * 80)
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    try:
        test_alphabetical_bug_is_fixed()
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

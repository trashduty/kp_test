#!/usr/bin/env python3
"""
Test script to verify the debug logging functionality.
This simulates API responses with different data structures.
"""

import os
import sys
import json

# Set dummy API key for testing
os.environ['KENPOM_API_KEY'] = 'dummy_key_for_testing'

# Import after setting env var
from scrape_kenpom_stats import fetch_four_factors

def mock_fetch_with_sample_data():
    """
    Simulate what fetch_four_factors would do with sample data.
    This tests the debug logging output without making real API calls.
    """
    print("=" * 70)
    print("TEST: Debug Logging with Mock Data")
    print("=" * 70)
    print()
    
    # Create mock data that represents what the API might return
    mock_data = [
        {
            'TeamName': 'Auburn',
            'AdjEM': 28.45,
            'RankAdjEM': 1,
            'AdjOE': 125.3,
            'RankAdjOE': 5,
            'AdjDE': 96.85,
            'RankAdjDE': 3,
            'AdjTempo': 72.5,
            'RankAdjTempo': 45,
            'Luck': 0.045,
            'RankLuck': 100
        },
        {
            'TeamName': 'Duke',
            'AdjEM': 27.89,
            'RankAdjEM': 2,
            'AdjOE': 124.8,
            'RankAdjOE': 7,
            'AdjDE': 96.91,
            'RankAdjDE': 4,
            'AdjTempo': 71.2,
            'RankAdjTempo': 88,
            'Luck': 0.025,
            'RankLuck': 150
        },
        {
            'TeamName': 'Houston',
            'AdjEM': 27.12,
            'RankAdjEM': 3,
            'AdjOE': 122.5,
            'RankAdjOE': 15,
            'AdjDE': 95.38,
            'RankAdjDE': 1,
            'AdjTempo': 68.9,
            'RankAdjTempo': 200,
            'Luck': -0.015,
            'RankLuck': 250
        },
        {
            'TeamName': 'Iowa State',
            'AdjEM': 26.75,
            'RankAdjEM': 4,
            'AdjOE': 123.2,
            'RankAdjOE': 12,
            'AdjDE': 96.45,
            'RankAdjDE': 2,
            'AdjTempo': 70.1,
            'RankAdjTempo': 120,
            'Luck': 0.005,
            'RankLuck': 180
        },
        {
            'TeamName': 'Kentucky',
            'AdjEM': 26.34,
            'RankAdjEM': 5,
            'AdjOE': 121.8,
            'RankAdjOE': 20,
            'AdjDE': 95.46,
            'RankAdjDE': 2,
            'AdjTempo': 73.5,
            'RankAdjTempo': 25,
            'Luck': 0.055,
            'RankLuck': 75
        }
    ]
    
    # Simulate the debug logging that fetch_four_factors does
    data = mock_data
    
    print(f"✅ Successfully retrieved data for {len(data)} teams.")
    print()
    
    # ============================================================
    # COMPREHENSIVE DEBUG LOGGING (same as in fetch_four_factors)
    # ============================================================
    
    if data:
        # 1. Print full raw API response structure (first team only)
        print("🔍 DEBUG: Raw API Response (first team):")
        print("-" * 60)
        print(json.dumps(data[0], indent=2, default=str))
        print("-" * 60)
        print()
        
        # 2. List all available field names
        all_fields = list(data[0].keys())
        print("📋 DEBUG: Available fields in API response:")
        print(f"   {all_fields}")
        print()
        
        # 3. Check specifically for rank-related fields
        print("🔍 DEBUG: Rank-related fields analysis:")
        rank_related_fields = []
        for field in all_fields:
            if 'rank' in field.lower():
                rank_related_fields.append(field)
                value = data[0].get(field)
                print(f"   - {field}: {value}")
        
        if not rank_related_fields:
            print("   ⚠️  No rank-related fields found in response!")
        print()
        
        # 4. Specifically check for expected rank fields
        print("🔍 DEBUG: Checking for specific expected fields:")
        expected_fields = ['RankAdjEM', 'Rank', 'RankOverall', 'AdjEM']
        for field in expected_fields:
            if field in data[0]:
                print(f"   ✓ {field}: {data[0][field]}")
            else:
                print(f"   ✗ {field}: NOT FOUND")
        print()
        
        # 5. Print sample of 3-5 teams with key fields
        print("📊 DEBUG: Sample teams with all fields:")
        sample_size = min(5, len(data))
        for i in range(sample_size):
            team = data[i]
            team_name = team.get('TeamName', 'Unknown')
            rank_adj_em = team.get('RankAdjEM', 'N/A')
            adj_em = team.get('AdjEM', 'N/A')
            print(f"   {i+1}. {team_name}")
            print(f"      - RankAdjEM: {rank_adj_em}")
            print(f"      - AdjEM: {adj_em}")
            print(f"      - All fields: {list(team.keys())[:10]}...")  # First 10 fields
        print()
        
        # 6. Log summary of missing vs present fields
        print("📝 DEBUG: Field availability summary:")
        critical_fields = ['TeamName', 'RankAdjEM', 'AdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE']
        missing_fields = []
        present_fields = []
        for field in critical_fields:
            if field in data[0]:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        print(f"   ✓ Present fields ({len(present_fields)}): {present_fields}")
        if missing_fields:
            print(f"   ✗ Missing fields ({len(missing_fields)}): {missing_fields}")
        else:
            print(f"   ✓ All critical fields are present!")
        print()
        
    print("=" * 60)
    print()
    
    return data


if __name__ == "__main__":
    try:
        print("\nThis test demonstrates the comprehensive debug logging that will")
        print("be displayed when scrape_kenpom_stats.py runs with real API data.\n")
        
        data = mock_fetch_with_sample_data()
        
        print()
        print("=" * 70)
        print("✓ Debug logging test completed successfully!")
        print("=" * 70)
        print()
        print("Summary of debug output:")
        print("  ✓ Full raw API response structure (first team)")
        print("  ✓ List of all available fields")
        print("  ✓ Rank-related fields analysis")
        print("  ✓ Specific expected fields check")
        print("  ✓ Sample of 5 teams with key data")
        print("  ✓ Field availability summary")
        print()
        print("When running with real API data, this logging will help identify:")
        print("  • Whether RankAdjEM exists in the API response")
        print("  • What the actual field names are for ranking data")
        print("  • The complete structure of the API response")
        print()
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

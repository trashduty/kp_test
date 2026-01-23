# Debug Logging Implementation

## Overview

This document explains the comprehensive debug logging added to `scrape_kenpom_stats.py` to help diagnose issues with KenPom API ranking data.

## What Was Added

The `fetch_ratings()` function now includes extensive debug logging that displays:

### 1. Full Raw API Response (First Team)
- Pretty-printed JSON structure of the first team's data
- Shows exact field names and values as returned by the API
- Uses `json.dumps()` with indentation for readability

### 2. Available Fields List
- Complete list of all field names present in the API response
- Helps identify what data is actually available from the API

### 3. Rank-Related Fields Analysis
- Automatically detects all fields containing "rank" in the name
- Shows the value for each rank-related field
- Warns if no rank-related fields are found

### 4. Specific Expected Fields Check
- Checks for: `RankAdjEM`, `Rank`, `RankOverall`, `AdjEM`
- Shows checkmark (✓) if present, X (✗) if missing
- Displays actual values for fields that exist

### 5. Sample Teams Data
- Shows data for first 3-5 teams
- Includes team name, RankAdjEM, AdjEM values
- Lists available fields for each team

### 6. Field Availability Summary
- Checks critical fields: `TeamName`, `RankAdjEM`, `AdjEM`, `AdjOE`, `RankAdjOE`, `AdjDE`, `RankAdjDE`
- Reports which fields are present vs. missing
- Confirms if all critical fields are available

## Example Output

```
🚀 Fetching Ratings data for 2026...
✅ Successfully retrieved data for 365 teams.

🔍 DEBUG: Raw API Response (first team):
------------------------------------------------------------
{
  "TeamName": "Auburn",
  "AdjEM": 28.45,
  "RankAdjEM": 1,
  "AdjOE": 125.3,
  "RankAdjOE": 5,
  "AdjDE": 96.85,
  "RankAdjDE": 3,
  "AdjTempo": 72.5,
  "RankAdjTempo": 45,
  "Luck": 0.045,
  "RankLuck": 100
}
------------------------------------------------------------

📋 DEBUG: Available fields in API response:
   ['TeamName', 'AdjEM', 'RankAdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE', 'AdjTempo', 'RankAdjTempo', 'Luck', 'RankLuck']

🔍 DEBUG: Rank-related fields analysis:
   - RankAdjEM: 1
   - RankAdjOE: 5
   - RankAdjDE: 3
   - RankAdjTempo: 45
   - RankLuck: 100

🔍 DEBUG: Checking for specific expected fields:
   ✓ RankAdjEM: 1
   ✗ Rank: NOT FOUND
   ✗ RankOverall: NOT FOUND
   ✓ AdjEM: 28.45

📊 DEBUG: Sample teams with all fields:
   1. Auburn
      - RankAdjEM: 1
      - AdjEM: 28.45
      - All fields: ['TeamName', 'AdjEM', 'RankAdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE', 'AdjTempo', 'RankAdjTempo', 'Luck']...
   2. Duke
      - RankAdjEM: 2
      - AdjEM: 27.89
      - All fields: ['TeamName', 'AdjEM', 'RankAdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE', 'AdjTempo', 'RankAdjTempo', 'Luck']...

📝 DEBUG: Field availability summary:
   ✓ Present fields (7): ['TeamName', 'RankAdjEM', 'AdjEM', 'AdjOE', 'RankAdjOE', 'AdjDE', 'RankAdjDE']
   ✓ All critical fields are present!

============================================================
```

## How to Use

Simply run the scraper as normal:

```bash
python scrape_kenpom_stats.py
```

The debug output will automatically display before the CSV file is created. This allows you to:

1. Verify the API is returning the expected fields
2. Confirm `RankAdjEM` exists and has correct values
3. Identify any discrepancies in field names
4. Understand the full API response structure

## Testing

A comprehensive test file is available at `tests/test_debug_logging.py` that demonstrates the debug output with mock data. Run it with:

```bash
python tests/test_debug_logging.py
```

## No Functional Changes

**Important:** This update only ADDS debug logging. No existing functionality has been changed:

- CSV writing logic remains unchanged
- Field mappings are still the same
- The `save_to_csv()` function works exactly as before
- All existing tests pass without modification

## Next Steps

Once the debug output reveals the actual API response structure, follow-up changes can be made to:

1. Fix any incorrect field mappings
2. Properly use the `RankAdjEM` field for the `Rk` column
3. Address any missing or misnamed fields
4. Ensure teams are ranked correctly in the output CSV

# Grade Spread Predictions Script

This Python script grades spread predictions from the `trashduty/cbb` repository's `graded_results.csv` file.

## Overview

The script reads basketball game data, filters predictions based on specific criteria, calculates whether teams covered the spread, and outputs the results to a CSV file.

## Requirements

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - requests
  - rich

## Usage

```bash
python grade_spread_predictions.py
```

## Features

1. **Fetch Data**: Retrieves `graded_results.csv` from the `trashduty/cbb` repository via GitHub API
2. **Filter Data**: Filters for rows where:
   - `spread_consensus_flag == 1`
   - `spread_edge >= 0.04`
3. **Calculate Coverage**: Determines if teams covered the spread based on:
   - **Home team** covers if: `actual_spread > opening_spread`
   - **Away team** covers if: `actual_spread < opening_spread`
   - **Push** if: `actual_spread == opening_spread`
4. **Output Results**: Adds a "Covered" column with values:
   - `0` = did not cover
   - `1` = covered
   - `2` = push
5. **Save to CSV**: Saves filtered results to `filtered_graded_results.csv`

## Authentication

The script supports optional GitHub authentication for accessing private repositories:

```bash
export GITHUB_TOKEN="your_github_token_here"
python grade_spread_predictions.py
```

If the GitHub API is unavailable or returns an error, the script will automatically fall back to using a local `graded_results.csv` file if present.

## Input Data Format

The script expects the following columns in the input CSV:
- `team` - Name of the team being evaluated
- `home_team` - Name of the home team
- `away_team` - Name of the away team
- `home_score` - Final score of the home team
- `away_score` - Final score of the away team
- `opening_spread` - The opening point spread
- `spread_consensus_flag` - Filter flag (1 or 0)
- `spread_edge` - Edge value for filtering

## Output

The script creates `filtered_graded_results.csv` with all input columns plus:
- `Covered` - Coverage result (0, 1, or 2)

## Examples

### Home Team Coverage
```
Team: Duke (Home)
Score: 85-80 (Duke wins)
Opening Spread: 3.5
Actual Spread: 5 (85-80)
Result: Covered (1) because 5 > 3.5
```

### Away Team Coverage
```
Team: Kentucky (Away)
Score: 78-75 (Kansas wins at home)
Opening Spread: 2.0
Actual Spread: 3 (78-75)
Result: Did Not Cover (0) because 3 >= 2.0
```

### Push
```
Team: Syracuse (Home)
Score: 85-82
Opening Spread: 3.0
Actual Spread: 3 (85-82)
Result: Push (2) because 3 == 3.0
```

## Error Handling

- If GitHub API access fails, the script attempts to use a local file
- Missing required columns will cause the script to fail with a clear error message
- Network timeouts are set to 30 seconds to prevent hanging

## License

This script is part of the KenPom efficiency plots repository and follows the same license terms.

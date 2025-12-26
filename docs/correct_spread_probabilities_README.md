# Correct Spread Probabilities Script

This Python script corrects spread cover probabilities in graded results by looking them up from the canonical spreads lookup table.

## Overview

The script reads basketball game data from graded results, matches each row to the canonical lookup table based on opening spread and predicted outcome, and adds two new columns with corrected probability values and a match flag indicating whether the original values were correct.

## Requirements

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - numpy
  - rich

## Usage

### Basic Usage

```bash
python correct_spread_probabilities.py <graded_results.csv>
```

This will create an output file with the suffix `_with_confirmed_spreads.csv`.

### Custom Output Path

```bash
python correct_spread_probabilities.py <graded_results.csv> -o <output_path.csv>
```

### Custom Lookup Table

```bash
python correct_spread_probabilities.py <graded_results.csv> -l path/to/custom_lookup.csv
```

### Examples

```bash
# Process graded results with default output name
python correct_spread_probabilities.py graded_results.csv

# Specify custom output path
python correct_spread_probabilities.py graded_results.csv -o corrected_results.csv

# Use different lookup table
python correct_spread_probabilities.py graded_results.csv -l custom_lookup.csv -o output.csv
```

## How It Works

### Data Mapping

The script maps graded results to the canonical lookup table using the following fields:

- **`opening_spread`** in graded results → **`market_spread`** in lookup table
- **`predicted_outcome`** in graded results → **`model_spread`** in lookup table

Both spreads are rounded to one decimal place (half-point increments) to handle floating-point precision issues. For example:
- `-7.50001` rounds to `-7.5`
- `-7.49999` rounds to `-7.5`
- `-6.999999` rounds to `-7.0`

### Lookup Process

1. The script loads the canonical lookup table from `docs/spreads_lookup_combined.csv`
2. It filters the lookup table to only spread rows (where `total_category == 1`)
3. For each row in graded results:
   - Rounds `opening_spread` and `predicted_outcome` to one decimal place
   - Looks up the matching `(market_spread, model_spread)` pair in the lookup table
   - Retrieves the `cover_prob` value

### Output Columns

The script adds two new columns to the graded results:

#### `spread_cover_probability_confirmed`

The canonical cover probability from the lookup table. This value represents the historically accurate probability that the spread will be covered based on the market spread and model prediction.

- **Type**: Float (0.0 to 1.0)
- **NaN**: If no matching row is found in the lookup table

#### `spread_cover_probability_match_flag`

An integer flag indicating whether the original `spread_cover_probability` matches the confirmed value.

- **1**: Original value matches confirmed value within tolerance (`1e-9`)
- **0**: Original value does NOT match confirmed value, or original column doesn't exist, or no match found

### Match Flag Logic

The match flag uses a numerical tolerance of `1e-9` (0.000000001) to account for floating-point precision:

```python
if abs(original_value - confirmed_value) <= 1e-9:
    match_flag = 1
else:
    match_flag = 0
```

Examples:
- `0.5000` vs `0.5000` → Match (flag = 1)
- `0.5000` vs `0.50000000001` → Match (flag = 1)
- `0.5000` vs `0.5001` → No match (flag = 0)
- `0.5000` vs `NaN` → No match (flag = 0)

## Input Data Format

### Graded Results CSV

The script expects the following columns in the input CSV:

- **`opening_spread`** (required) - The opening point spread for the game
- **`predicted_outcome`** (required) - The model's predicted spread outcome
- **`spread_cover_probability`** (optional) - Original probability values to compare against
- Any other columns - These are preserved in the output

### Lookup Table CSV

The lookup table must have the following columns:

- **`total_category`** - Category identifier (1 for spreads)
- **`market_spread`** - Market spread value
- **`model_spread`** - Model prediction spread value
- **`cover_prob`** - Cover probability to retrieve

## Output

The script creates a CSV file with:
- All original columns from the graded results (preserved unchanged)
- **`spread_cover_probability_confirmed`** - New column with canonical probabilities
- **`spread_cover_probability_match_flag`** - New column with match indicators

### Console Output

The script provides detailed logging output including:

```
[1/4] Loading lookup table...
✓ Loaded lookup table with 174243 rows

[2/4] Loading graded results...
✓ Loaded graded results with 1234 rows

[3/4] Correcting probabilities...
✓ Probability correction complete:
    Matched rows: 1200
    Unmatched rows: 34
    Original values matching confirmed: 800
    Original values NOT matching confirmed: 400

[4/4] Saving corrected results...
✓ Successfully saved corrected results to graded_results_with_confirmed_spreads.csv
```

## Edge Cases and Error Handling

### Missing Matches

If a combination of `(opening_spread, predicted_outcome)` doesn't exist in the lookup table:
- `spread_cover_probability_confirmed` will be `NaN`
- `spread_cover_probability_match_flag` will be `0`
- The script logs how many rows failed to match

### Missing Original Probability Column

If the input graded results don't have a `spread_cover_probability` column:
- `spread_cover_probability_confirmed` is still populated
- `spread_cover_probability_match_flag` will be `0` for all rows
- A warning is logged

### File Not Found

If the lookup table or graded results file doesn't exist:
- The script exits with an error message
- Exit code 1 is returned

### Missing Required Columns

If required columns are missing from either file:
- The script exits with a clear error message
- Lists which columns are missing

## Data Quality Monitoring

The script reports:
- Total number of matched rows
- Total number of unmatched rows (for data quality monitoring)
- Number of original values that matched vs didn't match

This information helps identify:
- Data quality issues in the graded results
- Missing combinations in the lookup table
- Incorrect probability calculations in the original data

## Spreads Only

**Important**: This script only processes spreads, not totals or moneylines. The lookup table is filtered to `total_category == 1` (spreads only). Totals and moneyline logic are intentionally ignored as per the requirements.

## Examples

### Example Input (graded_results.csv)

```csv
team,home_team,opening_spread,predicted_outcome,spread_cover_probability
Duke,Duke,-7.5,-7.5,0.5000
UNC,Duke,-7.5,-7.0,0.4800
Kentucky,Kentucky,-7.0,-7.0,0.5000
```

### Example Output (graded_results_with_confirmed_spreads.csv)

```csv
team,home_team,opening_spread,predicted_outcome,spread_cover_probability,spread_cover_probability_confirmed,spread_cover_probability_match_flag
Duke,Duke,-7.5,-7.5,0.5000,0.5000,1
UNC,Duke,-7.5,-7.0,0.4800,0.4800,1
Kentucky,Kentucky,-7.0,-7.0,0.5000,0.5200,0
```

In this example:
- Duke and UNC rows have matching probabilities (flag = 1)
- Kentucky row has a mismatch: original was 0.5000 but canonical is 0.5200 (flag = 0)

## Testing

The script includes comprehensive unit tests in `tests/test_correct_spread_probabilities.py`.

### Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run tests
pytest tests/test_correct_spread_probabilities.py -v
```

### Test Coverage

- Spread rounding with floating-point noise
- Probability matching within tolerance
- Exact matches and mismatches
- Unmatched rows (NaN handling)
- Column preservation
- Missing original probability column

### Test Data

Sample test data files are provided:
- `tests/test_data_lookup.csv` - Sample lookup table
- `tests/test_data_graded_results.csv` - Sample graded results

You can run the script on these files to verify behavior:

```bash
python correct_spread_probabilities.py tests/test_data_graded_results.csv -l tests/test_data_lookup.csv
```

## Performance Considerations

The script uses pandas merge operations which are optimized for large datasets. It can efficiently process:
- Lookup tables with 100,000+ rows
- Graded results with 10,000+ rows

The half-point rounding is applied only once per file, minimizing computational overhead.

## Integration with Existing Pipeline

This script is designed to integrate easily into the existing data pipeline:

1. **As a standalone step**: Run after grading results to add corrected probabilities
2. **As part of a workflow**: Chain with other scripts using bash or Python
3. **In automated pipelines**: Use in GitHub Actions or cron jobs

Example pipeline integration:

```bash
# Grade predictions
python grade_spread_predictions.py

# Correct spread probabilities
python correct_spread_probabilities.py filtered_graded_results.csv

# Analyze performance with corrected data
python analyze_model_performance.py
```

## Numerical Precision

This implementation prioritizes numerical precision as the business operates on tight edges:

- Uses `1e-9` tolerance for probability comparisons (sub-nanopercent precision)
- Rounds spreads consistently to one decimal place
- Uses pandas' native float handling to minimize precision loss
- Does not perform unnecessary conversions or operations on probability values

## License

This script is part of the KenPom efficiency plots repository and follows the same license terms.

## Troubleshooting

### "File not found" errors

Ensure you're running the script from the repository root and that file paths are correct.

### "Missing required columns" errors

Verify that your graded results CSV has `opening_spread` and `predicted_outcome` columns.

### High number of unmatched rows

This indicates:
- Spreads in your graded results that don't exist in the lookup table
- Data quality issues (invalid spread values, extreme outliers)
- Need to update the lookup table with additional spread combinations

### All match flags are 0

This indicates:
- The original `spread_cover_probability` column doesn't exist, or
- All original probabilities are incorrect, or
- There's a systematic issue with the original probability calculation

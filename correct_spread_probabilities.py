import os
import sys
import argparse
import pandas as pd
import numpy as np
from rich.console import Console
from rich.logging import RichHandler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")
console = Console()

"""
Correct Spread Probabilities Script

This script corrects spread cover probabilities in graded results by looking them up
from the canonical spreads lookup table.

Requirements:
1. Load canonical lookup table from docs/spreads_lookup_combined.csv
2. Load graded results CSV (path provided via CLI)
3. Match on (opening_spread, predicted_outcome) to (market_spread, model_spread)
4. Add two new columns:
   - spread_cover_probability_confirmed: cover_prob from lookup table
   - spread_cover_probability_match_flag: 1 if original matches confirmed, 0 otherwise
5. Write updated CSV with _with_confirmed_spreads suffix

Usage:
    python correct_spread_probabilities.py <graded_results.csv>
    python correct_spread_probabilities.py <graded_results.csv> -o <output_path.csv>
    
Example:
    python correct_spread_probabilities.py graded_results.csv
    python correct_spread_probabilities.py graded_results.csv -o corrected_results.csv
"""

# Numerical tolerance for comparing probabilities
PROBABILITY_TOLERANCE = 1e-9

# Path to canonical lookup table
LOOKUP_TABLE_PATH = "docs/spreads_lookup_combined.csv"


def round_spread(value):
    """
    Round spread value to one decimal place (half-point increments).
    
    This ensures that small floating point errors don't break joins.
    
    Args:
        value: Numeric value to round
        
    Returns:
        float: Value rounded to one decimal place
        
    Examples:
        >>> round_spread(-7.50001)
        -7.5
        >>> round_spread(-7.49999)
        -7.5
    """
    if pd.isna(value):
        return np.nan
    return round(float(value), 1)


def check_probability_match(original, confirmed, tolerance=PROBABILITY_TOLERANCE):
    """
    Check if two probability values match within tolerance.
    
    Args:
        original: Original probability value
        confirmed: Confirmed probability value from lookup
        tolerance: Numerical tolerance for comparison (default: 1e-9)
        
    Returns:
        int: 1 if values match within tolerance, 0 otherwise
        
    Examples:
        >>> check_probability_match(0.5, 0.5)
        1
        >>> check_probability_match(0.5, 0.50000000001)
        1
        >>> check_probability_match(0.5, 0.6)
        0
        >>> check_probability_match(0.5, np.nan)
        0
    """
    # If either value is NaN, they don't match
    if pd.isna(original) or pd.isna(confirmed):
        return 0
    
    # Check if values are within tolerance
    return 1 if abs(float(original) - float(confirmed)) <= tolerance else 0


def load_lookup_table(path=LOOKUP_TABLE_PATH):
    """
    Load the canonical spreads lookup table.
    
    Args:
        path: Path to the lookup CSV file
        
    Returns:
        pd.DataFrame: Lookup table with rounded spreads
        
    Raises:
        FileNotFoundError: If lookup table doesn't exist
        ValueError: If required columns are missing
    """
    logger.info(f"[cyan]Loading lookup table from {path}...[/cyan]")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Lookup table not found at: {path}")
    
    # Load the lookup table
    lookup_df = pd.read_csv(path)
    
    # Verify required columns exist
    required_cols = ['total_category', 'market_spread', 'model_spread', 'cover_prob']
    missing_cols = [col for col in required_cols if col not in lookup_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in lookup table: {missing_cols}")
    
    # Round spreads to handle floating point precision
    lookup_df['market_spread'] = lookup_df['market_spread'].apply(round_spread)
    lookup_df['model_spread'] = lookup_df['model_spread'].apply(round_spread)
    
    logger.info(f"[green]✓[/green] Loaded lookup table with {len(lookup_df)} rows")
    
    return lookup_df


def load_graded_results(path):
    """
    Load graded results CSV file.
    
    Args:
        path: Path to the graded results CSV file
        
    Returns:
        pd.DataFrame: Graded results data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    logger.info(f"[cyan]Loading graded results from {path}...[/cyan]")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graded results file not found at: {path}")
    
    # Load the graded results
    results_df = pd.read_csv(path)
    
    # Verify required columns exist
    required_cols = ['opening_spread', 'predicted_outcome']
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in graded results: {missing_cols}")
    
    logger.info(f"[green]✓[/green] Loaded graded results with {len(results_df)} rows")
    
    return results_df


def correct_spread_probabilities(results_df, lookup_df):
    """
    Correct spread probabilities by matching with lookup table.
    
    Args:
        results_df: DataFrame with graded results
        lookup_df: DataFrame with canonical lookup table
        
    Returns:
        pd.DataFrame: Results with two new columns added:
            - spread_cover_probability_confirmed
            - spread_cover_probability_match_flag
    """
    logger.info("[cyan]Correcting spread probabilities...[/cyan]")
    
    # Create a copy to avoid modifying original
    corrected_df = results_df.copy()
    
    # Round spreads in graded results
    corrected_df['opening_spread_rounded'] = corrected_df['opening_spread'].apply(round_spread)
    corrected_df['predicted_outcome_rounded'] = corrected_df['predicted_outcome'].apply(round_spread)
    
    # Prepare lookup for merge (select only spread rows, filter by total_category=1)
    # According to problem statement, we only care about spreads (not totals/moneyline)
    lookup_spreads = lookup_df[lookup_df['total_category'] == 1].copy()
    lookup_spreads = lookup_spreads[['market_spread', 'model_spread', 'cover_prob']].copy()
    
    # Merge with lookup table
    corrected_df = corrected_df.merge(
        lookup_spreads,
        left_on=['opening_spread_rounded', 'predicted_outcome_rounded'],
        right_on=['market_spread', 'model_spread'],
        how='left',
        suffixes=('', '_lookup')
    )
    
    # Rename cover_prob to spread_cover_probability_confirmed
    corrected_df['spread_cover_probability_confirmed'] = corrected_df['cover_prob']
    
    # Calculate match flag
    if 'spread_cover_probability' in corrected_df.columns:
        corrected_df['spread_cover_probability_match_flag'] = corrected_df.apply(
            lambda row: check_probability_match(
                row['spread_cover_probability'],
                row['spread_cover_probability_confirmed']
            ),
            axis=1
        )
    else:
        # If no original spread_cover_probability column exists, flag is 0
        logger.warning("[yellow]⚠[/yellow] No 'spread_cover_probability' column found in input. Match flag will be 0 for all rows.")
        corrected_df['spread_cover_probability_match_flag'] = 0
    
    # Drop temporary columns used for merging
    columns_to_drop = [
        'opening_spread_rounded',
        'predicted_outcome_rounded',
        'market_spread',
        'model_spread',
        'cover_prob'
    ]
    corrected_df = corrected_df.drop(columns=[col for col in columns_to_drop if col in corrected_df.columns])
    
    # Count matches and mismatches
    matched_count = corrected_df['spread_cover_probability_confirmed'].notna().sum()
    unmatched_count = corrected_df['spread_cover_probability_confirmed'].isna().sum()
    
    if 'spread_cover_probability' in results_df.columns:
        match_flag_1_count = (corrected_df['spread_cover_probability_match_flag'] == 1).sum()
        match_flag_0_count = (corrected_df['spread_cover_probability_match_flag'] == 0).sum()
        
        logger.info(f"[green]✓[/green] Probability correction complete:")
        logger.info(f"    Matched rows: {matched_count}")
        logger.info(f"    Unmatched rows: {unmatched_count}")
        logger.info(f"    Original values matching confirmed: {match_flag_1_count}")
        logger.info(f"    Original values NOT matching confirmed: {match_flag_0_count}")
    else:
        logger.info(f"[green]✓[/green] Probability correction complete:")
        logger.info(f"    Matched rows: {matched_count}")
        logger.info(f"    Unmatched rows: {unmatched_count}")
    
    if unmatched_count > 0:
        logger.warning(f"[yellow]⚠[/yellow] {unmatched_count} rows could not be matched to lookup table")
        logger.info("[yellow]    These rows will have NaN in spread_cover_probability_confirmed[/yellow]")
        logger.info("[yellow]    and 0 in spread_cover_probability_match_flag[/yellow]")
    
    return corrected_df


def save_results(df, input_path, output_path=None):
    """
    Save corrected results to CSV file.
    
    Args:
        df: DataFrame with corrected probabilities
        input_path: Original input file path (used to generate default output name)
        output_path: Optional specific output path
        
    Returns:
        str: Path where file was saved
    """
    if output_path is None:
        # Generate default output path with _with_confirmed_spreads suffix
        base_path = os.path.splitext(input_path)[0]
        output_path = f"{base_path}_with_confirmed_spreads.csv"
    
    logger.info(f"[cyan]Saving corrected results to {output_path}...[/cyan]")
    
    df.to_csv(output_path, index=False)
    
    logger.info(f"[green]✓[/green] Successfully saved corrected results to {output_path}")
    
    return output_path


def main():
    """
    Main function to orchestrate spread probability correction.
    """
    parser = argparse.ArgumentParser(
        description="Correct spread cover probabilities using canonical lookup table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s graded_results.csv
  %(prog)s graded_results.csv -o corrected_results.csv
  %(prog)s path/to/results.csv -l path/to/lookup.csv
        """
    )
    parser.add_argument(
        'graded_results',
        help='Path to graded results CSV file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output path for corrected CSV (default: input_with_confirmed_spreads.csv)',
        default=None
    )
    parser.add_argument(
        '-l', '--lookup',
        help=f'Path to lookup table CSV (default: {LOOKUP_TABLE_PATH})',
        default=LOOKUP_TABLE_PATH
    )
    
    args = parser.parse_args()
    
    logger.info("=== Starting spread probability correction ===")
    
    try:
        # Step 1: Load lookup table
        logger.info("[1/4] Loading lookup table...")
        lookup_df = load_lookup_table(args.lookup)
        
        # Step 2: Load graded results
        logger.info("[2/4] Loading graded results...")
        results_df = load_graded_results(args.graded_results)
        
        # Step 3: Correct probabilities
        logger.info("[3/4] Correcting probabilities...")
        corrected_df = correct_spread_probabilities(results_df, lookup_df)
        
        # Step 4: Save results
        logger.info("[4/4] Saving corrected results...")
        output_path = save_results(corrected_df, args.graded_results, args.output)
        
        logger.info("[green]✓[/green] Spread probability correction completed successfully")
        logger.info(f"[green]Output saved to: {output_path}[/green]")
        
    except FileNotFoundError as e:
        logger.error(f"[red]✗[/red] File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"[red]✗[/red] Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[red]✗[/red] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("=== Spread probability correction completed ===")


if __name__ == "__main__":
    main()

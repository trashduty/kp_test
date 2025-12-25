#!/usr/bin/env python3
"""
Fix spread cover probability values by matching against canonical lookup table.

This script matches spreads from graded results to the lookup table and adds
two new columns:
- spread_cover_probability_confirmed: The correct cover_prob from lookup
- spread_cover_probability_match_flag: 1 if original matches confirmed, 0 otherwise
"""

import argparse
import pandas as pd
import sys


def round_to_half(value):
    """Round a value to the nearest half-point (1 decimal place)."""
    if pd.isna(value):
        return value
    return round(float(value) * 2) / 2


def load_lookup_table(lookup_path):
    """
    Load the spreads lookup table and create a mapping dictionary.
    
    Returns a dictionary with key (total_category, market_spread, model_spread) -> cover_prob
    """
    print(f"Loading lookup table from: {lookup_path}")
    lookup_df = pd.read_csv(lookup_path)
    
    # Create a dictionary for fast lookups
    # Key: (total_category, market_spread, model_spread) -> cover_prob
    lookup_dict = {}
    for _, row in lookup_df.iterrows():
        total_category = int(row['total_category'])
        market_spread = round_to_half(row['market_spread'])
        model_spread = round_to_half(row['model_spread'])
        cover_prob = row['cover_prob']
        lookup_dict[(total_category, market_spread, model_spread)] = cover_prob
    
    print(f"Loaded {len(lookup_dict)} lookup entries")
    return lookup_dict


def get_total_category(market_total):
    """
    Determine the total category based on market_total value.
    
    Categories are based on typical college basketball total ranges:
    - Category 1: Low totals (< 145)
    - Category 2: Medium totals (145-160)
    - Category 3: High totals (> 160)
    """
    if pd.isna(market_total):
        # Default to category 2 (medium) if total is not available
        return 2
    
    if market_total < 145:
        return 1
    elif market_total < 160:
        return 2
    else:
        return 3


def match_spread_probability(row, lookup_dict, tolerance=0.01):
    """
    Match a row from graded results to the lookup table.
    
    Returns a tuple: (confirmed_probability, match_flag)
    - confirmed_probability: The correct cover_prob from lookup table
    - match_flag: 1 if original probability matches confirmed (within tolerance), 0 otherwise
    """
    # Round spreads to half-point increments
    market_spread = round_to_half(row['opening_spread'])
    model_spread = round_to_half(row['predicted_outcome'])
    
    # Check if we have valid spreads
    if pd.isna(market_spread) or pd.isna(model_spread):
        return None, 0
    
    # Determine total category from market_total
    total_category = get_total_category(row.get('market_total'))
    
    # Lookup the confirmed probability
    key = (total_category, market_spread, model_spread)
    confirmed_prob = lookup_dict.get(key)
    
    if confirmed_prob is None:
        # No match found in lookup table
        return None, 0
    
    # Check if original probability matches confirmed probability
    original_prob = row['spread_cover_probability']
    if pd.isna(original_prob):
        match_flag = 0
    else:
        # Match if within tolerance
        match_flag = 1 if abs(original_prob - confirmed_prob) <= tolerance else 0
    
    return confirmed_prob, match_flag


def process_graded_results(graded_path, lookup_path, output_path):
    """
    Process graded results and add confirmed spread cover probabilities.
    """
    print(f"Loading graded results from: {graded_path}")
    graded_df = pd.read_csv(graded_path)
    
    print(f"Loaded {len(graded_df)} rows from graded results")
    
    # Load lookup table
    lookup_dict = load_lookup_table(lookup_path)
    
    # Initialize new columns
    confirmed_probs = []
    match_flags = []
    
    # Process each row
    print("Matching spreads to lookup table...")
    for idx, row in graded_df.iterrows():
        confirmed_prob, match_flag = match_spread_probability(row, lookup_dict)
        confirmed_probs.append(confirmed_prob)
        match_flags.append(match_flag)
    
    # Add new columns
    graded_df['spread_cover_probability_confirmed'] = confirmed_probs
    graded_df['spread_cover_probability_match_flag'] = match_flags
    
    # Calculate statistics
    total_rows = len(graded_df)
    rows_with_confirmed = graded_df['spread_cover_probability_confirmed'].notna().sum()
    matching_rows = graded_df['spread_cover_probability_match_flag'].sum()
    
    print(f"\nResults:")
    print(f"  Total rows: {total_rows}")
    print(f"  Rows with confirmed probability: {rows_with_confirmed} ({rows_with_confirmed/total_rows*100:.1f}%)")
    print(f"  Rows where original matches confirmed: {matching_rows} ({matching_rows/total_rows*100:.1f}%)")
    
    # Save output
    print(f"\nSaving corrected results to: {output_path}")
    graded_df.to_csv(output_path, index=False)
    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description='Fix spread cover probability values using canonical lookup table'
    )
    parser.add_argument(
        '--graded',
        required=True,
        help='Path to graded results CSV file'
    )
    parser.add_argument(
        '--lookup',
        required=True,
        help='Path to spreads lookup CSV file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path for output CSV file with confirmed probabilities'
    )
    
    args = parser.parse_args()
    
    try:
        process_graded_results(args.graded, args.lookup, args.output)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

import os
import sys
import pandas as pd
import requests
import base64
from io import StringIO
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
Grade Spread Predictions Script

This script grades spread predictions from the trashduty/cbb repository's graded_results.csv file.

Requirements:
1. Read graded_results.csv from trashduty/cbb repository via GitHub API
2. Filter for rows where spread_consensus_flag == 1 AND spread_edge >= 0.04
3. Calculate if the team covered the spread based on:
   - Home team covers if: actual_spread > opening_spread
   - Away team covers if: actual_spread < opening_spread
   - Push if: actual_spread == opening_spread
4. Add "Covered" column with values:
   - 0 = did not cover
   - 1 = covered
   - 2 = push
5. Save results to filtered_graded_results.csv

Usage:
    python grade_spread_predictions.py

Environment Variables:
    GITHUB_TOKEN - Optional GitHub token for accessing private repositories
    
Notes:
    - If GitHub API access fails, the script will attempt to use a local graded_results.csv file
    - The script requires the following columns in the input CSV:
      team, home_team, away_team, home_score, away_score, opening_spread,
      spread_consensus_flag, spread_edge
"""


def fetch_graded_results_from_github():
    """
    Fetches graded_results.csv from the trashduty/cbb repository
    Falls back to local file if API access fails
    """
    # GitHub API URL for the file
    url = "https://api.github.com/repos/trashduty/cbb/contents/graded_results.csv"
    
    # Set up headers with authentication if available
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        logger.info("[cyan]Using GitHub token for authentication[/cyan]")
    
    try:
        logger.info("[cyan]Fetching graded_results.csv from trashduty/cbb repository...[/cyan]")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # GitHub API returns file content as base64 encoded
        file_data = response.json()
        content_base64 = file_data['content']
        
        # Decode base64 content
        content_decoded = base64.b64decode(content_base64).decode('utf-8')
        
        # Load into pandas DataFrame
        df = pd.read_csv(StringIO(content_decoded))
        
        logger.info(f"[green]✓[/green] Successfully loaded graded_results.csv with {len(df)} rows")
        return df
        
    except requests.exceptions.HTTPError as http_err:
        logger.warning(f"[yellow]⚠[/yellow] HTTP error occurred: {http_err}")
        logger.info("[cyan]Attempting to use local graded_results.csv file...[/cyan]")
        return try_local_file()
    except Exception as err:
        logger.warning(f"[yellow]⚠[/yellow] Error occurred: {err}")
        logger.info("[cyan]Attempting to use local graded_results.csv file...[/cyan]")
        return try_local_file()


def try_local_file():
    """
    Try to load graded_results.csv from local directory
    """
    try:
        if os.path.exists('graded_results.csv'):
            df = pd.read_csv('graded_results.csv')
            logger.info(f"[green]✓[/green] Successfully loaded local graded_results.csv with {len(df)} rows")
            return df
        else:
            logger.error("[red]✗[/red] Local graded_results.csv file not found")
            logger.info("[yellow]Please ensure you have access to the trashduty/cbb repository or place graded_results.csv in the current directory[/yellow]")
            return None
    except Exception as e:
        logger.error(f"[red]✗[/red] Error loading local file: {e}")
        return None


def filter_spread_predictions(df):
    """
    Filter for rows where spread_consensus_flag == 1 AND spread_edge >= 0.04
    """
    logger.info("[cyan]Filtering spread predictions...[/cyan]")
    
    # Apply filters
    filtered_df = df[
        (df['spread_consensus_flag'] == 1) & 
        (df['spread_edge'] >= 0.04)
    ].copy()
    
    logger.info(f"[green]✓[/green] Filtered to {len(filtered_df)} rows")
    return filtered_df


def calculate_spread_coverage(row):
    """
    Calculate if the team covered the spread
    Returns:
        0 = did not cover
        1 = covered
        2 = push
    """
    team = row['team']
    home_team = row['home_team']
    away_team = row['away_team']
    home_score = row['home_score']
    away_score = row['away_score']
    opening_spread = row['opening_spread']
    
    # Calculate actual spread (home_score - away_score)
    actual_spread = home_score - away_score
    
    # Determine if team was home or away
    is_home = (team == home_team)
    
    # Check for push
    if actual_spread == opening_spread:
        return 2  # push
    
    # Check if covered
    if is_home:
        # Home team covers if actual_spread > opening_spread
        return 1 if actual_spread > opening_spread else 0
    else:
        # Away team covers if actual_spread < opening_spread
        return 1 if actual_spread < opening_spread else 0


def add_covered_column(df):
    """
    Add the 'Covered' column to the dataframe
    """
    logger.info("[cyan]Calculating spread coverage...[/cyan]")
    
    df['Covered'] = df.apply(calculate_spread_coverage, axis=1)
    
    # Count results
    covered_count = (df['Covered'] == 1).sum()
    not_covered_count = (df['Covered'] == 0).sum()
    push_count = (df['Covered'] == 2).sum()
    
    logger.info(f"[green]✓[/green] Coverage calculation complete:")
    logger.info(f"    Covered: {covered_count}")
    logger.info(f"    Did not cover: {not_covered_count}")
    logger.info(f"    Push: {push_count}")
    
    return df


def save_results(df, output_file='filtered_graded_results.csv'):
    """
    Save the results to a CSV file
    """
    logger.info(f"[cyan]Saving results to {output_file}...[/cyan]")
    
    df.to_csv(output_file, index=False)
    
    logger.info(f"[green]✓[/green] Successfully saved results to {output_file}")


def main():
    """
    Main function to orchestrate the spread prediction grading
    """
    logger.info("=== Starting spread prediction grading ===")
    
    try:
        # Step 1: Fetch data from GitHub
        logger.info("[1/4] Fetching graded_results.csv from GitHub...")
        df = fetch_graded_results_from_github()
        
        if df is None:
            logger.error("[red]✗[/red] Failed to fetch graded_results.csv")
            sys.exit(1)
        
        # Step 2: Filter the data
        logger.info("[2/4] Filtering data...")
        filtered_df = filter_spread_predictions(df)
        
        if len(filtered_df) == 0:
            logger.warning("[yellow]⚠[/yellow] No rows match the filter criteria")
            sys.exit(0)
        
        # Step 3: Add Covered column
        logger.info("[3/4] Calculating spread coverage...")
        result_df = add_covered_column(filtered_df)
        
        # Step 4: Save results
        logger.info("[4/4] Saving results...")
        save_results(result_df)
        
        logger.info("[green]✓[/green] Successfully completed spread prediction grading")
        
    except Exception as e:
        logger.error(f"[red]✗[/red] Error in grading script: {str(e)}")
        sys.exit(1)
    
    logger.info("=== Spread prediction grading completed successfully ===")


if __name__ == "__main__":
    main()

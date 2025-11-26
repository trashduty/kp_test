import os
import sys
import pandas as pd
import requests
import base64
import traceback
from io import StringIO
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
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

# Constants
GRADED_RESULTS_COMMIT = "56448b2e6e4f76970b6dfa5bb03bdfb4a2972552"

"""
Model Performance Analysis Script

This script analyzes model performance from the trashduty/cbb repository's graded_results.csv file.

The script calculates and displays comprehensive summary statistics including:
1. Overall Spread Records (Favorites vs Underdogs)
2. Overall Totals Records (Overs vs Unders)
3. Model Spread Performance by Edge (All Games)
4. Model Spread Performance by Edge (Consensus Only)
5. Model Spread Performance by Point Spread Ranges
6. Model Over/Under Performance by Edge (All Games)
7. Model Over/Under Performance by Edge (Consensus Only)
8. Overall Model Totals Record
9. Moneyline Performance by Win Probability (All Games)
10. Moneyline Performance by Win Probability (Consensus Only)

Usage:
    python analyze_model_performance.py

Environment Variables:
    GITHUB_TOKEN - Optional GitHub token for accessing private repositories
"""


def fetch_graded_results_from_github():
    """
    Fetches graded_results.csv from the trashduty/cbb repository at specific commit
    Falls back to local file if API access fails
    """
    # Try raw GitHub URL first (more reliable)
    raw_url = f"https://raw.githubusercontent.com/trashduty/cbb/{GRADED_RESULTS_COMMIT}/graded_results.csv"
    
    try:
        logger.info("[cyan]Fetching graded_results.csv from trashduty/cbb repository...[/cyan]")
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        
        # Load into pandas DataFrame
        df = pd.read_csv(StringIO(response.text))
        
        logger.info(f"[green]✓[/green] Successfully loaded graded_results.csv with {len(df)} rows")
        return df
        
    except Exception as err:
        logger.warning(f"[yellow]⚠[/yellow] Error occurred: {err}")
        logger.info("[cyan]Attempting to use GitHub API...[/cyan]")
        return fetch_via_api()


def fetch_via_api():
    """
    Try to fetch using GitHub API with base64 decoding
    """
    url = "https://api.github.com/repos/trashduty/cbb/contents/graded_results.csv"
    params = {'ref': GRADED_RESULTS_COMMIT}
    
    headers = {}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        file_data = response.json()
        content_base64 = file_data['content']
        content_decoded = base64.b64decode(content_base64).decode('utf-8')
        
        df = pd.read_csv(StringIO(content_decoded))
        logger.info(f"[green]✓[/green] Successfully loaded graded_results.csv with {len(df)} rows")
        return df
        
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


def format_win_loss_pct(wins, losses):
    """
    Format win-loss record with percentage
    """
    total = wins + losses
    if total == 0:
        return "0-0 (0.0%)"
    pct = (wins / total) * 100
    return f"{wins}-{losses} ({pct:.1f}%)"


def print_section_header(title):
    """
    Print a formatted section header
    """
    console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 80}[/bold cyan]\n")


def analyze_overall_spread_records(df):
    """
    Section 1: Overall Spread Records
    Analyze Favorites vs Underdogs performance
    """
    print_section_header("1. Overall Spread Records")
    
    # Remove rows with NaN spread_covered values
    df_clean = df.dropna(subset=['spread_covered'])
    
    # Favorites: opening_spread < 0
    favorites = df_clean[df_clean['opening_spread'] < 0].copy()
    fav_wins = (favorites['spread_covered'] == 1).sum()
    fav_losses = (favorites['spread_covered'] == 0).sum()
    
    # Underdogs: opening_spread > 0
    underdogs = df_clean[df_clean['opening_spread'] > 0].copy()
    dog_wins = (underdogs['spread_covered'] == 1).sum()
    dog_losses = (underdogs['spread_covered'] == 0).sum()
    
    console.print(f"[bold]Favorites Record:[/bold] {format_win_loss_pct(fav_wins, fav_losses)}")
    console.print(f"[bold]Underdogs Record:[/bold] {format_win_loss_pct(dog_wins, dog_losses)}")
    console.print(f"\nNote: {len(favorites)} favorite bets, {len(underdogs)} underdog bets")


def analyze_overall_totals_records(df):
    """
    Section 2: Overall Totals Records
    """
    print_section_header("2. Overall Totals Records")
    
    # Remove rows with NaN values
    df_clean = df.dropna(subset=['over_hit', 'under_hit'])
    
    # Count overs and unders
    over_wins = (df_clean['over_hit'] == 1).sum()
    over_losses = (df_clean['over_hit'] == 0).sum()
    
    under_wins = (df_clean['under_hit'] == 1).sum()
    under_losses = (df_clean['under_hit'] == 0).sum()
    
    console.print(f"[bold]Overs Record:[/bold] {format_win_loss_pct(over_wins, over_losses)}")
    console.print(f"[bold]Unders Record:[/bold] {format_win_loss_pct(under_wins, under_losses)}")


def analyze_spread_performance_by_edge(df, consensus_only=False):
    """
    Section 3 & 4: Model Spread Performance by Edge
    """
    title = "4. Model Spread Performance by Edge (Consensus Only)" if consensus_only else "3. Model Spread Performance by Edge (All Games)"
    print_section_header(title)
    
    # Remove rows with NaN values
    data = df.dropna(subset=['spread_covered', 'spread_edge']).copy()
    
    # Filter for consensus if needed
    if consensus_only:
        data = data[data['spread_consensus_flag'] == 1].copy()
    
    # Define edge tiers (edges are in decimal format, e.g., 0.025 = 2.5%)
    tiers = [
        (0.0, 0.019, "0-1.9%"),
        (0.02, 0.029, "2-2.9%"),
        (0.03, 0.039, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Edge Tier", style="yellow")
    table.add_column("Record", justify="right")
    table.add_column("Win %", justify="right")
    
    for min_edge, max_edge, label in tiers:
        tier_data = data[(data['spread_edge'] >= min_edge) & (data['spread_edge'] < max_edge)]
        wins = (tier_data['spread_covered'] == 1).sum()
        losses = (tier_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            table.add_row(label, "0-0", "0.0%")
    
    console.print(table)


def analyze_spread_performance_by_point_spread(df):
    """
    Section 5: Model Spread Performance by Point Spread Ranges
    """
    print_section_header("5. Model Spread Performance by Point Spread Ranges")
    
    # Filter for games where spread_cover_probability > 0.5 and remove NaN values
    confident_picks = df.dropna(subset=['spread_cover_probability', 'spread_covered', 'opening_spread']).copy()
    confident_picks = confident_picks[confident_picks['spread_cover_probability'] > 0.5].copy()
    
    # Define spread ranges
    ranges = [
        (0, 4.5, "0-4.5"),
        (5, 9.5, "5-9.5"),
        (10, 14.5, "10-14.5"),
        (15, 19.5, "15-19.5"),
        (20, 24.5, "20-24.5"),
        (25, 29.5, "25-29.5"),
        (30, float('inf'), "30+")
    ]
    
    # Analyze Favorites (opening_spread < 0)
    console.print("[bold]Favorites (opening_spread < 0):[/bold]\n")
    favorites = confident_picks[confident_picks['opening_spread'] < 0].copy()
    favorites['abs_spread'] = abs(favorites['opening_spread'])
    
    fav_table = Table(show_header=True, header_style="bold cyan")
    fav_table.add_column("Point Spread Range", style="yellow")
    fav_table.add_column("Record", justify="right")
    fav_table.add_column("Win %", justify="right")
    
    for min_spread, max_spread, label in ranges:
        range_data = favorites[(favorites['abs_spread'] >= min_spread) & (favorites['abs_spread'] <= max_spread)]
        wins = (range_data['spread_covered'] == 1).sum()
        losses = (range_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            fav_table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            fav_table.add_row(label, "0-0", "0.0%")
    
    console.print(fav_table)
    
    # Analyze Underdogs (opening_spread > 0)
    console.print("\n[bold]Underdogs (opening_spread > 0):[/bold]\n")
    underdogs = confident_picks[confident_picks['opening_spread'] > 0].copy()
    
    dog_table = Table(show_header=True, header_style="bold cyan")
    dog_table.add_column("Point Spread Range", style="yellow")
    dog_table.add_column("Record", justify="right")
    dog_table.add_column("Win %", justify="right")
    
    for min_spread, max_spread, label in ranges:
        range_data = underdogs[(underdogs['opening_spread'] >= min_spread) & (underdogs['opening_spread'] <= max_spread)]
        wins = (range_data['spread_covered'] == 1).sum()
        losses = (range_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            dog_table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            dog_table.add_row(label, "0-0", "0.0%")
    
    console.print(dog_table)


def analyze_over_under_performance_by_edge(df, consensus_only=False):
    """
    Section 6 & 7: Model Over/Under Performance by Edge
    """
    title = "7. Model Over/Under Performance by Edge (Consensus Only)" if consensus_only else "6. Model Over/Under Performance by Edge (All Games)"
    print_section_header(title)
    
    # Define edge tiers
    tiers = [
        (0.0, 0.019, "0-1.9%"),
        (0.02, 0.029, "2-2.9%"),
        (0.03, 0.039, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    # Analyze Overs
    console.print("[bold]Overs Performance:[/bold]\n")
    
    # Remove NaN values
    over_data = df.dropna(subset=['over_hit', 'over_edge']).copy()
    if consensus_only:
        over_data = over_data[over_data['over_consensus_flag'] == 1].copy()
    
    over_table = Table(show_header=True, header_style="bold cyan")
    over_table.add_column("Edge Tier", style="yellow")
    over_table.add_column("Record", justify="right")
    over_table.add_column("Win %", justify="right")
    
    for min_edge, max_edge, label in tiers:
        tier_data = over_data[(over_data['over_edge'] >= min_edge) & (over_data['over_edge'] < max_edge)]
        wins = (tier_data['over_hit'] == 1).sum()
        losses = (tier_data['over_hit'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            over_table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            over_table.add_row(label, "0-0", "0.0%")
    
    console.print(over_table)
    
    # Analyze Unders
    console.print("\n[bold]Unders Performance:[/bold]\n")
    
    # Remove NaN values
    under_data = df.dropna(subset=['under_hit', 'under_edge']).copy()
    if consensus_only:
        under_data = under_data[under_data['under_consensus_flag'] == 1].copy()
    
    under_table = Table(show_header=True, header_style="bold cyan")
    under_table.add_column("Edge Tier", style="yellow")
    under_table.add_column("Record", justify="right")
    under_table.add_column("Win %", justify="right")
    
    for min_edge, max_edge, label in tiers:
        tier_data = under_data[(under_data['under_edge'] >= min_edge) & (under_data['under_edge'] < max_edge)]
        wins = (tier_data['under_hit'] == 1).sum()
        losses = (tier_data['under_hit'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            under_table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            under_table.add_row(label, "0-0", "0.0%")
    
    console.print(under_table)


def analyze_overall_model_totals_record(df):
    """
    Section 8: Overall Model Totals Record
    """
    print_section_header("8. Overall Model Totals Record")
    
    # Remove rows with NaN values and filter for confident picks
    df_clean = df.dropna(subset=['over_cover_probability', 'under_cover_probability', 'over_hit', 'under_hit'])
    
    # Overs where over_cover_probability > 0.5
    confident_overs = df_clean[df_clean['over_cover_probability'] > 0.5].copy()
    over_wins = (confident_overs['over_hit'] == 1).sum()
    over_losses = (confident_overs['over_hit'] == 0).sum()
    
    # Unders where under_cover_probability > 0.5
    confident_unders = df_clean[df_clean['under_cover_probability'] > 0.5].copy()
    under_wins = (confident_unders['under_hit'] == 1).sum()
    under_losses = (confident_unders['under_hit'] == 0).sum()
    
    console.print(f"[bold]Overs (over_cover_probability > 0.5):[/bold] {format_win_loss_pct(over_wins, over_losses)}")
    console.print(f"[bold]Unders (under_cover_probability > 0.5):[/bold] {format_win_loss_pct(under_wins, under_losses)}")


def analyze_moneyline_performance_by_probability(df, consensus_only=False):
    """
    Section 9 & 10: Moneyline Performance by Win Probability
    """
    title = "10. Moneyline Performance by Win Probability (Consensus Only)" if consensus_only else "9. Moneyline Performance by Win Probability (All Games)"
    print_section_header(title)
    
    # Filter for consensus if needed
    data = df[df['moneyline_consensus_flag'] == 1].copy() if consensus_only else df.copy()
    
    # Remove rows with NaN moneyline_win_probability
    data = data.dropna(subset=['moneyline_win_probability'])
    
    # Define probability tiers
    tiers = [
        (0.10, 0.19, "10-19%"),
        (0.20, 0.29, "20-29%"),
        (0.30, 0.39, "30-39%"),
        (0.40, 0.49, "40-49%"),
        (0.50, 0.59, "50-59%"),
        (0.60, 0.69, "60-69%"),
        (0.70, 0.79, "70-79%"),
        (0.80, 0.89, "80-89%"),
        (0.90, 1.0, "90%+")
    ]
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Win Probability Tier", style="yellow")
    table.add_column("Record", justify="right")
    table.add_column("Win %", justify="right")
    
    for min_prob, max_prob, label in tiers:
        tier_data = data[(data['moneyline_win_probability'] >= min_prob) & (data['moneyline_win_probability'] <= max_prob)]
        wins = (tier_data['moneyline_won'] == 1).sum()
        losses = (tier_data['moneyline_won'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            table.add_row(label, f"{wins}-{losses}", f"{win_pct:.1f}%")
        else:
            table.add_row(label, "0-0", "0.0%")
    
    console.print(table)


def main():
    """
    Main function to orchestrate the model performance analysis
    """
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]Model Performance Analysis Report[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    try:
        # Fetch data from GitHub
        df = fetch_graded_results_from_github()
        
        if df is None:
            logger.error("[red]✗[/red] Failed to fetch graded_results.csv")
            sys.exit(1)
        
        # Run all analyses
        analyze_overall_spread_records(df)
        analyze_overall_totals_records(df)
        analyze_spread_performance_by_edge(df, consensus_only=False)
        analyze_spread_performance_by_edge(df, consensus_only=True)
        analyze_spread_performance_by_point_spread(df)
        analyze_over_under_performance_by_edge(df, consensus_only=False)
        analyze_over_under_performance_by_edge(df, consensus_only=True)
        analyze_overall_model_totals_record(df)
        analyze_moneyline_performance_by_probability(df, consensus_only=False)
        analyze_moneyline_performance_by_probability(df, consensus_only=True)
        
        console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
        console.print("[bold green]Analysis Complete![/bold green]")
        console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")
        
    except Exception as e:
        logger.error(f"[red]✗[/red] Error in analysis script: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

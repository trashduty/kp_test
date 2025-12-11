import os
import sys
import html
import pandas as pd
import requests
import base64
import traceback
from io import StringIO
from datetime import datetime, timezone
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

# Output file paths
DOCS_DIR = "docs"
TEXT_OUTPUT_FILE = os.path.join(DOCS_DIR, "model_performance_analysis.txt")
HTML_OUTPUT_FILE = os.path.join(DOCS_DIR, "model_performance_analysis.html")

"""
Model Performance Analysis Script

This script analyzes model performance from the trashduty/cbb repository's graded_results.csv file.

The script calculates and displays comprehensive summary statistics including:
1. Model Spread Performance by Edge (All Games)
2. Model Spread Performance by Edge (Consensus Only)
3. Model Spread Performance by Point Spread Ranges
4. Model Over/Under Performance by Edge (All Games)
5. Model Over/Under Performance by Edge (Consensus Only)
6. Overall Model Totals Record
7. Moneyline Performance by Win Probability (All Games)
8. Moneyline Performance by Win Probability (Consensus Only)
9. Moneyline Performance by Win Probability (4%+ Edge)
10. Moneyline Performance by Win Probability (4%+ Edge, Consensus Only)

Usage:
    python analyze_model_performance.py

Environment Variables:
    GITHUB_TOKEN - Optional GitHub token for accessing private repositories
"""


def fetch_graded_results_from_github():
    """
    Fetches graded_results.csv from the trashduty/cbb repository main branch
    Falls back to local file if API access fails
    """
    # Try raw GitHub URL first (more reliable)
    raw_url = "https://raw.githubusercontent.com/trashduty/cbb/main/graded_results.csv"
    
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
    params = {'ref': 'main'}
    
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


def get_last_game_date(df):
    """
    Extract the most recent game date from the dataframe
    
    Args:
        df: pandas DataFrame with game data
    
    Returns:
        str: Formatted date string (YYYY-MM-DD) or fallback message
    """
    # Handle empty dataframe
    if df is None or len(df) == 0:
        return "No games"
    
    # Check if date column exists
    date_columns = ['date', 'game_date', 'Date', 'GameDate']
    date_col = None
    
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
    
    # If no date column found
    if date_col is None:
        return "Unknown"
    
    try:
        # Get non-null dates
        dates = df[date_col].dropna()
        
        if len(dates) == 0:
            return "No games"
        
        # Try to parse as datetime if needed
        if dates.dtype == 'object':
            # Try to convert to datetime
            try:
                dates = pd.to_datetime(dates)
            except (ValueError, TypeError):
                # If conversion fails, use string comparison
                max_date = str(dates.max())
                # Try to extract just the date portion if it's a datetime string
                if ' ' in max_date:
                    max_date = max_date.split(' ')[0]
                return max_date
        
        # Get the maximum date
        max_date = dates.max()
        
        # Format the date
        if isinstance(max_date, str):
            return max_date
        elif hasattr(max_date, 'strftime'):
            return max_date.strftime('%Y-%m-%d')
        else:
            return str(max_date)
            
    except Exception as e:
        logger.warning(f"[yellow]⚠[/yellow] Error extracting last game date: {e}")
        return "Unknown"


def print_section_header(title):
    """
    Print a formatted section header
    """
    console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 80}[/bold cyan]\n")


def analyze_spread_performance_by_edge(df, consensus_only=False):
    """
    Section 1 & 2: Model Spread Performance by Edge
    """
    title = "2. Model Spread Performance by Edge (Consensus Only)" if consensus_only else "1. Model Spread Performance by Edge (All Games)"
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
    Section 3: Model Spread Performance by Point Spread Ranges
    """
    print_section_header("3. Model Spread Performance by Point Spread Ranges")
    
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
    Section 4 & 5: Model Over/Under Performance by Edge
    """
    title = "5. Model Over/Under Performance by Edge (Consensus Only)" if consensus_only else "4. Model Over/Under Performance by Edge (All Games)"
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
    Section 6: Overall Model Totals Record
    """
    print_section_header("6. Overall Model Totals Record")
    
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
    Section 7 & 8: Moneyline Performance by Win Probability
    """
    title = "8. Moneyline Performance by Win Probability (Consensus Only)" if consensus_only else "7. Moneyline Performance by Win Probability (All Games)"
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


def analyze_moneyline_performance_by_win_probability_high_edge(df, consensus_only=False):
    """
    Section 9 & 10: Moneyline Performance by Win Probability (4%+ Edge)
    """
    title = "10. Moneyline Performance by Win Probability (4%+ Edge, Consensus Only)" if consensus_only else "9. Moneyline Performance by Win Probability (4%+ Edge)"
    print_section_header(title)
    
    # Filter for moneyline edge >= 4% (0.04)
    data = df.dropna(subset=['moneyline_edge', 'moneyline_won', 'moneyline_win_probability']).copy()
    data = data[data['moneyline_edge'] >= 0.04].copy()
    
    # Filter for consensus if needed
    if consensus_only:
        data = data[data['moneyline_consensus_flag'] == 1].copy()
    
    # Define probability tiers (same as Section 8)
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


def collect_spread_performance_by_edge(df, consensus_only=False):
    """
    Collect spread performance by edge data for output
    """
    data = df.dropna(subset=['spread_covered', 'spread_edge']).copy()
    
    if consensus_only:
        data = data[data['spread_consensus_flag'] == 1].copy()
    
    tiers = [
        (0.0, 0.019, "0-1.9%"),
        (0.02, 0.029, "2-2.9%"),
        (0.03, 0.039, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    results = []
    for min_edge, max_edge, label in tiers:
        tier_data = data[(data['spread_edge'] >= min_edge) & (data['spread_edge'] < max_edge)]
        wins = (tier_data['spread_covered'] == 1).sum()
        losses = (tier_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            results.append({'tier': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            results.append({'tier': label, 'record': "0-0", 'pct': "0.0%"})
    
    return results


def collect_spread_performance_by_point_spread(df):
    """
    Collect spread performance by point spread ranges for output
    """
    confident_picks = df.dropna(subset=['spread_cover_probability', 'spread_covered', 'opening_spread']).copy()
    confident_picks = confident_picks[confident_picks['spread_cover_probability'] > 0.5].copy()
    
    ranges = [
        (0, 4.5, "0-4.5"),
        (5, 9.5, "5-9.5"),
        (10, 14.5, "10-14.5"),
        (15, 19.5, "15-19.5"),
        (20, 24.5, "20-24.5"),
        (25, 29.5, "25-29.5"),
        (30, float('inf'), "30+")
    ]
    
    # Favorites
    favorites = confident_picks[confident_picks['opening_spread'] < 0].copy()
    favorites['abs_spread'] = abs(favorites['opening_spread'])
    
    fav_results = []
    for min_spread, max_spread, label in ranges:
        range_data = favorites[(favorites['abs_spread'] >= min_spread) & (favorites['abs_spread'] <= max_spread)]
        wins = (range_data['spread_covered'] == 1).sum()
        losses = (range_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            fav_results.append({'range': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            fav_results.append({'range': label, 'record': "0-0", 'pct': "0.0%"})
    
    # Underdogs
    underdogs = confident_picks[confident_picks['opening_spread'] > 0].copy()
    
    dog_results = []
    for min_spread, max_spread, label in ranges:
        range_data = underdogs[(underdogs['opening_spread'] >= min_spread) & (underdogs['opening_spread'] <= max_spread)]
        wins = (range_data['spread_covered'] == 1).sum()
        losses = (range_data['spread_covered'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            dog_results.append({'range': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            dog_results.append({'range': label, 'record': "0-0", 'pct': "0.0%"})
    
    return {'favorites': fav_results, 'underdogs': dog_results}


def collect_over_under_performance_by_edge(df, consensus_only=False):
    """
    Collect over/under performance by edge data for output
    """
    tiers = [
        (0.0, 0.019, "0-1.9%"),
        (0.02, 0.029, "2-2.9%"),
        (0.03, 0.039, "3-3.9%"),
        (0.04, float('inf'), "4%+")
    ]
    
    # Overs
    over_data = df.dropna(subset=['over_hit', 'over_edge']).copy()
    if consensus_only:
        over_data = over_data[over_data['over_consensus_flag'] == 1].copy()
    
    over_results = []
    for min_edge, max_edge, label in tiers:
        tier_data = over_data[(over_data['over_edge'] >= min_edge) & (over_data['over_edge'] < max_edge)]
        wins = (tier_data['over_hit'] == 1).sum()
        losses = (tier_data['over_hit'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            over_results.append({'tier': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            over_results.append({'tier': label, 'record': "0-0", 'pct': "0.0%"})
    
    # Unders
    under_data = df.dropna(subset=['under_hit', 'under_edge']).copy()
    if consensus_only:
        under_data = under_data[under_data['under_consensus_flag'] == 1].copy()
    
    under_results = []
    for min_edge, max_edge, label in tiers:
        tier_data = under_data[(under_data['under_edge'] >= min_edge) & (under_data['under_edge'] < max_edge)]
        wins = (tier_data['under_hit'] == 1).sum()
        losses = (tier_data['under_hit'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            under_results.append({'tier': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            under_results.append({'tier': label, 'record': "0-0", 'pct': "0.0%"})
    
    return {'overs': over_results, 'unders': under_results}


def collect_overall_model_totals_record(df):
    """
    Collect overall model totals record data for output
    """
    df_clean = df.dropna(subset=['over_cover_probability', 'under_cover_probability', 'over_hit', 'under_hit'])
    
    confident_overs = df_clean[df_clean['over_cover_probability'] > 0.5].copy()
    over_wins = (confident_overs['over_hit'] == 1).sum()
    over_losses = (confident_overs['over_hit'] == 0).sum()
    
    confident_unders = df_clean[df_clean['under_cover_probability'] > 0.5].copy()
    under_wins = (confident_unders['under_hit'] == 1).sum()
    under_losses = (confident_unders['under_hit'] == 0).sum()
    
    return {
        'overs': {'wins': over_wins, 'losses': over_losses, 'record': format_win_loss_pct(over_wins, over_losses)},
        'unders': {'wins': under_wins, 'losses': under_losses, 'record': format_win_loss_pct(under_wins, under_losses)}
    }


def collect_moneyline_performance_by_probability(df, consensus_only=False):
    """
    Collect moneyline performance by win probability data for output
    """
    data = df[df['moneyline_consensus_flag'] == 1].copy() if consensus_only else df.copy()
    data = data.dropna(subset=['moneyline_win_probability'])
    
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
    
    results = []
    for min_prob, max_prob, label in tiers:
        tier_data = data[(data['moneyline_win_probability'] >= min_prob) & (data['moneyline_win_probability'] <= max_prob)]
        wins = (tier_data['moneyline_won'] == 1).sum()
        losses = (tier_data['moneyline_won'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            results.append({'tier': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            results.append({'tier': label, 'record': "0-0", 'pct': "0.0%"})
    
    return results


def collect_moneyline_performance_by_win_probability_high_edge(df, consensus_only=False):
    """
    Collect moneyline performance by win probability (4%+ edge) data for output
    """
    # Filter for moneyline edge >= 4% (0.04)
    data = df.dropna(subset=['moneyline_edge', 'moneyline_won', 'moneyline_win_probability']).copy()
    data = data[data['moneyline_edge'] >= 0.04].copy()
    
    # Filter for consensus if needed
    if consensus_only:
        data = data[data['moneyline_consensus_flag'] == 1].copy()
    
    # Define probability tiers (same as Section 8)
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
    
    results = []
    for min_prob, max_prob, label in tiers:
        tier_data = data[(data['moneyline_win_probability'] >= min_prob) & (data['moneyline_win_probability'] <= max_prob)]
        wins = (tier_data['moneyline_won'] == 1).sum()
        losses = (tier_data['moneyline_won'] == 0).sum()
        total = wins + losses
        
        if total > 0:
            win_pct = (wins / total) * 100
            results.append({'tier': label, 'record': f"{wins}-{losses}", 'pct': f"{win_pct:.1f}%"})
        else:
            results.append({'tier': label, 'record': "0-0", 'pct': "0.0%"})
    
    return results


def generate_plain_text_output(analysis_data, timestamp, last_game_date):
    """
    Generate plain text output from analysis data
    """
    lines = []
    lines.append("=" * 80)
    lines.append("Model Performance Analysis Report")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Last Game Included: {last_game_date}")
    lines.append("This report shows the model's record against the opening lines for spreads, totals, and moneylines.")
    lines.append("=" * 80)
    lines.append("")
    
    # Section 1: Model Spread Performance by Edge (All Games)
    lines.append("=" * 80)
    lines.append("1. Model Spread Performance by Edge (All Games)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['spread_by_edge_all']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 2: Model Spread Performance by Edge (Consensus Only)
    lines.append("=" * 80)
    lines.append("2. Model Spread Performance by Edge (Consensus Only)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['spread_by_edge_consensus']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 3: Model Spread Performance by Point Spread Ranges
    lines.append("=" * 80)
    lines.append("3. Model Spread Performance by Point Spread Ranges")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Favorites (opening_spread < 0):")
    lines.append("")
    lines.append(f"{'Point Spread Range':<20} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 42)
    for row in analysis_data['spread_by_point_spread']['favorites']:
        lines.append(f"{row['range']:<20} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    lines.append("Underdogs (opening_spread > 0):")
    lines.append("")
    lines.append(f"{'Point Spread Range':<20} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 42)
    for row in analysis_data['spread_by_point_spread']['underdogs']:
        lines.append(f"{row['range']:<20} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 4: Model Over/Under Performance by Edge (All Games)
    lines.append("=" * 80)
    lines.append("4. Model Over/Under Performance by Edge (All Games)")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Overs Performance:")
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['ou_by_edge_all']['overs']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    lines.append("Unders Performance:")
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['ou_by_edge_all']['unders']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 5: Model Over/Under Performance by Edge (Consensus Only)
    lines.append("=" * 80)
    lines.append("5. Model Over/Under Performance by Edge (Consensus Only)")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Overs Performance:")
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['ou_by_edge_consensus']['overs']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    lines.append("Unders Performance:")
    lines.append("")
    lines.append(f"{'Edge Tier':<15} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 37)
    for row in analysis_data['ou_by_edge_consensus']['unders']:
        lines.append(f"{row['tier']:<15} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 6: Overall Model Totals Record
    lines.append("=" * 80)
    lines.append("6. Overall Model Totals Record")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Overs (over_cover_probability > 0.5): {analysis_data['model_totals']['overs']['record']}")
    lines.append(f"Unders (under_cover_probability > 0.5): {analysis_data['model_totals']['unders']['record']}")
    lines.append("")
    
    # Section 7: Moneyline Performance by Win Probability (All Games)
    lines.append("=" * 80)
    lines.append("7. Moneyline Performance by Win Probability (All Games)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Win Probability Tier':<22} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 44)
    for row in analysis_data['moneyline_all']:
        lines.append(f"{row['tier']:<22} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 8: Moneyline Performance by Win Probability (Consensus Only)
    lines.append("=" * 80)
    lines.append("8. Moneyline Performance by Win Probability (Consensus Only)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Win Probability Tier':<22} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 44)
    for row in analysis_data['moneyline_consensus']:
        lines.append(f"{row['tier']:<22} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 9: Moneyline Performance by Win Probability (4%+ Edge)
    lines.append("=" * 80)
    lines.append("9. Moneyline Performance by Win Probability (4%+ Edge)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Win Probability Tier':<22} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 44)
    for row in analysis_data['moneyline_by_prob_high_edge_all']:
        lines.append(f"{row['tier']:<22} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    # Section 10: Moneyline Performance by Win Probability (4%+ Edge, Consensus Only)
    lines.append("=" * 80)
    lines.append("10. Moneyline Performance by Win Probability (4%+ Edge, Consensus Only)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Win Probability Tier':<22} {'Record':<12} {'Win %':<10}")
    lines.append("-" * 44)
    for row in analysis_data['moneyline_by_prob_high_edge_consensus']:
        lines.append(f"{row['tier']:<22} {row['record']:<12} {row['pct']:<10}")
    lines.append("")
    
    lines.append("=" * 80)
    lines.append("Analysis Complete!")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def escape_html(value):
    """
    Escape HTML special characters to prevent XSS
    """
    return html.escape(str(value))


def generate_html_output(analysis_data, timestamp, last_game_date):
    """
    Generate HTML output from analysis data
    """
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Performance Analysis</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #2c5282;
        }}
        h1 {{
            color: #2c5282;
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9rem;
        }}
        .disclaimer {{
            font-size: 0.9rem;
            color: #718096;
            margin-top: 10px;
            font-style: italic;
        }}
        section {{
            margin-bottom: 40px;
        }}
        h2 {{
            color: #2c5282;
            font-size: 1.3rem;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        h3 {{
            color: #4a5568;
            font-size: 1.1rem;
            margin: 20px 0 10px 0;
        }}
        .summary-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .summary-item:last-child {{
            border-bottom: none;
        }}
        .summary-label {{
            font-weight: 600;
            color: #4a5568;
        }}
        .summary-value {{
            font-weight: 500;
            color: #2d3748;
        }}
        .note {{
            color: #666;
            font-size: 0.9rem;
            font-style: italic;
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #2c5282;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        tr:hover {{
            background-color: #edf2f7;
        }}
        td:last-child, th:last-child {{
            text-align: right;
        }}
        td:nth-child(2), th:nth-child(2) {{
            text-align: center;
        }}
        .subsection {{
            margin-top: 25px;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #666;
            font-size: 0.9rem;
        }}
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            .container {{
                padding: 15px;
            }}
            h1 {{
                font-size: 1.5rem;
            }}
            h2 {{
                font-size: 1.1rem;
            }}
            table {{
                font-size: 0.9rem;
            }}
            th, td {{
                padding: 8px 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Model Performance Analysis Report</h1>
            <p class="timestamp">Generated: {escape_html(timestamp)}</p>
            <p class="timestamp">Last Game Included: {escape_html(last_game_date)}</p>
            <p class="disclaimer">This report shows the model's record against the opening lines for spreads, totals, and moneylines.</p>
        </header>

        <section>
            <h2>1. Model Spread Performance by Edge (All Games)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Edge Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['spread_by_edge_all']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>2. Model Spread Performance by Edge (Consensus Only)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Edge Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['spread_by_edge_consensus']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>3. Model Spread Performance by Point Spread Ranges</h2>
            <div class="subsection">
                <h3>Favorites (opening_spread &lt; 0)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Point Spread Range</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['spread_by_point_spread']['favorites']:
        html += f'''                        <tr>
                            <td>{escape_html(row['range'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Underdogs (opening_spread &gt; 0)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Point Spread Range</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['spread_by_point_spread']['underdogs']:
        html += f'''                        <tr>
                            <td>{escape_html(row['range'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>4. Model Over/Under Performance by Edge (All Games)</h2>
            <div class="subsection">
                <h3>Overs Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_all']['overs']:
        html += f'''                        <tr>
                            <td>{escape_html(row['tier'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Unders Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_all']['unders']:
        html += f'''                        <tr>
                            <td>{escape_html(row['tier'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>5. Model Over/Under Performance by Edge (Consensus Only)</h2>
            <div class="subsection">
                <h3>Overs Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_consensus']['overs']:
        html += f'''                        <tr>
                            <td>{escape_html(row['tier'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += '''                    </tbody>
                </table>
            </div>
            <div class="subsection">
                <h3>Unders Performance</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Edge Tier</th>
                            <th>Record</th>
                            <th>Win %</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    for row in analysis_data['ou_by_edge_consensus']['unders']:
        html += f'''                        <tr>
                            <td>{escape_html(row['tier'])}</td>
                            <td>{escape_html(row['record'])}</td>
                            <td>{escape_html(row['pct'])}</td>
                        </tr>
'''
    html += f'''                    </tbody>
                </table>
            </div>
        </section>

        <section>
            <h2>6. Overall Model Totals Record</h2>
            <div class="summary-item">
                <span class="summary-label">Overs (over_cover_probability &gt; 0.5):</span>
                <span class="summary-value">{escape_html(analysis_data['model_totals']['overs']['record'])}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Unders (under_cover_probability &gt; 0.5):</span>
                <span class="summary-value">{escape_html(analysis_data['model_totals']['unders']['record'])}</span>
            </div>
        </section>

        <section>
            <h2>7. Moneyline Performance by Win Probability (All Games)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_all']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>8. Moneyline Performance by Win Probability (Consensus Only)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_consensus']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>9. Moneyline Performance by Win Probability (4%+ Edge)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_by_prob_high_edge_all']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <section>
            <h2>10. Moneyline Performance by Win Probability (4%+ Edge, Consensus Only)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Win Probability Tier</th>
                        <th>Record</th>
                        <th>Win %</th>
                    </tr>
                </thead>
                <tbody>
'''
    for row in analysis_data['moneyline_by_prob_high_edge_consensus']:
        html += f'''                    <tr>
                        <td>{escape_html(row['tier'])}</td>
                        <td>{escape_html(row['record'])}</td>
                        <td>{escape_html(row['pct'])}</td>
                    </tr>
'''
    html += '''                </tbody>
            </table>
        </section>

        <footer>
            <p>Analysis generated automatically by GitHub Actions</p>
        </footer>
    </div>
</body>
</html>
'''
    return html


def save_output_files(analysis_data, timestamp, last_game_date):
    """
    Save analysis output to text and HTML files
    """
    # Ensure docs directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)
    
    # Generate and save plain text output
    text_output = generate_plain_text_output(analysis_data, timestamp, last_game_date)
    with open(TEXT_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(text_output)
    logger.info(f"[green]✓[/green] Saved plain text output to {TEXT_OUTPUT_FILE}")
    
    # Generate and save HTML output
    html_output = generate_html_output(analysis_data, timestamp, last_game_date)
    with open(HTML_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_output)
    logger.info(f"[green]✓[/green] Saved HTML output to {HTML_OUTPUT_FILE}")


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
        
        # Extract last game date
        last_game_date = get_last_game_date(df)
        logger.info(f"[cyan]Last Game Included: {last_game_date}[/cyan]")
        
        # Run all analyses (console output)
        analyze_spread_performance_by_edge(df, consensus_only=False)
        analyze_spread_performance_by_edge(df, consensus_only=True)
        analyze_spread_performance_by_point_spread(df)
        analyze_over_under_performance_by_edge(df, consensus_only=False)
        analyze_over_under_performance_by_edge(df, consensus_only=True)
        analyze_overall_model_totals_record(df)
        analyze_moneyline_performance_by_probability(df, consensus_only=False)
        analyze_moneyline_performance_by_probability(df, consensus_only=True)
        analyze_moneyline_performance_by_win_probability_high_edge(df, consensus_only=False)
        analyze_moneyline_performance_by_win_probability_high_edge(df, consensus_only=True)
        
        # Collect analysis data for file output
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        analysis_data = {
            'spread_by_edge_all': collect_spread_performance_by_edge(df, consensus_only=False),
            'spread_by_edge_consensus': collect_spread_performance_by_edge(df, consensus_only=True),
            'spread_by_point_spread': collect_spread_performance_by_point_spread(df),
            'ou_by_edge_all': collect_over_under_performance_by_edge(df, consensus_only=False),
            'ou_by_edge_consensus': collect_over_under_performance_by_edge(df, consensus_only=True),
            'model_totals': collect_overall_model_totals_record(df),
            'moneyline_all': collect_moneyline_performance_by_probability(df, consensus_only=False),
            'moneyline_consensus': collect_moneyline_performance_by_probability(df, consensus_only=True),
            'moneyline_by_prob_high_edge_all': collect_moneyline_performance_by_win_probability_high_edge(df, consensus_only=False),
            'moneyline_by_prob_high_edge_consensus': collect_moneyline_performance_by_win_probability_high_edge(df, consensus_only=True)
        }
        
        # Save output files
        save_output_files(analysis_data, timestamp, last_game_date)
        
        console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
        console.print("[bold green]Analysis Complete![/bold green]")
        console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")
        
    except Exception as e:
        logger.error(f"[red]✗[/red] Error in analysis script: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

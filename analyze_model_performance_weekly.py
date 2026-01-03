import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import logging
from rich.logging import RichHandler

# Set up logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("weekly_analysis")

console = Console()

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)

def get_week_label(week_start, week_end):
    """Generate a label for the week in format 'Dec 16-22'"""
    if week_start.month == week_end.month:
        return f"{week_start.strftime('%b')} {week_start.day}-{week_end.day}"
    else:
        return f"{week_start.strftime('%b')} {week_start.day}-{week_end.strftime('%b')} {week_end.day}"

def get_week_ranges(start_date, end_date):
    """
    Generate list of (week_start, week_end) tuples for all weeks in the range.
    Weeks run Monday-Sunday.
    
    Args:
        start_date: datetime object for the overall start date
        end_date: datetime object for the overall end date
    
    Returns:
        list of tuples: [(week_start, week_end), ...]
    """
    weeks = []
    
    # Start from the Monday of the week containing start_date
    current = start_date
    # Go back to Monday (0 = Monday, 6 = Sunday)
    days_to_monday = current.weekday()
    current = current - timedelta(days=days_to_monday)
    
    while current <= end_date:
        week_start = current
        week_end = current + timedelta(days=6)  # Sunday
        
        # Only include weeks that overlap with our date range
        if week_end >= start_date and week_start <= end_date:
            weeks.append((week_start, week_end))
        
        current = current + timedelta(days=7)
    
    return weeks

def load_game_data(start_date, end_date):
    """
    Load game data from all CSV files in the range.
    
    Args:
        start_date: datetime object
        end_date: datetime object
    
    Returns:
        DataFrame: Combined game data
    """
    config = load_config()
    data_dir = Path(config['data_dir'])
    
    all_data = []
    current_date = start_date
    
    logger.info("[bold cyan]Loading game data...[/bold cyan]")
    
    while current_date <= end_date:
        filename = f"kenpom_{current_date.strftime('%Y%m%d')}.csv"
        filepath = data_dir / filename
        
        if filepath.exists():
            try:
                df = pd.read_csv(filepath)
                df['date'] = current_date
                all_data.append(df)
                logger.info(f"[green]✓[/green] Loaded {filename} ({len(df)} games)")
            except Exception as e:
                logger.warning(f"[yellow]⚠[/yellow] Error loading {filename}: {e}")
        else:
            logger.debug(f"[dim]File not found: {filename}[/dim]")
        
        current_date += timedelta(days=1)
    
    if not all_data:
        logger.error("[red]No data files found in date range[/red]")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"[bold green]Total games loaded: {len(combined_df)}[/bold green]")
    
    return combined_df

def get_model_columns():
    """Return list of model columns to analyze"""
    return [
        'kenpom_pred',
        'massey_pred',
        'sagarin_pred',
        'bpi_pred',
        'dunkel_pred',
        'avg5_pred'
    ]

def calculate_accuracy(df, model_col):
    """
    Calculate accuracy for a model column.
    
    Args:
        df: DataFrame with game data
        model_col: Name of the prediction column
    
    Returns:
        float: Accuracy (0-1) or None if no valid predictions
    """
    valid_mask = df[model_col].notna() & df['winner'].notna()
    valid_df = df[valid_mask]
    
    if len(valid_df) == 0:
        return None
    
    correct = (valid_df[model_col] == valid_df['winner']).sum()
    total = len(valid_df)
    
    return correct / total if total > 0 else None

def filter_data_by_week(df, week_start, week_end):
    """
    Filter DataFrame to only include games from the specified week.
    
    Args:
        df: pandas DataFrame with game data
        week_start: datetime object for Monday
        week_end: datetime object for Sunday
    
    Returns:
        DataFrame: Filtered data for the week
    """
    # Convert date column to datetime
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert week_start and week_end to timezone-naive for comparison
    week_start_naive = week_start.replace(tzinfo=None)
    week_end_naive = week_end.replace(tzinfo=None)
    
    # Filter for the week
    mask = (df['date'] >= week_start_naive) & (df['date'] <= week_end_naive)
    week_data = df[mask].copy()
    
    logger.info(f"[cyan]Filtered to {len(week_data)} rows for {get_week_label(week_start, week_end)}[/cyan]")
    
    return week_data

def analyze_week(df, week_start, week_end):
    """
    Analyze model performance for a single week.
    
    Args:
        df: DataFrame with all game data
        week_start: datetime object for Monday
        week_end: datetime object for Sunday
    
    Returns:
        dict: Results for each model
    """
    week_data = filter_data_by_week(df, week_start, week_end)
    
    if len(week_data) == 0:
        logger.warning(f"[yellow]No games found for {get_week_label(week_start, week_end)}[/yellow]")
        return None
    
    results = {
        'week_label': get_week_label(week_start, week_end),
        'week_start': week_start,
        'week_end': week_end,
        'total_games': len(week_data),
        'models': {}
    }
    
    model_cols = get_model_columns()
    
    for model_col in model_cols:
        accuracy = calculate_accuracy(week_data, model_col)
        
        # Count valid predictions
        valid_count = week_data[model_col].notna().sum()
        
        results['models'][model_col] = {
            'accuracy': accuracy,
            'valid_predictions': valid_count
        }
    
    return results

def print_weekly_results(all_results):
    """
    Print results in a formatted table.
    
    Args:
        all_results: List of weekly result dictionaries
    """
    if not all_results:
        logger.error("[red]No results to display[/red]")
        return
    
    # Create table
    table = Table(title="Weekly Model Performance", show_header=True, header_style="bold magenta")
    
    # Add columns
    table.add_column("Week", style="cyan", width=12)
    table.add_column("Games", justify="right", style="white")
    
    model_cols = get_model_columns()
    model_names = {
        'kenpom_pred': 'KenPom',
        'massey_pred': 'Massey',
        'sagarin_pred': 'Sagarin',
        'bpi_pred': 'BPI',
        'dunkel_pred': 'Dunkel',
        'avg5_pred': 'Avg5'
    }
    
    for model_col in model_cols:
        table.add_column(model_names[model_col], justify="right", style="green")
    
    # Add rows
    for result in all_results:
        row = [
            result['week_label'],
            str(result['total_games'])
        ]
        
        for model_col in model_cols:
            model_result = result['models'][model_col]
            if model_result['accuracy'] is not None:
                acc_pct = model_result['accuracy'] * 100
                valid = model_result['valid_predictions']
                row.append(f"{acc_pct:.1f}% ({valid})")
            else:
                row.append("N/A")
        
        table.add_row(*row)
    
    console.print("\n")
    console.print(table)
    console.print("\n")

def print_summary_statistics(all_results):
    """
    Print summary statistics across all weeks.
    
    Args:
        all_results: List of weekly result dictionaries
    """
    if not all_results:
        return
    
    model_cols = get_model_columns()
    model_names = {
        'kenpom_pred': 'KenPom',
        'massey_pred': 'Massey',
        'sagarin_pred': 'Sagarin',
        'bpi_pred': 'BPI',
        'dunkel_pred': 'Dunkel',
        'avg5_pred': 'Avg5'
    }
    
    # Create summary table
    table = Table(title="Overall Summary", show_header=True, header_style="bold magenta")
    table.add_column("Model", style="cyan")
    table.add_column("Avg Accuracy", justify="right", style="green")
    table.add_column("Min", justify="right", style="yellow")
    table.add_column("Max", justify="right", style="yellow")
    table.add_column("Total Predictions", justify="right", style="white")
    
    for model_col in model_cols:
        accuracies = []
        total_valid = 0
        
        for result in all_results:
            model_result = result['models'][model_col]
            if model_result['accuracy'] is not None:
                accuracies.append(model_result['accuracy'])
                total_valid += model_result['valid_predictions']
        
        if accuracies:
            avg_acc = np.mean(accuracies) * 100
            min_acc = np.min(accuracies) * 100
            max_acc = np.max(accuracies) * 100
            
            table.add_row(
                model_names[model_col],
                f"{avg_acc:.1f}%",
                f"{min_acc:.1f}%",
                f"{max_acc:.1f}%",
                str(total_valid)
            )
    
    console.print(table)
    console.print("\n")

def main():
    """Main execution function"""
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   Weekly Model Performance Analysis   [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════[/bold cyan]\n")
    
    # Define date range
    start_date = datetime(2024, 12, 9)
    end_date = datetime(2024, 12, 29)
    
    logger.info(f"[bold]Analysis Period:[/bold] {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Load all game data
    all_games = load_game_data(start_date, end_date)
    
    if all_games.empty:
        logger.error("[red]No game data available. Exiting.[/red]")
        return
    
    # Get week ranges
    weeks = get_week_ranges(start_date, end_date)
    logger.info(f"[bold]Number of weeks:[/bold] {len(weeks)}\n")
    
    # Analyze each week
    all_results = []
    for week_start, week_end in weeks:
        logger.info(f"[bold yellow]Analyzing week: {get_week_label(week_start, week_end)}[/bold yellow]")
        result = analyze_week(all_games, week_start, week_end)
        if result:
            all_results.append(result)
    
    # Print results
    print_weekly_results(all_results)
    print_summary_statistics(all_results)
    
    logger.info("[bold green]✓ Analysis complete![/bold green]\n")

if __name__ == "__main__":
    main()

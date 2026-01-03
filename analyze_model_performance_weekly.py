import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from rich.console import Console
from rich.table import Table
import logging
from rich.logging import RichHandler

# Set up logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")

console = Console()

def load_data(filepath):
    """Load the CSV data with error handling."""
    try:
        df = pd.read_csv(filepath)
        logger.info(f"[green]Successfully loaded data from {filepath}[/green]")
        logger.info(f"[cyan]Total rows: {len(df)}[/cyan]")
        return df
    except FileNotFoundError:
        logger.error(f"[red]Error: File {filepath} not found[/red]")
        return None
    except Exception as e:
        logger.error(f"[red]Error loading data: {str(e)}[/red]")
        return None

def get_week_label(week_start, week_end):
    """Generate a readable week label."""
    return f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"

def get_previous_week_range():
    """
    Calculate the date range for the previous complete week (Monday-Sunday).
    
    Returns:
        tuple: (week_start, week_end) datetime objects in Eastern Time
    """
    # Get current time in Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Calculate last Monday
    days_since_monday = (now.weekday() + 7) % 7  # 0 = Monday, 6 = Sunday
    last_monday = now - timedelta(days=days_since_monday + 7)
    
    # Set to start of day (Monday 00:00:00)
    week_start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate last Sunday (6 days after Monday)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return week_start, week_end

def get_week_before_last_range():
    """
    Calculate the date range for the week before last (Monday-Sunday).
    
    Returns:
        tuple: (week_start, week_end) datetime objects in Eastern Time
    """
    # Get current time in Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Calculate the Monday two weeks ago
    days_since_monday = (now.weekday() + 7) % 7
    two_weeks_ago_monday = now - timedelta(days=days_since_monday + 14)
    
    # Set to start of day (Monday 00:00:00)
    week_start = two_weeks_ago_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate Sunday (6 days after Monday)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return week_start, week_end

def calculate_metrics(df):
    """
    Calculate performance metrics from the dataframe.
    
    Args:
        df: pandas DataFrame with prediction data
    
    Returns:
        dict: Dictionary containing calculated metrics
    """
    if df is None or len(df) == 0:
        return {
            'total_games': 0,
            'correct_predictions': 0,
            'accuracy': 0.0,
            'avg_confidence': 0.0,
            'total_units_wagered': 0.0,
            'net_profit': 0.0,
            'roi': 0.0,
            'high_conf_games': 0,
            'high_conf_correct': 0,
            'high_conf_accuracy': 0.0
        }
    
    # Basic metrics
    total_games = len(df)
    correct_predictions = df['correct'].sum()
    accuracy = (correct_predictions / total_games * 100) if total_games > 0 else 0.0
    
    # Confidence metrics
    avg_confidence = df['confidence'].mean()
    
    # Financial metrics (assuming unit size of $100)
    UNIT_SIZE = 100
    df['wager'] = df['confidence'] * UNIT_SIZE
    total_units_wagered = df['wager'].sum()
    
    # Calculate profit/loss for each bet
    df['profit'] = df.apply(
        lambda row: row['wager'] * (row['odds'] - 1) if row['correct'] else -row['wager'],
        axis=1
    )
    net_profit = df['profit'].sum()
    roi = (net_profit / total_units_wagered * 100) if total_units_wagered > 0 else 0.0
    
    # High confidence metrics (>=0.7)
    high_conf_df = df[df['confidence'] >= 0.7]
    high_conf_games = len(high_conf_df)
    high_conf_correct = high_conf_df['correct'].sum() if high_conf_games > 0 else 0
    high_conf_accuracy = (high_conf_correct / high_conf_games * 100) if high_conf_games > 0 else 0.0
    
    return {
        'total_games': total_games,
        'correct_predictions': correct_predictions,
        'accuracy': accuracy,
        'avg_confidence': avg_confidence,
        'total_units_wagered': total_units_wagered,
        'net_profit': net_profit,
        'roi': roi,
        'high_conf_games': high_conf_games,
        'high_conf_correct': high_conf_correct,
        'high_conf_accuracy': high_conf_accuracy
    }

def display_metrics_table(metrics, week_label):
    """
    Display metrics in a formatted Rich table.
    
    Args:
        metrics: Dictionary of calculated metrics
        week_label: String label for the week being displayed
    """
    table = Table(title=f"Model Performance - {week_label}", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="green", width=20)
    
    # Add rows
    table.add_row("Total Games", str(metrics['total_games']))
    table.add_row("Correct Predictions", str(metrics['correct_predictions']))
    table.add_row("Accuracy", f"{metrics['accuracy']:.2f}%")
    table.add_row("Average Confidence", f"{metrics['avg_confidence']:.3f}")
    table.add_row("", "")  # Spacer
    table.add_row("Total Units Wagered", f"${metrics['total_units_wagered']:.2f}")
    table.add_row("Net Profit/Loss", f"${metrics['net_profit']:.2f}")
    table.add_row("ROI", f"{metrics['roi']:.2f}%")
    table.add_row("", "")  # Spacer
    table.add_row("High Confidence Games (≥0.7)", str(metrics['high_conf_games']))
    table.add_row("High Confidence Correct", str(metrics['high_conf_correct']))
    table.add_row("High Confidence Accuracy", f"{metrics['high_conf_accuracy']:.2f}%")
    
    console.print(table)

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

def main():
    """Main execution function."""
    console.print("\n[bold blue]═══════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]   Model Performance Analysis - Weekly Report   [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]\n")
    
    # Load data
    filepath = "data/predictions_with_actuals.csv"
    df = load_data(filepath)
    
    if df is None:
        return
    
    # Get week ranges
    prev_week_start, prev_week_end = get_previous_week_range()
    week_before_start, week_before_end = get_week_before_last_range()
    
    logger.info(f"[yellow]Previous Week: {get_week_label(prev_week_start, prev_week_end)}[/yellow]")
    logger.info(f"[yellow]Week Before Last: {get_week_label(week_before_start, week_before_end)}[/yellow]\n")
    
    # Filter data for each week
    prev_week_df = filter_data_by_week(df, prev_week_start, prev_week_end)
    week_before_df = filter_data_by_week(df, week_before_start, week_before_end)
    
    # Calculate and display metrics for previous week
    console.print("\n")
    prev_metrics = calculate_metrics(prev_week_df)
    display_metrics_table(prev_metrics, get_week_label(prev_week_start, prev_week_end))
    
    # Calculate and display metrics for week before last
    console.print("\n")
    week_before_metrics = calculate_metrics(week_before_df)
    display_metrics_table(week_before_metrics, get_week_label(week_before_start, week_before_end))
    
    # Display comparison
    console.print("\n[bold blue]═══════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]            Week-over-Week Comparison           [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════[/bold blue]\n")
    
    comparison_table = Table(show_header=True, header_style="bold magenta")
    comparison_table.add_column("Metric", style="cyan", width=25)
    comparison_table.add_column("Previous Week", style="green", width=20)
    comparison_table.add_column("Week Before", style="yellow", width=20)
    comparison_table.add_column("Change", style="bold", width=20)
    
    # Helper function to format change with color
    def format_change(current, previous, is_currency=False, is_percentage=False):
        if previous == 0:
            return "N/A"
        
        change = current - previous
        prefix = "+" if change > 0 else ""
        
        if is_currency:
            change_str = f"{prefix}${change:.2f}"
        elif is_percentage:
            change_str = f"{prefix}{change:.2f}pp"
        else:
            change_str = f"{prefix}{change:.2f}"
        
        # Color code based on metric type
        if is_currency or is_percentage:
            color = "green" if change > 0 else "red" if change < 0 else "white"
        else:
            color = "white"
        
        return f"[{color}]{change_str}[/{color}]"
    
    # Add comparison rows
    comparison_table.add_row(
        "Accuracy",
        f"{prev_metrics['accuracy']:.2f}%",
        f"{week_before_metrics['accuracy']:.2f}%",
        format_change(prev_metrics['accuracy'], week_before_metrics['accuracy'], is_percentage=True)
    )
    
    comparison_table.add_row(
        "Net Profit/Loss",
        f"${prev_metrics['net_profit']:.2f}",
        f"${week_before_metrics['net_profit']:.2f}",
        format_change(prev_metrics['net_profit'], week_before_metrics['net_profit'], is_currency=True)
    )
    
    comparison_table.add_row(
        "ROI",
        f"{prev_metrics['roi']:.2f}%",
        f"{week_before_metrics['roi']:.2f}%",
        format_change(prev_metrics['roi'], week_before_metrics['roi'], is_percentage=True)
    )
    
    comparison_table.add_row(
        "High Conf Accuracy",
        f"{prev_metrics['high_conf_accuracy']:.2f}%",
        f"{week_before_metrics['high_conf_accuracy']:.2f}%",
        format_change(prev_metrics['high_conf_accuracy'], week_before_metrics['high_conf_accuracy'], is_percentage=True)
    )
    
    console.print(comparison_table)
    console.print("\n")

if __name__ == "__main__":
    main()

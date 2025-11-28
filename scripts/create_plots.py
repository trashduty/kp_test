"""
Create basketball analytics plots for offensive/defensive efficiency vs adjusted tempo.

This script generates two publication-ready plots:
1. Offensive Efficiency (ORtg) vs Adjusted Tempo (AdjT)
2. Defensive Efficiency (DRtg) vs Adjusted Tempo (AdjT)

Features:
- Quadrant shading based on median values
- Team logos for top/bottom 10% performers
- Professional styling for GitHub Pages
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import requests
from io import BytesIO
import numpy as np

# Get the script directory and repository root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

# File paths
KENPOM_CSV = os.path.join(REPO_ROOT, "kenpom_stats.csv")
LOGOS_CSV = os.path.join(REPO_ROOT, "ncaa_teams_colors_logos_CBB.csv")
OUTPUT_DIR = os.path.join(REPO_ROOT, "docs", "plots")


def load_data():
    """Load and merge KenPom stats with team logos."""
    # Load KenPom statistics
    kenpom_df = pd.read_csv(KENPOM_CSV)
    
    # Load team logos
    logos_df = pd.read_csv(LOGOS_CSV).drop_duplicates(subset='current_team')
    
    # Merge datasets
    merged_df = kenpom_df.merge(
        logos_df, 
        how='left', 
        left_on='Team', 
        right_on='current_team'
    )
    
    return merged_df


def get_logo_image(url, zoom=0.04):
    """Fetch and return a logo image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        # Convert to RGBA if needed for transparency
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        return OffsetImage(img, zoom=zoom)
    except Exception as e:
        print(f"Could not load logo: {url} - {e}")
        return None


def get_highlight_teams(df, rating_col, tempo_col):
    """Get teams that should display logos (top/bottom 10%)."""
    # Calculate percentiles for rating column
    rating_10 = df[rating_col].quantile(0.10)
    rating_90 = df[rating_col].quantile(0.90)
    
    # Calculate percentiles for tempo
    tempo_10 = df[tempo_col].quantile(0.10)
    tempo_90 = df[tempo_col].quantile(0.90)
    
    # Get teams in extreme rating percentiles
    if rating_col == 'DRtg':
        # For DRtg, lower is better, so top 10% has lowest values
        top_rating = df[df[rating_col] <= rating_10]['Team'].tolist()
        bottom_rating = df[df[rating_col] >= rating_90]['Team'].tolist()
    else:
        # For ORtg, higher is better
        top_rating = df[df[rating_col] >= rating_90]['Team'].tolist()
        bottom_rating = df[df[rating_col] <= rating_10]['Team'].tolist()
    
    # Get teams in extreme tempo percentiles
    top_tempo = df[df[tempo_col] >= tempo_90]['Team'].tolist()
    bottom_tempo = df[df[tempo_col] <= tempo_10]['Team'].tolist()
    
    # Combine all highlight teams
    highlight_teams = set(top_rating + bottom_rating + top_tempo + bottom_tempo)
    
    return highlight_teams


def create_quadrant_plot(df, x_col, y_col, title, xlabel, ylabel, output_file, 
                         invert_y=False, higher_is_better_y=True):
    """
    Create a quadrant plot with team logos for highlighted teams.
    
    Parameters:
    - df: DataFrame with team data
    - x_col: Column for x-axis (e.g., 'AdjT')
    - y_col: Column for y-axis (e.g., 'ORtg' or 'DRtg')
    - title: Plot title
    - xlabel: X-axis label
    - ylabel: Y-axis label
    - output_file: Output file path
    - invert_y: Whether to invert y-axis (True for DRtg where lower is better)
    - higher_is_better_y: Whether higher values are better on y-axis
    """
    # Calculate medians for quadrant lines
    median_x = df[x_col].median()
    median_y = df[y_col].median()
    
    # Get teams that should show logos
    highlight_teams = get_highlight_teams(df, y_col, x_col)
    
    # Create figure with professional styling
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Set background color
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    
    # Define quadrant colors based on whether higher y is better
    if higher_is_better_y:
        # Top-right (high tempo, high rating) - good
        # Bottom-left (low tempo, low rating) - bad
        colors = {
            'top_right': '#90EE90',    # Light green - good offense, high tempo
            'top_left': '#FFD700',     # Gold - good offense, low tempo
            'bottom_right': '#FFD700', # Gold - bad offense, high tempo
            'bottom_left': '#FFB6C1',  # Light pink - bad offense, low tempo
        }
    else:
        # For DRtg (lower is better)
        colors = {
            'top_right': '#FFB6C1',    # Light pink - bad defense, high tempo
            'top_left': '#FFD700',     # Gold - bad defense, low tempo
            'bottom_right': '#FFD700', # Gold - good defense, high tempo
            'bottom_left': '#90EE90',  # Light green - good defense, low tempo
        }
    
    # Get axis limits
    x_min, x_max = df[x_col].min() - 0.5, df[x_col].max() + 0.5
    y_min, y_max = df[y_col].min() - 0.5, df[y_col].max() + 0.5
    
    # Draw quadrant shading
    alpha = 0.2
    # Top-right quadrant
    ax.fill_between([median_x, x_max], median_y, y_max, 
                    color=colors['top_right'], alpha=alpha)
    # Top-left quadrant
    ax.fill_between([x_min, median_x], median_y, y_max, 
                    color=colors['top_left'], alpha=alpha)
    # Bottom-right quadrant
    ax.fill_between([median_x, x_max], y_min, median_y, 
                    color=colors['bottom_right'], alpha=alpha)
    # Bottom-left quadrant
    ax.fill_between([x_min, median_x], y_min, median_y, 
                    color=colors['bottom_left'], alpha=alpha)
    
    # Draw median lines
    ax.axhline(median_y, linestyle='--', color='gray', alpha=0.7, linewidth=1.5)
    ax.axvline(median_x, linestyle='--', color='gray', alpha=0.7, linewidth=1.5)
    
    # Plot all teams as dots first
    ax.scatter(df[x_col], df[y_col], 
               s=30, c='#1f77b4', alpha=0.5, edgecolors='white', linewidth=0.5)
    
    # Add logos or labels for highlighted teams
    for _, row in df.iterrows():
        team = row['Team']
        x = row[x_col]
        y = row[y_col]
        
        if team in highlight_teams:
            logo_url = row.get('logo')
            if pd.notna(logo_url):
                im = get_logo_image(logo_url, zoom=0.04)
                if im is not None:
                    ab = AnnotationBbox(im, (x, y), frameon=False, pad=0)
                    ax.add_artist(ab)
                else:
                    # Fallback to text label
                    ax.annotate(team, (x, y), fontsize=7, ha='center', va='center',
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                                       edgecolor='gray', alpha=0.8))
            else:
                ax.annotate(team, (x, y), fontsize=7, ha='center', va='center',
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                                   edgecolor='gray', alpha=0.8))
    
    # Styling
    ax.set_xlabel(xlabel, fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    
    # Set axis limits with padding
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    # Invert y-axis if needed (for DRtg where lower is better visually)
    if invert_y:
        ax.invert_yaxis()
    
    # Add grid
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Add median value annotations
    ax.text(x_max - 0.3, median_y, f'Median: {median_y:.1f}', 
            fontsize=9, va='bottom', ha='right', style='italic', color='gray')
    ax.text(median_x, y_max - 0.3 if not invert_y else y_min + 0.3, 
            f'Median: {median_x:.1f}', 
            fontsize=9, va='top' if not invert_y else 'bottom', ha='left', 
            style='italic', color='gray')
    
    # Add legend for quadrants
    if higher_is_better_y:
        legend_text = (
            "• Green: High efficiency, fast tempo (elite)\n"
            "• Gold: Mixed performance\n"
            "• Pink: Low efficiency, slow tempo"
        )
    else:
        legend_text = (
            "• Green: Strong defense, slow tempo (elite)\n"
            "• Gold: Mixed performance\n"
            "• Pink: Weak defense, fast tempo"
        )
    
    ax.text(0.02, 0.02, legend_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor='gray', alpha=0.9))
    
    # Add data source note
    ax.text(0.98, 0.02, 'Data: KenPom | Logos shown for top/bottom 10%', 
            transform=ax.transAxes, fontsize=8, 
            verticalalignment='bottom', horizontalalignment='right',
            style='italic', color='gray')
    
    # Tight layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ Saved: {output_file}")


def main():
    """Main function to generate both plots."""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} teams")
    
    # Create Plot 1: Offensive Efficiency vs Adjusted Tempo
    print("\nCreating Offensive Efficiency vs Tempo plot...")
    create_quadrant_plot(
        df=df,
        x_col='AdjT',
        y_col='ORtg',
        title='Offensive Efficiency vs Adjusted Tempo\nAll 365 NCAA Teams',
        xlabel='Adjusted Tempo (AdjT)',
        ylabel='Offensive Rating (ORtg)',
        output_file=os.path.join(OUTPUT_DIR, 'offensive_efficiency_tempo.png'),
        invert_y=False,
        higher_is_better_y=True
    )
    
    # Create Plot 2: Defensive Efficiency vs Adjusted Tempo
    print("\nCreating Defensive Efficiency vs Tempo plot...")
    create_quadrant_plot(
        df=df,
        x_col='AdjT',
        y_col='DRtg',
        title='Defensive Efficiency vs Adjusted Tempo\nAll 365 NCAA Teams',
        xlabel='Adjusted Tempo (AdjT)',
        ylabel='Defensive Rating (DRtg)',
        output_file=os.path.join(OUTPUT_DIR, 'defensive_efficiency_tempo.png'),
        invert_y=True,  # Lower DRtg is better, so invert for visual clarity
        higher_is_better_y=False
    )
    
    print("\n✅ All plots generated successfully!")


if __name__ == "__main__":
    main()

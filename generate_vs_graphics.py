#!/usr/bin/env python3
"""
Generate VS graphics for daily basketball matchups.

This script:
1. Downloads kp.csv and logos.csv from the trashduty/cbb repository
2. Identifies games for today and tomorrow
3. Matches team names with logos
4. Generates PNG images (1200x600px) showing:
   - Away team logo (left)
   - "VS" text (center)
   - Home team logo (right)
   - Game date (bottom)
5. Saves images to _vs_graphics/ directory
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO, StringIO
import os
import re


# Constants
KP_CSV_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/kp.csv"
LOGOS_CSV_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/logos.csv"
OUTPUT_DIR = "_vs_graphics"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 600
LOGO_SIZE = 300
BACKGROUND_COLOR = (245, 245, 245)  # Light gray

# Font paths for different systems
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:\\Windows\\Fonts\\arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
]

DATE_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:\\Windows\\Fonts\\arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
]


def download_csv(url):
    """Download CSV file from URL and return as pandas DataFrame."""
    try:
        print(f"Downloading {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except requests.RequestException as e:
        raise Exception(f"Failed to download {url}: {e}")


def slugify(text):
    """Convert text to lowercase slug with hyphens."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def download_logo(url, cache_dir="_logo_cache"):
    """Download logo from URL and return PIL Image. Cache for reuse."""
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create cache filename using hash of URL to avoid collisions
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    file_ext = url.split('.')[-1].lower()
    if file_ext not in ['png', 'jpg', 'jpeg', 'svg', 'gif']:
        file_ext = 'png'
    cache_filename = os.path.join(cache_dir, f"{url_hash}.{file_ext}")
    
    # Check cache first
    if os.path.exists(cache_filename):
        try:
            return Image.open(cache_filename).convert('RGBA')
        except Exception as e:
            print(f"Warning: Failed to load cached logo {cache_filename}: {e}")
    
    # Download logo
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        
        # Save to cache
        img.save(cache_filename, 'PNG')
        return img
    except Exception as e:
        print(f"Warning: Failed to download logo from {url}: {e}")
        return None


def create_placeholder_logo(size=LOGO_SIZE):
    """Create a placeholder logo when actual logo is not available."""
    img = Image.new('RGBA', (size, size), (200, 200, 200, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "?" in the center
    font = None
    for font_path in FONT_PATHS:
        try:
            font = ImageFont.truetype(font_path, 120)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    text = "?"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill=(100, 100, 100, 255), font=font)
    return img


def resize_logo(logo, target_size=LOGO_SIZE):
    """Resize logo to target size while maintaining aspect ratio."""
    # Create a copy to avoid modifying the original
    logo_copy = logo.copy()
    logo_copy.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
    return logo_copy


def match_team_logo(team_name, logos_df):
    """Match team name to logo URL from logos dataframe."""
    # Try exact match first
    match = logos_df[logos_df['ncaa_name'] == team_name]
    if not match.empty:
        return match.iloc[0]['logos']
    
    # Try case-insensitive match
    match = logos_df[logos_df['ncaa_name'].str.lower() == team_name.lower()]
    if not match.empty:
        return match.iloc[0]['logos']
    
    # Try partial match
    for idx, row in logos_df.iterrows():
        if team_name.lower() in row['ncaa_name'].lower() or row['ncaa_name'].lower() in team_name.lower():
            return row['logos']
    
    return None


def generate_vs_graphic(away_team, home_team, game_date_str, away_logo_url, home_logo_url, output_path):
    """Generate a VS graphic PNG image."""
    
    # Create base image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Download and resize logos
    away_logo = download_logo(away_logo_url) if away_logo_url else None
    home_logo = download_logo(home_logo_url) if home_logo_url else None
    
    if away_logo is None:
        print(f"Warning: Using placeholder for {away_team} logo")
        away_logo = create_placeholder_logo()
    else:
        away_logo = resize_logo(away_logo)
    
    if home_logo is None:
        print(f"Warning: Using placeholder for {home_team} logo")
        home_logo = create_placeholder_logo()
    else:
        home_logo = resize_logo(home_logo)
    
    # Calculate positions
    # Away logo on left
    away_x = 150
    away_y = (IMAGE_HEIGHT - LOGO_SIZE) // 2
    
    # Home logo on right
    home_x = IMAGE_WIDTH - 150 - LOGO_SIZE
    home_y = (IMAGE_HEIGHT - LOGO_SIZE) // 2
    
    # Center logos vertically within their space
    away_logo_y = away_y + (LOGO_SIZE - away_logo.height) // 2
    home_logo_y = home_y + (LOGO_SIZE - home_logo.height) // 2
    
    away_logo_x = away_x + (LOGO_SIZE - away_logo.width) // 2
    home_logo_x = home_x + (LOGO_SIZE - home_logo.width) // 2
    
    # Paste logos
    img.paste(away_logo, (away_logo_x, away_logo_y), away_logo)
    img.paste(home_logo, (home_logo_x, home_logo_y), home_logo)
    
    # Draw "VS" text in center
    vs_font = None
    for font_path in FONT_PATHS:
        try:
            vs_font = ImageFont.truetype(font_path, 100)
            break
        except:
            continue
    
    date_font = None
    for font_path in DATE_FONT_PATHS:
        try:
            date_font = ImageFont.truetype(font_path, 36)
            break
        except:
            continue
    
    if vs_font is None:
        vs_font = ImageFont.load_default()
    if date_font is None:
        date_font = ImageFont.load_default()
    
    vs_text = "VS"
    vs_bbox = draw.textbbox((0, 0), vs_text, font=vs_font)
    vs_width = vs_bbox[2] - vs_bbox[0]
    vs_height = vs_bbox[3] - vs_bbox[1]
    
    vs_x = (IMAGE_WIDTH - vs_width) // 2
    vs_y = (IMAGE_HEIGHT - vs_height) // 2 - 30
    
    draw.text((vs_x, vs_y), vs_text, fill=(50, 50, 50), font=vs_font)
    
    # Draw date at bottom
    try:
        date_obj = datetime.strptime(game_date_str, '%Y%m%d')
        formatted_date = date_obj.strftime('%B %d, %Y')
    except:
        formatted_date = game_date_str
    
    date_bbox = draw.textbbox((0, 0), formatted_date, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (IMAGE_WIDTH - date_width) // 2
    date_y = IMAGE_HEIGHT - 80
    
    draw.text((date_x, date_y), formatted_date, fill=(80, 80, 80), font=date_font)
    
    # Save image
    img.save(output_path, 'PNG')
    print(f"Generated: {output_path}")


def get_target_dates():
    """Get today and tomorrow's dates in YYYYMMDD format."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    return [
        today.strftime('%Y%m%d'),
        tomorrow.strftime('%Y%m%d')
    ]


def main():
    """Main execution function."""
    print("Starting VS graphics generation...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Download data
    print("Downloading data files...")
    kp_df = download_csv(KP_CSV_URL)
    logos_df = download_csv(LOGOS_CSV_URL)
    
    print(f"Loaded {len(kp_df)} rows from kp.csv")
    print(f"Loaded {len(logos_df)} logos from logos.csv")
    
    # Get target dates
    target_dates = get_target_dates()
    print(f"Filtering for dates: {target_dates}")
    
    # Filter for target dates
    kp_df['Game Date'] = kp_df['Game Date'].astype(str)
    games_df = kp_df[kp_df['Game Date'].isin(target_dates)].copy()
    
    print(f"Found {len(games_df)} game rows for target dates")
    
    # Group by game to avoid duplicates (each game has 2 rows)
    games_df['game_key'] = games_df['Game Date'] + '_' + games_df['Away Team'] + '_' + games_df['Home Team']
    unique_games = games_df.drop_duplicates(subset='game_key')
    
    print(f"Processing {len(unique_games)} unique games...")
    
    # Generate graphics for each game
    generated_count = 0
    for idx, row in unique_games.iterrows():
        away_team = row['Away Team']
        home_team = row['Home Team']
        game_date = row['Game Date']
        
        print(f"\nProcessing: {away_team} @ {home_team} on {game_date}")
        
        # Match logos
        away_logo_url = match_team_logo(away_team, logos_df)
        home_logo_url = match_team_logo(home_team, logos_df)
        
        if away_logo_url is None:
            print(f"Warning: No logo found for {away_team}")
        if home_logo_url is None:
            print(f"Warning: No logo found for {home_team}")
        
        # Generate filename
        away_slug = slugify(away_team)
        home_slug = slugify(home_team)
        
        try:
            date_obj = datetime.strptime(game_date, '%Y%m%d')
            date_prefix = date_obj.strftime('%Y-%m-%d')
        except:
            date_prefix = game_date
        
        filename = f"{date_prefix}-{away_slug}-vs-{home_slug}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        # Generate graphic
        try:
            generate_vs_graphic(
                away_team=away_team,
                home_team=home_team,
                game_date_str=game_date,
                away_logo_url=away_logo_url,
                home_logo_url=home_logo_url,
                output_path=output_path
            )
            generated_count += 1
        except Exception as e:
            print(f"Error generating graphic for {away_team} vs {home_team}: {e}")
    
    print(f"\n✓ Successfully generated {generated_count} graphics")
    print(f"✓ Output directory: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

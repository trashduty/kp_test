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
CROSSWALK_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/data/crosswalk.csv"
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


def convert_api_to_kenpom_name(team_name, crosswalk_df):
    """
    Step 2-3: Convert team name from API format to KenPom format using crosswalk.
    
    Args:
        team_name: Team name from kp.csv (Away Team or Home Team column)
        crosswalk_df: DataFrame loaded from data/crosswalk.csv
    
    Returns:
        KenPom name from crosswalk "kenpom" column, or original name if not found
    """
    if crosswalk_df is None or crosswalk_df.empty:
        return team_name
    
    team_name_lower = team_name.strip().lower()
    for _, row in crosswalk_df.iterrows():
        api_name = str(row['API']).strip().lower()
        if api_name == team_name_lower:
            kenpom_name = str(row['kenpom']).strip()
            print(f"  [Crosswalk] '{team_name}' (API) -> '{kenpom_name}' (kenpom)")
            return kenpom_name
    
    print(f"  [Crosswalk] '{team_name}' not found in crosswalk, using original name")
    return team_name


def download_logo(url, cache_dir="_logo_cache"):
    """Download logo from URL and return PIL Image. Cache for reuse. Handles SVG files."""
    if url is None:
        return None
    
    print(f"  Downloading logo from: {url}")
    
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create cache filename using hash of URL to avoid collisions
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    file_ext = url.split('.')[-1].lower()
    if file_ext not in ['png', 'jpg', 'jpeg', 'svg', 'gif']:
        file_ext = 'png'
    cache_filename = os.path.join(cache_dir, f"{url_hash}.png")  # Always cache as PNG
    
    # Check cache first
    if os.path.exists(cache_filename):
        try:
            img = Image.open(cache_filename).convert('RGBA')
            print(f"  ✓ Loaded from cache")
            return img
        except Exception as e:
            print(f"  ⚠ Failed to load cached logo {cache_filename}: {e}")
    
    # Download logo
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Handle SVG files
        if url.lower().endswith('.svg'):
            try:
                import cairosvg
                png_data = cairosvg.svg2png(bytestring=response.content)
                img = Image.open(BytesIO(png_data)).convert('RGBA')
                print(f"  ✓ Successfully converted SVG to PNG")
            except ImportError:
                print(f"  ⚠ cairosvg not installed, cannot process SVG - using placeholder")
                return None
            except Exception as e:
                print(f"  ✗ Failed to process SVG: {e}")
                return None
        else:
            # Handle regular image formats
            img = Image.open(BytesIO(response.content)).convert('RGBA')
            print(f"  ✓ Successfully downloaded and processed logo")
        
        # Save to cache
        img.save(cache_filename, 'PNG')
        return img
    except Exception as e:
        print(f"  ✗ Failed to download logo: {e}")
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


def find_team_logo(kenpom_name, logos_df):
    """
    Step 5: Find team logo using the kenpom name.
    
    Args:
        kenpom_name: Team name in KenPom format (from crosswalk conversion)
        logos_df: DataFrame loaded from data/logos.csv
    
    Returns:
        Logo URL or None
    """
    if 'ncaa_name' in logos_df.columns:
        for _, row in logos_df.iterrows():
            ncaa_name = str(row['ncaa_name']).strip()
            if ncaa_name == kenpom_name:
                logo_url = row['logos']
                print(f"  [Logo] Found logo for '{kenpom_name}': {logo_url}")
                return logo_url
    
    print(f"  [Logo] Warning: No logo found for '{kenpom_name}'")
    return None


def generate_vs_graphic(away_team, home_team, game_date_str, away_logo_url, home_logo_url, output_path):
    """Generate a VS graphic PNG image."""
    
    # Create base image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Download and resize logos with error handling
    away_logo = None
    home_logo = None
    
    if away_logo_url:
        try:
            away_logo = download_logo(away_logo_url)
        except Exception as e:
            print(f"  ✗ Exception downloading away logo: {e}")
            away_logo = None
    
    if home_logo_url:
        try:
            home_logo = download_logo(home_logo_url)
        except Exception as e:
            print(f"  ✗ Exception downloading home logo: {e}")
            home_logo = None
    
    if away_logo is None:
        print(f"  ⚠ Using placeholder for {away_team} logo")
        away_logo = create_placeholder_logo()
    else:
        away_logo = resize_logo(away_logo)
    
    if home_logo is None:
        print(f"  ⚠ Using placeholder for {home_team} logo")
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
    crosswalk_df = download_csv(CROSSWALK_URL)
    
    print(f"Loaded {len(kp_df)} rows from kp.csv")
    print(f"kp.csv columns: {list(kp_df.columns)}")
    print(f"Loaded {len(logos_df)} logos from logos.csv")
    print(f"logos.csv columns: {list(logos_df.columns)}")
    
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
        
        print(f"\n{'='*60}")
        print(f"Processing: {away_team} @ {home_team} on {game_date}")
        print(f"{'='*60}")
        
        # Step 2-3: Convert team names using crosswalk
        print(f"Converting team names using crosswalk...")
        away_kenpom_name = convert_api_to_kenpom_name(away_team, crosswalk_df)
        home_kenpom_name = convert_api_to_kenpom_name(home_team, crosswalk_df)
        
        # Step 5: Match logos using kenpom names
        try:
            away_logo_url = find_team_logo(away_kenpom_name, logos_df)
        except Exception as e:
            print(f"  ✗ Error matching away team logo: {e}")
            away_logo_url = None
            
        try:
            home_logo_url = find_team_logo(home_kenpom_name, logos_df)
        except Exception as e:
            print(f"  ✗ Error matching home team logo: {e}")
            home_logo_url = None
        
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
            print(f"  ✗ Error generating graphic for {away_team} vs {home_team}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✓ Successfully generated {generated_count} graphics")
    print(f"✓ Output directory: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

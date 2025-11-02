import os
import sys
import pandas as pd
import requests
from datetime import datetime
import pytz
from rich.console import Console
from rich.logging import RichHandler
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")
console = Console()

# Load environment variables
load_dotenv()

def get_championship_odds():
    """
    Fetches championship odds from the OddsAPI using the correct endpoint
    """
    key = os.getenv("ODDS_API_KEY")
    if not key:
        logger.error("[red]✗[/red] ODDSAPI key not found in environment variables.")
        raise ValueError("ODDSAPI key not found in environment variables.")

    base_url = "https://api.the-odds-api.com/v4/sports"
    odds_url = f"{base_url}/basketball_ncaab_championship_winner/odds/?apiKey={key}&regions=us&oddsFormat=american"

    try:
        logger.info("[cyan]Fetching championship odds data...[/cyan]")
        response = requests.get(odds_url)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.error("[red]✗[/red] No odds data returned from API")
            return pd.DataFrame()

        # Process the championship odds data
        odds_records = []
        for bookmaker in data:
            outcomes = bookmaker['bookmakers'][0]['markets'][0]['outcomes']
            for outcome in outcomes:
                odds_records.append({
                    'Team': outcome['name'],
                    'Odds': outcome['price']
                })

        odds_df = pd.DataFrame(odds_records)
        
        # Save to CSV
        odds_df.to_csv('championship_odds.csv', index=False)
        logger.info(f"[green]✓[/green] Successfully saved championship odds for {len(odds_df)} teams")
        
        return odds_df

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"[red]✗[/red] HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        logger.error(f"[red]✗[/red] Error occurred: {err}")
        return None

if __name__ == "__main__":
    logger.info("=== Starting odds data fetch ===")
    
    try:
        # Fetch championship odds
        logger.info("[1/1] Fetching championship odds from The Odds API...")
        championship_odds = get_championship_odds()
        
        if championship_odds is None:
            logger.error("[red]✗[/red] Failed to fetch championship odds")
            sys.exit(1)
            
        logger.info("[green]✓[/green] Successfully completed odds data fetch")
        
    except Exception as e:
        logger.error(f"[red]✗[/red] Error in odds fetch script: {str(e)}")
        sys.exit(1)
        
    logger.info("=== Odds data fetch completed successfully ===")

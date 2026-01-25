#!/usr/bin/env python3
"""
Generate college basketball game matchup preview posts.

This script:
1. Downloads CBB_Output.csv and kp.csv from the trashduty/cbb repository
2. Loads local kenpom_stats.csv
3. Identifies games for the next day
4. Generates markdown preview posts for each game
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import os
import re

# ... (helper functions normalize_team_name, find_team_in_kenpom, etc.)

def main():
    print("Starting game preview generation...")
    
    # URLs for external data
    CBB_OUTPUT_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/CBB_Output.csv"
    KP_URL = "https://raw.githubusercontent.com/trashduty/cbb/main/kp.csv"
    
    # Download external data
    print("Downloading CBB_Output.csv...")
    cbb_output = download_csv(CBB_OUTPUT_URL)
    
    print("Downloading kp.csv...")
    kp_data = download_csv(KP_URL)
    
    # Load local KenPom stats
    print("Loading kenpom_stats.csv...")
    kenpom_stats = pd.read_csv('kenpom_stats.csv')
    
    # Determine target date (next day) relative to Eastern Time
    et_tz = pytz.timezone('US/Eastern')
    today = datetime.now(et_tz)
    target_date = today + timedelta(days=1)
    target_date_str = target_date.strftime('%b %d').replace(' 0', ' ')  # e.g., "Jan 25"
    
    print(f"Looking for games on: {target_date_str} (tomorrow local time)")
    
    # ... rest of the file remains unchanged

def find_team_logo(team_name, logos_df, crosswalk_df):
    """Find team logo URL from logos dataframe using crosswalk for name conversion."""    
    # Step 1: Find the team in crosswalk.csv and get the kenpom name
    kenpom_name = None
    if crosswalk_df is not None and not crosswalk_df.empty:
        # Search for team_name in the 'API' column of crosswalk
        team_name_lower = team_name.strip().lower()
        for _, row in crosswalk_df.iterrows():
            api_name = str(row['API']).strip().lower()
            if api_name == team_name_lower:
                kenpom_name = str(row['kenpom']).strip()
                print(f"  Found '{team_name}' in crosswalk -> kenpom name: '{kenpom_name}'")
                break
    
    # If not found in crosswalk, use original team name
    if not kenpom_name:
        kenpom_name = team_name
        print(f"  '{team_name}' not found in crosswalk, using original name")
    
    # Step 2: Use the kenpom name to search logos.csv in the 'ncaa_name' column
    if 'ncaa_name' in logos_df.columns:
        for _, row in logos_df.iterrows():
            ncaa_name = str(row['ncaa_name']).strip()
            if ncaa_name == kenpom_name:
                logo_url = row['logos']
                print(f"  Found logo for '{kenpom_name}': {logo_url}")
                return logo_url
    
    # If still not found, return placeholder
    print(f"  Warning: No logo found for '{team_name}' (kenpom: '{kenpom_name}')")
    return "https://via.placeholder.com/150"
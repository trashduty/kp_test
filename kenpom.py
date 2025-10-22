def fetch_kenpom_team_stats(output_csv_path="master_kenpom_stats.csv"):
    """
    Fetches all team-level stats from KenPom's main stats page and exports them to a CSV.
    """
    logger = logging.getLogger('kenpom')
    
    # Load environment variables
    load_dotenv()
    USERNAME = os.getenv("KENPOM_USERNAME")
    PASSWORD = os.getenv("KENPOM_PASSWORD")
    
    if not USERNAME or not PASSWORD:
        logger.error("Missing KenPom credentials in environment variables.")
        return None

    # Set up headless browser
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0')

    logger.info("Starting headless Chrome driver")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        logger.info("Navigating to KenPom login")
        driver.get('https://kenpom.com/fanmatch.php')

        email_el = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
        email_el.send_keys(USERNAME)

        pwd_el = driver.find_element(By.NAME, 'password')
        pwd_el.send_keys(PASSWORD)
        pwd_el.send_keys(Keys.RETURN)

        time.sleep(3)

        logger.info("Navigating to stats.php")
        driver.get("https://kenpom.com/stats.php")
        time.sleep(3)

        logger.info("Reading table HTML")
        stats_table = wait.until(EC.presence_of_element_located((By.ID, 'ratings-table')))
        table_html = stats_table.get_attribute('outerHTML')

        df = pd.read_html(table_html)[0]

        # Clean up headers
        df.columns = df.columns.droplevel(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
        df.columns = [col.strip() for col in df.columns]

        # Drop any rows where the Team is NaN or not string
        df = df[df['Team'].apply(lambda x: isinstance(x, str))]

        # Clean rank from team names (e.g., "1. Purdue" → "Purdue")
        df['Team'] = df['Team'].str.replace(r'^\d+\.\s*', '', regex=True)

        logger.info(f"Fetched {len(df)} teams")

        # Save to CSV
        df.to_csv(output_csv_path, index=False)
        logger.info(f"Stats exported to {output_csv_path}")
        return df

    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        return None
    finally:
        driver.quit()
        logger.info("Driver session ended")

name: Scrape Daily Matchups

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    env:
      HEADLESS: "false"
      KENPOM_USERNAME: ${{ secrets.KENPOM_USERNAME }}
      KENPOM_PASSWORD: ${{ secrets.KENPOM_PASSWORD }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Chrome
        uses: browser-actions/setup-chrome@v1
        with:
          chrome-version: stable

      - name: Install Python dependencies
        run: |
          pip install --upgrade pip
          pip install undetected-chromedriver python-dotenv

      - name: Run scraper
        run: python scrape_daily_matchups.py
        continue-on-error: true

      - name: Upload CSV
        uses: actions/upload-artifact@v4
        with:
          name: matchups_csv
          path: daily_matchups.csv
          if-no-files-found: ignore

      - name: Upload screenshot
        uses: actions/upload-artifact@v4
        with:
          name: screenshot
          path: error_screenshot.png
          if-no-files-found: ignore

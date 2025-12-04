import os
from zyte_smart_browser import Browser
from bs4 import BeautifulSoup
import asyncio
import csv
from datetime import datetime, timedelta

# ---------------------------------------
# Helper: Determine date to scrape
# ---------------------------------------
def get_target_date():
    env_date = os.environ.get("SCRAPE_DATE", "").strip()
    if env_date:
        return env_date
    # default = today
    return datetime.now().strftime("%Y-%m-%d")


TARGET_DATE = get_target_date()
URL = f"https://kenpom.com/fanmatch.php?d={TARGET_DATE}"

# ---------------------------------------
# Credentials
# ---------------------------------------
USERNAME = os.environ.get("KENPOM_USERNAME")
PASSWORD = os.environ.get("KENPOM_PASSWORD")
ZYTE_KEY = os.environ.get("ZYTE_API_KEY")  # YOU store this in GitHub secrets


# ---------------------------------------
# Scraper logic
# ---------------------------------------
async def scrape():
    async with Browser(api_key=ZYTE_KEY) as browser:

        # 1) Load login page
        print("🔍 Loading KenPom login...")
        page = await browser.open("https://kenpom.com/login.php")

        # Fill login form
        await page.wait_for_selector('input[name="email"]')
        await page.type('input[name="email"]', USERNAME)
        await page.type('input[name="password"]', PASSWORD)

        print("🔐 Submitting login form...")
        await page.click('input[type="submit"]')

        await page.wait_for_navigation()

        # 2) Navigate to FANMATCH page
        print(f"📊 Navigating to: {URL}")
        page = await browser.open(URL)

        # 3) Extract table HTML
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        table = soup.select_one("table.mytable")
        if not table:
            print("❌ FANMATCH table not found.")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            return

        print("✅ FANMATCH table found. Parsing...")

        # 4) Extract rows
        rows = []
        for tr in table.select("tr"):
            cols = [td.get_text(strip=True) for td in tr.select("td")]
            if cols:
                rows.append(cols)

        # 5) Save CSV
        out_file = "daily_matchups.csv"
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"✅ Saved: {out_file}")


if __name__ == "__main__":
    asyncio.run(scrape())

import os
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from zyte_api.aio.client import AsyncZyteAPIClient
import csv


def get_target_date():
    env_date = os.environ.get("SCRAPE_DATE", "").strip()
    if env_date:
        return env_date
    return datetime.now().strftime("%Y-%m-%d")


TARGET_DATE = get_target_date()
LOGIN_URL = "https://kenpom.com/login.php"
FANMATCH_URL = f"https://kenpom.com/fanmatch.php?d={TARGET_DATE}"

ZYTE_KEY = os.environ.get("ZYTE_API_KEY")
USERNAME = os.environ.get("KENPOM_USERNAME")
PASSWORD = os.environ.get("KENPOM_PASSWORD")


async def scrape():
    async with AsyncZyteAPIClient(api_key=ZYTE_KEY) as client:
        
        # ----------------------------------------------------
        # STEP 1: Load login page (browser mode)
        # ----------------------------------------------------
        print("🔍 Loading login page...")
        login_response = await client.get({
            "url": LOGIN_URL,
            "browserHtml": True,
            "httpResponseBody": True
        })

        page_html = login_response["browserHtml"]

        # ----------------------------------------------------
        # STEP 2: Submit login form
        # ----------------------------------------------------
        print("🔐 Submitting login...")

        login_response = await client.post({
            "url": LOGIN_URL,
            "browserHtml": True,
            "httpResponseBody": True,
            "form": {
                "email": USERNAME,
                "password": PASSWORD
            }
        })

        # ----------------------------------------------------
        # STEP 3: Access FANMATCH now that we're logged in
        # ----------------------------------------------------
        print(f"📊 Loading FANMATCH page for {TARGET_DATE}...")

        fm_response = await client.get({
            "url": FANMATCH_URL,
            "browserHtml": True,
            "httpResponseBody": True,
        })

        html = fm_response["browserHtml"]

        if not html:
            print("❌ FANMATCH returned no HTML. Saving debug file...")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(str(fm_response))
            return

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.mytable")

        if not table:
            print("❌ FANMATCH table not found. Saving debug_html.html...")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            return

        print("✅ Table found. Extracting...")

        rows = []
        for tr in table.select("tr"):
            cols = [td.get_text(strip=True) for td in tr.select("td")]
            if cols:
                rows.append(cols)

        out_file = "daily_matchups.csv"
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"🎉 Saved CSV as: {out_file}")


if __name__ == "__main__":
    asyncio.run(scrape())

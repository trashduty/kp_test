import os
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from zyte_api import AsyncZyteAPI


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

    client = AsyncZyteAPI(api_key=ZYTE_KEY)

    try:
        # STEP 1 — Load login page
        print("🔍 Loading login page...")
        await client.request_raw({
            "url": LOGIN_URL,
            "browserHtml": True
        })

        # STEP 2 — Submit login form
        print("🔐 Submitting login form...")

        login_result = await client.request_raw({
            "url": LOGIN_URL,
            "httpMethod": "POST",
            "browserHtml": True,
            "form": {
                "email": USERNAME,
                "password": PASSWORD
            }
        })

        # STEP 3 — Load FANMATCH page after login
        print(f"📊 Loading FANMATCH for {TARGET_DATE}...")
        fm_result = await client.request_raw({
            "url": FANMATCH_URL,
            "browserHtml": True,
        })

        html = fm_result.get("browserHtml")

        if not html:
            print("❌ No HTML received — saving debug.")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(str(fm_result))
            return

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.mytable")

        if not table:
            print("❌ Could not find table — saving HTML.")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            return

        print("✅ Extracting rows...")

        rows = []
        for tr in table.select("tr"):
            cols = [td.get_text(strip=True) for td in tr.select("td")]
            if cols:
                rows.append(cols)

        out_file = "daily_matchups.csv"
        import csv
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"🎉 SUCCESS — Saved {len(rows)} rows to {out_file}")

    finally:
        # VERY IMPORTANT: close client (since no asy

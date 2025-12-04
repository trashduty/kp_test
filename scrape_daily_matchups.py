import os
from zyte_api import ZyteAPIClient
from bs4 import BeautifulSoup
import csv
from datetime import datetime

# -------------------------
# Determine scrape date
# -------------------------
def get_target_date():
    env_date = os.environ.get("SCRAPE_DATE", "").strip()
    if env_date:
        return env_date
    return datetime.now().strftime("%Y-%m-%d")

TARGET_DATE = get_target_date()
URL = f"https://kenpom.com/fanmatch.php?d={TARGET_DATE}"

# -------------------------
# Zyte API Key
# -------------------------
ZYTE_KEY = os.environ.get("ZYTE_API_KEY")
USERNAME = os.environ.get("KENPOM_USERNAME")
PASSWORD = os.environ.get("KENPOM_PASSWORD")


async def scrape():
    print("📡 Requesting page through Zyte API...")
    async with ZyteAPIClient(api_key=ZYTE_KEY) as client:

        # Tell Zyte API to return the fully rendered HTML
        response = await client.get(
            {
                "url": URL,
                "render": True,        # <-- CRITICAL! Enables JS + Cloudflare solving
                "httpResponseBody": True,
                "browserHtml": True,
            }
        )

        html = response["browserHtml"]
        if not html:
            print("❌ Error: No HTML returned.")
            return

        print("✅ HTML received from Zyte. Parsing...")

        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.mytable")

        if not table:
            print("❌ FANMATCH table not found. Saving debug_html.html...")
            with open("debug_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            return

        print("✅ FANMATCH table found. Extracting data...")

        rows = []
        for tr in table.select("tr"):
            cols = [td.get_text(strip=True) for td in tr.select("td")]
            if cols:
                rows.append(cols)

        # Save to CSV
        out_file = "daily_matchups.csv"
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Column1","Column2","Column3","..."])
            writer.writerows(rows)

        print(f"🎉 Saved CSV: {out_file}")


# Required for async runner inside GitHub
import asyncio
if __name__ == "__main__":
    asyncio.run(scrape())

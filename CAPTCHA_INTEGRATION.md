# ⚠️ DEPRECATED - 2captcha Integration Documentation

**This documentation is deprecated as of December 2024.** The KenPom scraping approach has been replaced with direct API access, which eliminates the need for web scraping, Selenium, and CAPTCHA solving.

## New Approach: KenPom API

The `scrape_daily_matchups.py` script now uses the official KenPom Fanmatch API instead of web scraping. This provides:
- ✅ No web scraping needed
- ✅ No Selenium/ChromeDriver dependencies
- ✅ No CAPTCHA challenges to solve
- ✅ Faster and more reliable data fetching
- ✅ Official data source

### Setup for API Access

1. **Get a KenPom API key**:
   - Access the KenPom API through your subscription
   - Contact KenPom support if you need API access

2. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Add your API key:
     ```bash
     KENPOM_API_KEY=your_api_key_here
     ```

3. **For GitHub Actions**:
   - Add `KENPOM_API_KEY` as a repository secret
   - The workflow is automatically configured to use it

---

## Historical Information (Archived)

The content below describes the old web scraping approach and is kept for reference only.



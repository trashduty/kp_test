# 2captcha Integration Documentation

## Overview

The KenPom scraping scripts now include automatic CAPTCHA detection and solving capabilities using the [2captcha](https://2captcha.com) service. This helps bypass bot detection and CAPTCHA challenges that may prevent successful data collection.

## What's New

### CAPTCHA Solver Module

A new `captcha_solver.py` module provides:
- **Multi-CAPTCHA Support**: Handles reCAPTCHA v2, hCaptcha, and Cloudflare Turnstile
- **Auto-Detection**: Automatically identifies which CAPTCHA type is present
- **Graceful Degradation**: Works without API key (detection only) and doesn't break if CAPTCHAs aren't present
- **Clear Logging**: Provides informative feedback during the solving process

### Updated Scripts

All KenPom scraping scripts have been updated:
- `scrape_kenpom_stats.py`
- `scrape_fanmatch.py`
- `scrape_ap_rankings.py`
- `scrape_daily_matchups.py`

Each script now:
- Loads the `TWOCAPTCHA_API_KEY` from environment variables
- Checks for CAPTCHAs at key points (page load, login, data scraping)
- Uses a realistic user agent to avoid detection
- Takes screenshots on error for debugging

## Setup Instructions

### For Local Development

1. **Get a 2captcha API key** (optional but recommended):
   - Sign up at [https://2captcha.com](https://2captcha.com)
   - Add funds to your account
   - Copy your API key from the dashboard

2. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Add your credentials:
     ```bash
     KENPOM_USERNAME=your_email@example.com
     KENPOM_PASSWORD=your_password
     TWOCAPTCHA_API_KEY=your_2captcha_api_key
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the scripts**:
   ```bash
   python scrape_kenpom_stats.py
   ```

### For GitHub Actions

Add the `TWOCAPTCHA_API_KEY` as a repository secret:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `TWOCAPTCHA_API_KEY`
5. Value: Your 2captcha API key
6. Click **Add secret**

The GitHub Actions workflows (`kenpom-stats.yml` and `daily-plots.yml`) are already configured to use this secret.

## How It Works

### CAPTCHA Detection

The `CaptchaSolver` class automatically detects CAPTCHAs by:
1. Looking for specific HTML elements (e.g., `g-recaptcha`, `h-captcha`, `cf-turnstile`)
2. Checking for CAPTCHA iframes
3. Extracting the site key required for solving

### CAPTCHA Solving

When a CAPTCHA is detected:
1. The site key and URL are sent to 2captcha's API
2. 2captcha workers solve the CAPTCHA (typically takes 10-30 seconds)
3. The solution token is injected back into the page
4. The script waits 2 seconds to appear human-like
5. Scraping continues normally

### Graceful Fallback

If no API key is provided:
- Scripts will still check for CAPTCHAs
- They'll log warnings if CAPTCHAs are detected
- They'll continue attempting to scrape (may fail if CAPTCHA is required)

## Cost Considerations

2captcha pricing (as of 2024):
- reCAPTCHA v2: ~$1.00 per 1000 solves
- hCaptcha: ~$1.00 per 1000 solves
- Cloudflare Turnstile: ~$1.00 per 1000 solves

For typical daily scraping runs (4 scripts × 3 CAPTCHA checks = 12 checks per day):
- Even if all checks encounter CAPTCHAs (unlikely), cost would be < $0.50/month
- In practice, CAPTCHAs may appear rarely, resulting in much lower costs

## Troubleshooting

### "No API key provided" message
This is normal if you haven't set the `TWOCAPTCHA_API_KEY` environment variable. The scripts will still work if CAPTCHAs aren't present.

### "CAPTCHA detected but cannot solve"
This means a CAPTCHA is blocking the page and you need to add your API key to bypass it.

### "Failed to solve CAPTCHA"
Possible causes:
- Insufficient balance in 2captcha account
- Network issues with 2captcha API
- Incorrect API key
- CAPTCHA type not supported (rare)

Check the detailed error message in the logs for more information.

### Scripts fail even with API key
- Verify your API key is correct
- Check your 2captcha account balance
- Review error screenshots saved in the repository root
- Check GitHub Actions artifacts for debug information

## Additional Resources

- [2captcha Documentation](https://2captcha.com/2captcha-api)
- [2captcha Python Library](https://github.com/2captcha/2captcha-python)
- [KenPom Website](https://kenpom.com)

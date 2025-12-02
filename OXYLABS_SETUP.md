# Oxylabs Proxy Setup

This repository uses Oxylabs residential proxies with **selenium-wire** to bypass Cloudflare bot detection.

## What is Selenium-Wire?

Selenium-wire is an extension of Selenium that intercepts network requests and handles proxy authentication automatically. This is necessary because Chrome doesn't natively support authenticated proxies via command-line arguments.

## Installation

Selenium-wire is already included in `requirements.txt`. If installing manually:

```bash
pip install selenium-wire
```

## GitHub Actions Setup

Add these secrets to your repository (Settings → Secrets and variables → Actions → New repository secret):

1. **PROXY_USE_SELENIUM_WIRE**: `true`
2. **OXY_USERNAME**: `your_oxylabs_username`
3. **OXY_PASSWORD**: `your_oxylabs_password`
4. **OXY_HOST**: `pr.oxylabs.io` (optional, defaults to this)
5. **OXY_PORT**: `7777` (optional, defaults to this)
6. **OXY_STICKY**: `github-actions-1` (recommended for sticky sessions)

## Local Setup

For local testing, add these to your `.env` file:

```env
PROXY_USE_SELENIUM_WIRE=true
OXY_USERNAME=your_oxylabs_username
OXY_PASSWORD=your_oxylabs_password
OXY_HOST=pr.oxylabs.io
OXY_PORT=7777
OXY_STICKY=sticky1
```

## Sticky Sessions

**What are sticky sessions?**
Sticky sessions maintain the same IP address throughout your scraping session. This is critical for bypassing Cloudflare, which detects and blocks IP changes during login.

**How to use:**
Set the `OXY_STICKY` environment variable to any unique string:
```env
OXY_STICKY=sticky1
```

The scraper will use `username-session-{OXY_STICKY}` when connecting to Oxylabs.

**Example:**
If your username is `customer-user123` and `OXY_STICKY=sticky1`, the proxy connection will use:
```
customer-user123-session-sticky1
```

## Testing the Proxy

### Test with diagnostic tool
```bash
python tools/check_proxy.py
```

This will:
- ✅ Test proxy connection with `requests` library
- ✅ Test proxy connection with `selenium-wire`
- ✅ Display your IP address (should be Oxylabs residential IP)
- ✅ Show headers to verify they look realistic

### Test Oxylabs Connection (curl)
```bash
curl -x pr.oxylabs.io:7777 -U "your_oxylabs_username:your_oxylabs_password" https://ip.oxylabs.io/location
```

You should see a JSON response with location information.

### Test with sticky session (curl)
```bash
curl -x pr.oxylabs.io:7777 -U "your_oxylabs_username-session-sticky1:your_oxylabs_password" https://ip.oxylabs.io/location
```

Run this multiple times - the IP address should remain the same.

## How It Works

1. **Selenium-wire intercepts all Chrome network traffic**
2. **Routes it through Oxylabs proxy** (`pr.oxylabs.io:7777`)
3. **Automatically adds authentication** (username/password)
4. **Oxylabs routes you through residential IPs** (rotating US IPs, or sticky if configured)
5. **KenPom sees "normal home user"** instead of "GitHub datacenter"
6. **No more Cloudflare blocks!** 🎉

## Sticky Session Benefits

- **Same IP throughout session**: Login and scraping use the same IP
- **No Cloudflare warnings**: Cloudflare won't flag IP changes as suspicious
- **Better success rate**: Reduces bot detection risk
- **Recommended for all production use**

## Disabling the Proxy

To run without proxy (for local testing where Cloudflare doesn't block):

Set `PROXY_USE_SELENIUM_WIRE=false` in your `.env` file or GitHub secret.

## Troubleshooting

### "No module named 'blinker._saferef'" Error

This is a dependency conflict. Fix by installing the correct versions:

```bash
pip uninstall blinker selenium-wire -y
pip install blinker==1.7.0
pip install selenium-wire==5.1.0
```

The issue occurs because:
- Selenium-wire requires `blinker` with `_saferef` module
- Blinker 2.x removed `_saferef`
- We pin to blinker 1.7.0 which still has it

### Other dependency issues

If you still have problems:

```bash
# Clean install all dependencies
pip uninstall selenium selenium-wire blinker undetected-chromedriver -y
pip install --no-cache-dir -r requirements.txt
```

### Proxy authentication failed
- Verify your Oxylabs credentials are correct
- Check if your Oxylabs subscription is active
- Log into Oxylabs dashboard to verify account status: https://dashboard.oxylabs.io/
- Ensure you haven't exceeded your bandwidth limit

### Still getting Cloudflare blocks
- Verify `PROXY_USE_SELENIUM_WIRE=true` is set
- Ensure sticky session is configured: `OXY_STICKY=sticky1`
- Run `python tools/check_proxy.py` to verify proxy is working
- Check proxy logs for "Using sticky session: {id}"
- Try adding longer delays between requests
- Contact Oxylabs support if issues persist

### Diagnostic tool fails
```bash
python tools/check_proxy.py
```
Should show your proxy IP and headers. If it fails:
- Verify internet connectivity
- Check proxy credentials
- Try curl test command first

### Proxy works locally but not in GitHub Actions
- Verify all secrets are added to GitHub Actions
- Check the Actions logs for proxy connection errors
- Ensure secrets are spelled exactly as shown above: `OXY_USERNAME`, `OXY_PASSWORD`, etc.
- Check Oxylabs dashboard for connection attempts

### "Cannot connect to proxy" error
- Verify `pr.oxylabs.io:7777` is reachable
- Check if port 7777 is blocked by firewall
- Try testing with curl command first

### IP rotates between requests (no sticky session)
- Make sure `OXY_STICKY` environment variable is set
- Check logs for "Using sticky session" message
- Verify username format: `username-session-{STICKY_ID}`

## Monitoring Usage

- Log into your Oxylabs dashboard: https://dashboard.oxylabs.io/
- View bandwidth usage, connection logs, and IP rotation
- Each scrape session uses approximately 1-2 MB
- Running daily should use < 100 MB/month

## Support

If you encounter issues:
1. Check the GitHub Actions logs for specific error messages
2. Test the curl command to verify Oxylabs credentials work
3. Run scrapers locally with proxy enabled to isolate the issue
4. Contact Oxylabs support if proxy connection fails

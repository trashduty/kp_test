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

1. **PROXY_ENABLED**: `true`
2. **PROXY_SERVER**: `pr.oxylabs.io:7777`
3. **PROXY_USERNAME**: `customer-bullytheboard_OnFjP-cc-US`
4. **PROXY_PASSWORD**: `Btb_analytics1`

## Local Setup

For local testing, add these to your `.env` file:

```env
PROXY_ENABLED=true
PROXY_SERVER=pr.oxylabs.io:7777
PROXY_USERNAME=customer-bullytheboard_OnFjP-cc-US
PROXY_PASSWORD=Btb_analytics1
```

## Testing the Proxy

### Test Oxylabs Connection
```bash
curl -x pr.oxylabs.io:7777 -U "customer-bullytheboard_OnFjP-cc-US:Btb_analytics1" https://ip.oxylabs.io/location
```

You should see a JSON response with location information.

### Test in Python
Run a scraper locally with `PROXY_ENABLED=true` in your `.env` file. You should see:
```
✅ Proxy enabled: Using Oxylabs (pr.oxylabs.io:7777)
✅ Successfully initialized Chrome
```

## How It Works

1. **Selenium-wire intercepts all Chrome network traffic**
2. **Routes it through Oxylabs proxy** (`pr.oxylabs.io:7777`)
3. **Automatically adds authentication** (username/password)
4. **Oxylabs routes you through residential IPs** (rotating US IPs)
5. **KenPom sees "normal home user"** instead of "GitHub datacenter"
6. **No more Cloudflare blocks!** 🎉

## Disabling the Proxy

To run without proxy (for local testing where Cloudflare doesn't block):

Set `PROXY_ENABLED=false` in your `.env` file or GitHub secret.

## Troubleshooting

### ERR_NO_SUPPORTED_PROXIES (OLD ERROR - NOW FIXED)
This was caused by trying to use Chrome's `--proxy-server` argument with authentication. Now fixed with selenium-wire.

### Proxy authentication failed
- Verify your Oxylabs credentials are correct
- Check if your Oxylabs subscription is active
- Log into Oxylabs dashboard to verify account status
- Ensure you haven't exceeded your bandwidth limit

### Still getting Cloudflare blocks
- Oxylabs residential proxies should bypass most blocks
- Verify proxy is actually being used (check logs for "✅ Proxy enabled")
- Try adding longer delays between requests
- Contact Oxylabs support if issues persist

### Selenium-wire installation issues
```bash
pip install --upgrade selenium-wire
```

### Proxy works locally but not in GitHub Actions
- Verify all 4 secrets are added to GitHub Actions
- Check the Actions logs for proxy connection errors
- Ensure secrets are spelled exactly as shown above
- Check Oxylabs dashboard for connection attempts

### "Cannot connect to proxy" error
- Verify `pr.oxylabs.io:7777` is reachable
- Check if port 7777 is blocked by firewall
- Try testing with curl command first

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

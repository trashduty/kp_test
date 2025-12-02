# Oxylabs Proxy Setup

This repository uses Oxylabs residential proxies to bypass Cloudflare bot detection.

## GitHub Actions Setup

Add these secrets to your repository (Settings → Secrets and variables → Actions → New repository secret):

1. **PROXY_ENABLED**: `true`
2. **PROXY_SERVER**: `pr.oxylabs.io:7777`
3. **PROXY_USERNAME**: `your_oxylabs_username`
4. **PROXY_PASSWORD**: `your_oxylabs_password`

## Local Setup

For local testing, add these to your `.env` file:

```env
PROXY_ENABLED=true
PROXY_SERVER=pr.oxylabs.io:7777
PROXY_USERNAME=your_oxylabs_username
PROXY_PASSWORD=your_oxylabs_password
```

## Testing the Proxy

Test your Oxylabs connection with:

```bash
curl -x pr.oxylabs.io:7777 -U "your_oxylabs_username:your_oxylabs_password" https://ip.oxylabs.io/location
```

You should see a JSON response with location information, confirming the proxy works.

## Disabling the Proxy

To run without proxy (for local testing where Cloudflare doesn't block):

Set `PROXY_ENABLED=false` in your `.env` file or GitHub secret.

## Troubleshooting

### Proxy authentication failed
- Verify your credentials are correct
- Check if your Oxylabs subscription is active
- Ensure you haven't exceeded your bandwidth limit

### Still getting Cloudflare blocks
- Oxylabs residential proxies should bypass most blocks
- Try adding delays between requests
- Contact Oxylabs support if issues persist

### Proxy works locally but not in GitHub Actions
- Verify all 4 secrets are added to GitHub Actions
- Check the Actions logs for proxy connection errors
- Ensure secrets are spelled exactly as shown above

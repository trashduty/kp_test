# KenPom Efficiency Plots - GitHub Pages Setup

This repository hosts KenPom college basketball efficiency plots that are automatically updated daily via GitHub Actions.

## 📊 View the Plots

Visit the live GitHub Pages site: **https://trashduty.github.io/kp_test/**

## 🚀 GitHub Pages Setup Instructions

To enable GitHub Pages for this repository:

1. Go to your repository on GitHub
2. Click on **Settings** (⚙️)
3. In the left sidebar, click on **Pages**
4. Under **Source**, select:
   - **Branch**: `main` (or your default branch)
   - **Folder**: `/docs`
5. Click **Save**
6. GitHub Pages will be enabled and your site will be published at: `https://[username].github.io/[repository]/`

## 📁 Directory Structure

```
docs/
├── index.html          # Main page displaying all plots
├── css/
│   └── style.css       # Styling for the page
└── plots/              # Plot images (automatically updated)
    ├── kenpom_top100_eff.png
    ├── kenpom_ap25_eff.png
    ├── march_madness_championship_odds.png
    └── conferences/
        ├── kenpom_acc_eff.png
        ├── kenpom_b10_eff.png
        └── ... (all conference plots)
```

## 🔄 Automatic Updates

The plots are automatically updated daily via GitHub Actions:

### KenPom Plots (6:00 AM UTC)
1. Scrapes KenPom statistics
2. Scrapes AP Top 25 rankings
3. Generates efficiency plots using R
4. Commits and pushes the changes

### March Madness Championship Odds (12:00 PM UTC)
1. Scrapes KenPom statistics
2. Fetches championship odds from The Odds API
3. Generates March Madness contenders plot with odds overlay
4. Commits and pushes the updated plot

## 🔗 Embedding Plots

You can embed these plots on external websites:

### Top 100 Plot
```html
<img src="https://trashduty.github.io/kp_test/plots/kenpom_top100_eff.png" 
     alt="KenPom Top 100 Efficiency Plot" 
     style="max-width: 100%; height: auto;">
```

### AP Top 25 Plot
```html
<img src="https://trashduty.github.io/kp_test/plots/kenpom_ap25_eff.png" 
     alt="AP Top 25 Efficiency Plot" 
     style="max-width: 100%; height: auto;">
```

### March Madness Championship Odds Plot
```html
<img src="https://trashduty.github.io/kp_test/plots/march_madness_championship_odds.png" 
     alt="March Madness Championship Odds" 
     style="max-width: 100%; height: auto;">
```

### Conference Plots
```html
<!-- Replace [CONF] with conference code (acc, b10, b12, etc.) -->
<img src="https://trashduty.github.io/kp_test/plots/conferences/kenpom_[CONF]_eff.png" 
     alt="Conference Efficiency Plot" 
     style="max-width: 100%; height: auto;">
```

### Available Conference Codes
`acc`, `b10`, `b12`, `be`, `sec`, `a10`, `amer`, `mwc`, `wcc`, `asun`, `ae`, `bsky`, `bsth`, `bw`, `caa`, `cusa`, `horz`, `ivy`, `maac`, `mac`, `meac`, `mvc`, `nec`, `ovc`, `pl`, `sc`, `slnd`, `sum`, `sb`, `swac`, `wac`

## 📝 Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Auto-updating**: Plots refresh daily without manual intervention
- **Clean Layout**: Organized by Top 100, AP Top 25, March Madness, and Conference sections
- **Easy Embedding**: Simple URLs for external use
- **Lazy Loading**: Images load efficiently for better performance
- **Championship Odds**: Integrated odds data from The Odds API for March Madness contenders

## 🛠️ Customization

To customize the appearance:

1. Edit `docs/css/style.css` for styling changes
2. Edit `docs/index.html` to modify layout or add/remove sections
3. Commit and push changes - GitHub Pages will automatically rebuild

## 📊 Data Sources

- **Efficiency Metrics**: [KenPom.com](https://kenpom.com) - the leading college basketball analytics site
- **Championship Odds**: [The Odds API](https://the-odds-api.com) - real-time sports betting odds
- **AP Rankings**: [ESPN](https://www.espn.com/mens-college-basketball/rankings) - AP Top 25 polls

## 📄 License

The plots and code are available for personal and educational use. Please credit KenPom.com as the data source when using the plots.

---

## 🔐 Proxy Configuration (Oxylabs)

To bypass Cloudflare bot detection, this repository supports Oxylabs residential proxies with sticky sessions.

### Environment Variables

Add these to your `.env` file or GitHub Actions secrets:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PROXY_USE_SELENIUM_WIRE` | No | Enable selenium-wire proxy | `true` or `false` |
| `OXY_USERNAME` | Yes* | Oxylabs username | `customer-user123` |
| `OXY_PASSWORD` | Yes* | Oxylabs password | `your_password` |
| `OXY_HOST` | No | Oxylabs proxy host | `pr.oxylabs.io` (default) |
| `OXY_PORT` | No | Oxylabs proxy port | `7777` (default) |
| `OXY_STICKY` | No | Sticky session ID | `sticky1` or `session123` |

*Required only if `PROXY_USE_SELENIUM_WIRE=true`

### Sticky Sessions

Oxylabs sticky sessions maintain the same IP address throughout your scraping session. This is critical for bypassing Cloudflare, which may flag IP changes during login.

**How to use:**
1. Set `OXY_STICKY` to any unique string (e.g., `sticky1`, `session123`)
2. The scraper will use `username-session-{OXY_STICKY}` when connecting
3. All requests will route through the same residential IP

**Example:**
```env
PROXY_USE_SELENIUM_WIRE=true
OXY_USERNAME=customer-user123
OXY_PASSWORD=your_password
OXY_STICKY=sticky1
```

This creates the proxy username: `customer-user123-session-sticky1`

### Testing Your Proxy Setup

Run the diagnostic tool to verify your proxy configuration:

```bash
python tools/check_proxy.py
```

This will:
- ✅ Test proxy connection with `requests` library
- ✅ Test proxy connection with `selenium-wire`
- ✅ Display your IP address (should be Oxylabs residential IP)
- ✅ Show headers to verify they look realistic

### GitHub Actions Setup

Add these secrets to your repository (Settings → Secrets → Actions):

1. `PROXY_USE_SELENIUM_WIRE`: `true`
2. `OXY_USERNAME`: Your Oxylabs username
3. `OXY_PASSWORD`: Your Oxylabs password
4. `OXY_STICKY`: A unique session identifier (e.g., `github-actions-1`)

The workflow will automatically use these for proxy authentication.

### Troubleshooting

**"Cloudflare Turnstile challenge appears"**
- Verify `PROXY_USE_SELENIUM_WIRE=true` is set
- Ensure sticky session is enabled (`OXY_STICKY` is set)
- Run `tools/check_proxy.py` to verify proxy is working
- Check that your IP in the diagnostic matches Oxylabs residential pool

**"Proxy authentication failed"**
- Verify credentials in Oxylabs dashboard: https://dashboard.oxylabs.io/
- Check if subscription is active and has bandwidth remaining
- Test with curl: `curl -x pr.oxylabs.io:7777 -U "user:pass" https://httpbin.org/ip`

**"IP rotates between requests"**
- Make sure `OXY_STICKY` is set to maintain the same IP
- Verify the session ID appears in the logs: "Using sticky session: {id}"

**"Still getting blocked by Cloudflare"**
- Consider integrating a Turnstile solver (see comments in code)
- Add longer delays between requests
- Contact Oxylabs support for residential IP quality issues

### Turnstile Solver Integration (Optional)

If Cloudflare Turnstile challenges persist even with a proxy, you can integrate a solving service:

**Supported services:**
- [2Captcha](https://2captcha.com/2captcha-api#turnstile)
- [Anti-Captcha](https://anti-captcha.com/apidoc/task-types/TurnstileTask)
- [CapSolver](https://www.capsolver.com/products/cloudflare-turnstile)

**Setup:**
1. Get an API key from your chosen service
2. Add to `.env`: `TURNSTILE_SOLVER_API_KEY=your_key_here`
3. See comments in `scrape_kenpom_stats.py` for integration points

⚠️ **Never commit API keys to the repository!** Always use environment variables.

### Additional Resources

- [Oxylabs Documentation](https://developers.oxylabs.io/scraper-apis/residential-proxies)
- [Selenium-Wire Documentation](https://github.com/wkeeling/selenium-wire)
- See `OXYLABS_SETUP.md` for detailed proxy setup instructions

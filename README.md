# KenPom Efficiency Plots - GitHub Pages Setup

This repository hosts KenPom college basketball efficiency plots that are automatically updated daily via GitHub Actions, plus an interactive online odds calculator for betting analysis.

## 📊 View the Plots

Visit the live GitHub Pages site: **https://trashduty.github.io/kp_test/**

## 🎯 Online Odds Calculator

Calculate cover probability and betting edge: **https://trashduty.github.io/kp_test/odds-calculator.html**

The odds calculator enables users to:
- Input market line, model prediction, and betting odds
- Calculate cover probability based on historical spread data
- Compute implied probability from American odds (positive or negative)
- Determine betting edge (cover probability minus implied probability)

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
├── index.html                      # Main page displaying all plots
├── odds-calculator.html            # Interactive odds calculator
├── spreads_lookup_combined.json    # Spread probability data (27MB)
├── css/
│   └── style.css                   # Styling for the page
└── plots/                          # Plot images (automatically updated)
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

## 🔗 Embedding Content

You can embed plots and the odds calculator on external websites:

### Odds Calculator
```html
<iframe src="https://trashduty.github.io/kp_test/odds-calculator.html" 
        width="100%" 
        height="700px" 
        frameborder="0"
        style="max-width: 650px; margin: 0 auto; display: block;">
</iframe>
```

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

### Efficiency Plots
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Auto-updating**: Plots refresh daily without manual intervention
- **Clean Layout**: Organized by Top 100, AP Top 25, March Madness, and Conference sections
- **Easy Embedding**: Simple URLs for external use
- **Lazy Loading**: Images load efficiently for better performance
- **Championship Odds**: Integrated odds data from The Odds API for March Madness contenders

### Odds Calculator
- **Client-side Processing**: Fully browser-based, no backend required
- **Real-time Calculations**: Instant results as you input values
- **Comprehensive Data**: 174,000+ probability records from historical spread data
- **American Odds Support**: Handles both negative and positive odds formats
- **Edge Detection**: Automatically calculates betting edge to identify value bets

## 🎲 How the Odds Calculator Works

1. **User Input**: Enter the market line, model prediction, and betting odds
2. **Data Lookup**: Fetches matching probability from `spreads_lookup_combined.json` (174,243 records)
3. **Implied Probability**: Calculates from American odds
   - Negative odds: `|odds| / (|odds| + 100)` (e.g., -110 → 52.38%)
   - Positive odds: `100 / (odds + 100)` (e.g., +200 → 33.33%)
4. **Edge Calculation**: `cover_prob - implied_probability`
   - Positive edge suggests value bet
   - Negative edge suggests bet against

### Example
Input: Market Line: -60, Prediction: -60, Odds: -110
- Cover Probability: 50.00%
- Implied Probability: 52.38%
- Edge: -2.38% (suggests avoiding this bet)

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


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
    └── conferences/
        ├── kenpom_acc_eff.png
        ├── kenpom_b10_eff.png
        └── ... (all conference plots)
```

## 🔄 Automatic Updates

The plots are automatically updated daily at 6:00 AM UTC via GitHub Actions:

1. The workflow scrapes KenPom statistics
2. Generates new plots using R
3. Copies plots to both `plots/` and `docs/plots/` directories
4. Commits and pushes the changes to the repository
5. GitHub Pages automatically rebuilds and serves the updated plots

## 🔗 Embedding Plots

You can embed these plots on external websites:

### HTML
```html
<img src="https://trashduty.github.io/kp_test/plots/kenpom_top100_eff.png" 
     alt="KenPom Top 100 Efficiency Plot" 
     style="max-width: 100%; height: auto;">
```

### Markdown
```markdown
![KenPom Top 100](https://trashduty.github.io/kp_test/plots/kenpom_top100_eff.png)
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
- **Clean Layout**: Organized by Top 100 and Conference sections
- **Easy Embedding**: Simple URLs for external use
- **Lazy Loading**: Images load efficiently for better performance

## 🛠️ Customization

To customize the appearance:

1. Edit `docs/css/style.css` for styling changes
2. Edit `docs/index.html` to modify layout or add/remove sections
3. Commit and push changes - GitHub Pages will automatically rebuild

## 📊 Data Source

All data is sourced from [KenPom.com](https://kenpom.com), the leading college basketball analytics site.

## 📄 License

The plots and code are available for personal and educational use. Please credit KenPom.com as the data source when using the plots.

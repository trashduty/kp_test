import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import os

# Load datasets
eff_stats = pd.read_csv("kenpom_stats.csv")
teams = pd.read_csv("ncaa_teams_colors_logos_CBB.csv").drop_duplicates(subset='current_team')

# Select top 100 teams and merge with logos
eff_stats = eff_stats.iloc[0:100].copy()
eff_stats = eff_stats.merge(teams, how='left', left_on='Team', right_on='current_team')
eff_stats["NetEfficiency"] = eff_stats["ORtg"] - eff_stats["DRtg"]

# Calculate means
mean_ortg = eff_stats["ORtg"].mean()
mean_drtg = eff_stats["DRtg"].mean()

# Create plot
fig, ax = plt.subplots(figsize=(14, 10))

# Shaded quadrants
ax.axhspan(
    eff_stats["DRtg"].min(), mean_drtg,
    xmin=(mean_ortg - eff_stats["ORtg"].min()) / (eff_stats["ORtg"].max() - eff_stats["ORtg"].min()),
    xmax=1, alpha=0.1, color='green'
)
ax.axhspan(
    mean_drtg, eff_stats["DRtg"].max(),
    xmin=0, xmax=(mean_ortg - eff_stats["ORtg"].min()) / (eff_stats["ORtg"].max() - eff_stats["ORtg"].min()),
    alpha=0.1, color='red'
)

# Dashed mean lines
ax.axhline(mean_drtg, linestyle='dashed', color='gray')
ax.axvline(mean_ortg, linestyle='dashed', color='gray')

# Add logos (or fallback team name)
def add_logo(x, y, path, ax, zoom=0.05):
    try:
        img = Image.open(path)
        im = OffsetImage(img, zoom=zoom)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)
    except:
        print(f"⚠️ Could not load logo for: {path}")

for _, row in eff_stats.iterrows():
    if pd.notna(row.get("logo")) and os.path.exists(row["logo"]):
        add_logo(row["ORtg"], row["DRtg"], row["logo"], ax)
    else:
        ax.text(row["ORtg"], row["DRtg"], row["Team"], fontsize=6, ha='center', va='center')

# Labels & aesthetics
ax.set_xlabel("Offensive Rating (ORtg)", fontsize=16)
ax.set_ylabel("Defensive Rating (DRtg)", fontsize=16)
ax.set_title("Men's CBB Landscape | Top 100 Teams", fontsize=22, weight='bold')
ax.invert_yaxis()
ax.grid(True)

plt.tight_layout()
plt.savefig("kenpom_top100_eff.png", dpi=300)
plt.close()
print("✅ Plot saved as kenpom_top100_eff.png")

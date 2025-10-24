
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import requests
from io import BytesIO

# Load datasets
eff_stats = pd.read_csv("kenpom_stats.csv")
teams = pd.read_csv("ncaa_teams_colors_logos_CBB.csv").drop_duplicates(subset='current_team')

# Replace AdjOE/AdjDE with ORtg/DRtg
eff_stats = eff_stats.rename(columns={"AdjOE": "ORtg", "AdjDE": "DRtg"})

# Join top 100 teams with logos
eff_stats = eff_stats.iloc[0:100].copy()
eff_stats = eff_stats.merge(teams, how='left', left_on='Team', right_on='current_team')
eff_stats["NetEfficiency"] = eff_stats["ORtg"] - eff_stats["DRtg"]

# Calculate means
mean_ortg = eff_stats["ORtg"].mean()
mean_drtg = eff_stats["DRtg"].mean()

# Create plot
fig, ax = plt.subplots(figsize=(14, 10))

# Quadrant shading
ax.axvspan(mean_ortg, eff_stats["ORtg"].max(), eff_stats["DRtg"].min(), mean_drtg, alpha=0.1, color='green')
ax.axvspan(eff_stats["ORtg"].min(), mean_ortg, mean_drtg, eff_stats["DRtg"].max(), alpha=0.1, color='red')

# Dashed mean lines
ax.axhline(mean_drtg, linestyle='dashed', color='gray')
ax.axvline(mean_ortg, linestyle='dashed', color='gray')

# Add logos from URL or fallback to text
def add_logo(x, y, url, ax, zoom=0.05):
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        im = OffsetImage(img, zoom=zoom)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)
    except Exception as e:
        print(f"⚠️ Could not load logo for: {url} — {e}")

for _, row in eff_stats.iterrows():
    if pd.notna(row.get("logo")):
        add_logo(row["ORtg"], row["DRtg"], row["logo"], ax)
    else:
        ax.text(row["ORtg"], row["DRtg"], row["Team"], fontsize=6, ha='center', va='center')

# Labels and styling
ax.set_xlabel("Offensive Rating (ORtg)", fontsize=16)
ax.set_ylabel("Defensive Rating (DRtg)", fontsize=16)
ax.set_title("Men's CBB Landscape | Top 100 Teams", fontsize=22, weight='bold')
ax.invert_yaxis()
ax.grid(True)

plt.tight_layout()
plt.savefig("kenpom_top100_eff.png", dpi=300)
plt.close()
print("✅ Plot saved as kenpom_top100_eff.png")

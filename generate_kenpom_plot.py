import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import os

# Load datasets
eff_stats = pd.read_csv("kenpom_stats.csv")
teams = pd.read_csv("ncaa_teams_colors_logos_CBB.csv").drop_duplicates(subset='current_team')

# Join top 100 teams with logos
eff_stats = eff_stats.iloc[0:100].copy()
eff_stats = eff_stats.merge(teams, how='left', left_on='Team', right_on='current_team')
eff_stats["NetEfficiency"] = eff_stats["AdjOE"] - eff_stats["AdjDE"]

# Calculate means
mean_adjOE = eff_stats["AdjOE"].mean()
mean_adjDE = eff_stats["AdjDE"].mean()

# Create plot
fig, ax = plt.subplots(figsize=(14, 10))

# Shaded quadrants
ax.axhspan(eff_stats["AdjDE"].min(), mean_adjDE, xmin=(mean_adjOE - eff_stats["AdjOE"].min()) / (eff_stats["AdjOE"].max() - eff_stats["AdjOE"].min()), xmax=1, alpha=0.1, color='green')
ax.axhspan(mean_adjDE, eff_stats["AdjDE"].max(), xmin=0, xmax=(mean_adjOE - eff_stats["AdjOE"].min()) / (eff_stats["AdjOE"].max() - eff_stats["AdjOE"].min()), alpha=0.1, color='red')

# Dashed mean lines
ax.axhline(mean_adjDE, linestyle='dashed', color='gray')
ax.axvline(mean_adjOE, linestyle='dashed', color='gray')

# Add logos (or fallback text)
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
        add_logo(row["AdjOE"], row["AdjDE"], row["logo"], ax)
    else:
        ax.text(row["AdjOE"], row["AdjDE"], row["Team"], fontsize=6, ha='center', va='center')

# Labels & aesthetics
ax.set_xlabel("Adjusted Offensive Efficiency", fontsize=16)
ax.set_ylabel("Adjusted Defensive Efficiency", fontsize=16)
ax.set_title("Men's CBB Landscape | Top 100 Teams", fontsize=22, weight='bold')
ax.invert_yaxis()
ax.grid(True)

plt.tight_layout()
plt.savefig("kenpom_top100_eff.png", dpi=300)
plt.close()
print("✅ Plot saved as kenpom_top100_eff.png")
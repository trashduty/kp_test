# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)
library(httr)
library(jsonlite)

# Set timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Create docs directory if it doesn't exist
dir.create("docs", showWarnings = FALSE)

# Load data frames and immediately print their column names
cat("\n=== Loading kenpom_stats.csv ===\n")
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
cat("Actual column names in kenpom_stats.csv:\n")
print(colnames(eff_stats))

# Rename columns for easier use in plotting
# The CSV now has _value and _rank suffixes for paired columns
eff_stats <- eff_stats %>%
  rename(
    ORtg = ORtg_value,
    DRtg = DRtg_value,
    AdjT = AdjT_value,
    Luck = Luck_value
  )

cat("\n=== Loading ncaa_teams_colors_logos_CBB.csv ===\n")
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE)
cat("Columns in ncaa_teams_colors_logos_CBB.csv:\n")
print(colnames(ncaa_teams))

cat("\n=== Loading 2026 Crosswalk.csv ===\n")
crosswalk <- read_csv("2026 Crosswalk.csv", show_col_types = FALSE)
cat("Columns in 2026 Crosswalk.csv:\n")
print(colnames(crosswalk))

cat("\n=== Loading championship_odds.csv ===\n")
championship_odds <- read_csv("championship_odds.csv", show_col_types = FALSE)
cat("Columns in championship_odds.csv:\n")
print(colnames(championship_odds))

# Process championship odds data
championship_odds <- championship_odds %>%
  left_join(crosswalk, by = c("Team" = "API")) %>%
  select(kenpom, Odds)

# Join datasets and filter for updated criteria
eff_stats_joined <- eff_stats %>% 
  filter(ORtg_rank < 68, DRtg_rank < 55) %>%
  left_join(ncaa_teams, by = c("Team" = "current_team")) %>%
  left_join(championship_odds, by = c("Team" = "kenpom"))

# Calculate text positions - move text below logos
text_offset <- 3  # Adjust this value to control how far below the logos the text appears
eff_stats_joined <- eff_stats_joined %>%
  mutate(
    text_y = DRtg_rank + text_offset,  # Position text below logos
    segment_xend = ORtg_rank,  # Line will be vertical
    segment_yend = DRtg_rank + (text_offset * 0.8)  # Line ends just before text
  )

# Create the plot
p <- eff_stats_joined %>% 
  ggplot(aes(x = ORtg_rank, y = DRtg_rank)) +
  # Add solid green vertical line from (57, top) to (57, 44)
  geom_segment(aes(x = 57, xend = 57, y = min(eff_stats$DRtg_rank), yend = 44), 
               color = "green", size = 1.5) +
  # Add solid green horizontal line from (left, 44) to (57, 44)
  geom_segment(aes(x = min(eff_stats$ORtg_rank), xend = 57, y = 44, yend = 44), 
               color = "green", size = 1.5) +
  # Add red dashed vertical line from (21, top) to (21, 44)
  geom_segment(aes(x = 21, xend = 21, y = min(eff_stats$DRtg_rank), yend = 44), 
               color = "red", linetype = "dashed", size = 1.5) +
  # Add connecting lines from logos to text
  geom_segment(
    aes(xend = segment_xend, yend = segment_yend),
    color = "gray50",
    size = 0.5
  ) +
  # Add team logos
  geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
  # Add championship odds as text below logos with connecting lines
  geom_text(
    aes(y = text_y, label = Odds),
    size = 5,  # Increased text size
    fontface = "bold",
    color = "black",
    bg.color = "white",  # Add white background to text
    bg.r = 0.2  # Control the size of the background
  ) +
  theme_bw() +
  labs(
    x = "Offensive Efficiency Rank",
    y = "Defensive Efficiency Rank",
    title = "2026 March Madness Winner Watch List",
    subtitle = "Using data from kenpom.com",
    caption = timestamp
  ) +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title = element_text(size = 25),
    plot.caption = element_text(size = 10, hjust = 1)
  ) +
  scale_x_reverse(breaks = scales::pretty_breaks(n = 6)) +
  scale_y_reverse(breaks = scales::pretty_breaks(n = 8))

# Save the plot in docs directory for GitHub Pages
ggsave('docs/plots/mm_winner_plot.png', p, width = 14, height = 10, dpi = "retina")

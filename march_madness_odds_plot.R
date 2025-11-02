# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)
library(httr)
library(jsonlite)

# Get current timestamp
timestamp <- format(as.POSIXct("2025-11-02 02:49:49"), "%Y-%m-%d %H:%M:%S UTC")

# Load data and crosswalk
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE)
crosswalk <- read_csv("2026 Crosswalk.csv", show_col_types = FALSE)

# Load championship odds
championship_odds <- read_csv("championship_odds.csv", show_col_types = FALSE) %>%
  left_join(crosswalk, by = c("Team" = "API")) %>%
  select(kenpom, Odds)

# Join datasets and filter for updated criteria
eff_stats_joined <- eff_stats %>% 
  left_join(ncaa_teams, by = c("Team" = "Team")) %>% 
  filter(eff_stats[,7] < 68, eff_stats[,8] < 55) %>%  # Using correct rank columns
  left_join(championship_odds, by = c("Team" = "kenpom"))

# Create the plot
p <- eff_stats_joined %>% 
  ggplot(aes(x = eff_stats[,7], y = eff_stats[,8])) +  # Using correct rank columns
  # Add solid green vertical line from (57, top) to (57, 44)
  geom_segment(aes(x = 57, xend = 57, y = min(eff_stats[,8]), yend = 44), 
               color = "green", size = 1.5) +
  # Add solid green horizontal line from (left, 44) to (57, 44)
  geom_segment(aes(x = min(eff_stats[,7]), xend = 57, y = 44, yend = 44), 
               color = "green", size = 1.5) +
  # Add red dashed vertical line from (21, top) to (21, 44)
  geom_segment(aes(x = 21, xend = 21, y = min(eff_stats[,8]), yend = 44), 
               color = "red", linetype = "dashed", size = 1.5) +
  # Add team logos
  geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
  # Add championship odds as text above logos
  geom_text(aes(label = Odds), hjust = 0.5, vjust = 0.8, size = 3, color = "red") +
  theme_bw() +
  labs(
    x = "Offensive Efficiency Rank",
    y = "Defensive Efficiency Rank",
    title = "2026 March Madness Winner Watch List",
    subtitle = "Using data from kenpom.com",
    caption = timestamp  # Add timestamp
  ) +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title = element_text(size = 25),
    plot.caption = element_text(size = 10, hjust = 1)  # Right-aligned timestamp
  ) +
  scale_x_reverse(breaks = scales::pretty_breaks(n = 6)) +  # Reversed for rankings
  scale_y_reverse(breaks = scales::pretty_breaks(n = 8))  # Reversed for rankings

# Save the plot
ggsave('mm_winner_plot.png', p, width = 14, height = 10, dpi = "retina")

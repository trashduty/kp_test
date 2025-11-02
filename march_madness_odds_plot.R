# Load necessary libraries
library(tidyverse)
library(ggimage)
library(ggplot2)
library(readr)

# Load data and crosswalk
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE)
crosswalk <- read_csv("2026 Crosswalk.csv", show_col_types = FALSE)

# Function to get championship odds from the OddsAPI data
get_championship_odds <- function() {
  odds_data <- read_csv("CBB_Output.csv", show_col_types = FALSE)
  
  # Filter for championship markets and get highest odds for each team
  championship_odds <- odds_data %>%
    filter(grepl("championship", tolower(Game))) %>%
    group_by(Team) %>%
    summarize(Odds = max(`Opening Moneyline`, na.rm = TRUE))
  
  # Join with crosswalk to convert API team names to KenPom names
  championship_odds <- championship_odds %>%
    left_join(crosswalk, by = c("Team" = "API")) %>%
    select(kenpom, Odds)
  
  return(championship_odds)
}

# Get current timestamp
timestamp <- format(as.POSIXct("2025-11-02 01:48:49"), "%Y-%m-%d %H:%M:%S UTC")

# Join datasets and filter for updated criteria
# Using the ranks from columns following the first ORtg and DRtg columns
eff_stats_joined <- eff_stats %>% 
  left_join(ncaa_teams, by = c("Team" = "Team")) %>% 
  filter(eff_stats[,7] < 68, eff_stats[,8] < 55)  # Using correct rank columns

# Get championship odds and join with filtered data
championship_odds <- get_championship_odds()
eff_stats_joined <- eff_stats_joined %>%
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

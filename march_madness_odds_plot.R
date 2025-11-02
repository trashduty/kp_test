# Load necessary libraries
library(tidyverse)
library(ggimage)
library(ggplot2)
library(readr)
library(httr)
library(jsonlite)

# Load data and crosswalk
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE)
crosswalk <- read_csv("2026 Crosswalk.csv", show_col_types = FALSE)

# Function to get championship odds from the OddsAPI
get_championship_odds <- function() {
  api_url <- "https://api.the-odds-api.com/v4/sports/basketball_ncaab_championship_winner/odds/"
  response <- GET(api_url, 
                 query = list(apiKey = "9c8e92e73335bb6a206e6b657f41cb13",
                            regions = "us",
                            oddsFormat = "american"))
  
  if (status_code(response) == 200) {
    data <- fromJSON(rawToChar(response$content))
    odds_data <- data$bookmakers[[1]]$markets[[1]]$outcomes %>%
      as.data.frame() %>%
      select(name, price) %>%
      rename(Team = name, Odds = price)
    
    # Join with crosswalk
    odds_data <- odds_data %>%
      left_join(crosswalk, by = c("Team" = "API")) %>%
      select(kenpom, Odds)
    
    return(odds_data)
  } else {
    warning("Failed to fetch odds data")
    return(data.frame(kenpom = character(), Odds = numeric()))
  }
}

# Get current timestamp from provided date
timestamp <- format(as.POSIXct("2025-11-02 01:58:04"), "%Y-%m-%d %H:%M:%S UTC")

# Join datasets and filter for updated criteria
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

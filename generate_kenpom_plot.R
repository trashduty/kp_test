# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Function to standardize team names
standardize_team_name <- function(name) {
  # Create a mapping of variations to standard names
  name_mapping <- c(
    "Iowa St." = "Iowa State",
    "St. John's" = "St. John's",
    "UConn" = "Connecticut",
    "Florida St." = "Florida State",
    "Michigan St." = "Michigan State",
    "Mississippi St." = "Mississippi State",
    "Kansas St." = "Kansas State",
    "NC State" = "N.C. State",
    "TCU" = "Texas Christian",
    "San Diego St." = "San Diego State",
    "Arizona St." = "Arizona State",
    "Boise St." = "Boise State",
    "Ohio St." = "Ohio State",
    "Utah St." = "Utah State",
    "LSU" = "Louisiana State",
    "UCF" = "Central Florida",
    "SMU" = "Southern Methodist",
    "USC" = "Southern California",
    "UNLV" = "Nevada Las Vegas",
    "BYU" = "Brigham Young",
    "UNC" = "North Carolina",
    "VCU" = "Virginia Commonwealth",
    "UAB" = "Alabama Birmingham",
    "Ole Miss" = "Mississippi",
    "UMass" = "Massachusetts"
  )
  
  # Look up the standardized name, if not found, return original
  ifelse(name %in% names(name_mapping), 
         name_mapping[name], 
         name)
}

# Function to create base plot with specific means
create_base_plot <- function(data, means_data, title_prefix = "") {
  # Calculate means using provided data
  mean_ORtg <- mean(means_data$ORtg, na.rm = TRUE)
  mean_DRtg <- mean(means_data$DRtg, na.rm = TRUE)
  
  # Current timestamp
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")
  
  ggplot(data, aes(x = ORtg, y = DRtg)) +
    annotate("rect", xmin = mean_ORtg, xmax = Inf, ymin = -Inf, ymax = mean_DRtg, 
             alpha = 0.1, fill = "green") +
    annotate("rect", xmin = -Inf, xmax = mean_ORtg, ymin = mean_DRtg, ymax = Inf, 
             alpha = 0.1, fill = "red") +
    geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
    geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
    geom_image(aes(image = logo), size = 0.04, asp = 16/9) +
    theme_bw() +
    theme(
      plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title = element_text(size = 25),
      plot.caption = element_text(size = 10, hjust = 1)
    ) +
    scale_x_continuous(breaks = pretty_breaks(n = 6)) +
    scale_y_reverse(breaks = pretty_breaks(n = 6)) +
    labs(
      x = "Adjusted Offensive Efficiency",
      y = "Adjusted Defensive Efficiency",
      title = paste0(title_prefix),
      subtitle = "Using data from kenpom.com",
      caption = timestamp
    )
}

# Load and standardize KenPom data
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE) |>
  rename(
    ORtg = `ORtg...6`,
    ORtg_rank = `ORtg...7`,
    DRtg = `DRtg...8`,
    DRtg_rank = `DRtg...9`,
    AdjT = `AdjT...10`,
    AdjT_rank = `AdjT...11`,
    Luck = `Luck...12`,
    Luck_rank = `Luck...13`
  ) |>
  mutate(Team = sapply(Team, standardize_team_name))

ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Load and standardize AP Top 25 data if available
ap_teams <- tryCatch({
  read_csv("ap_top25.csv", show_col_types = FALSE) |>
    mutate(Team = sapply(Team, standardize_team_name))
}, error = function(e) NULL)

# 1. Top 100 Plot (using top 100 means)
eff_stats_top100 <- eff_stats |> 
  slice(1:100) |>  
  left_join(ncaa_teams, by = c("Team" = "current_team"))

# Use top 100 means for this plot
p1 <- create_base_plot(eff_stats_top100, eff_stats_top100, 
                      "Men's CBB Landscape | Top 100 Teams")

ggsave("plots/kenpom_top100_eff.png", plot = p1, width = 14, height = 10, dpi = "retina")

# 2. Individual Conference Plots (using conference-specific means)
# Create plots directory if it doesn't exist
dir.create("plots/conferences", showWarnings = FALSE, recursive = TRUE)

# Get all conferences
conferences <- unique(eff_stats$Conf)

# Generate plot for each conference
for(conf in conferences) {
  # Filter data for current conference
  conf_data <- eff_stats |> 
    filter(Conf == conf) |>
    left_join(ncaa_teams, by = c("Team" = "current_team"))
  
  # Only create plot if conference has teams
  if(nrow(conf_data) > 0) {
    # Use conference-specific means
    p_conf <- create_base_plot(conf_data, conf_data,
                              paste("Men's CBB Landscape |", conf, "Conference"))
    
    # Save plot with conference name in filename
    filename <- paste0("plots/conferences/kenpom_", 
                      tolower(gsub("[^[:alnum:]]", "_", conf)), 
                      "_eff.png")
    ggsave(filename, plot = p_conf, width = 14, height = 10, dpi = "retina")
  }
}

# 3. AP Top 25 Plot (using top 100 means)
if (!is.null(ap_teams)) {
  # Debug print
  cat("\nAP Top 25 Teams after standardization:\n")
  print(ap_teams$Team)
  
  eff_stats_ap25 <- eff_stats |> 
    inner_join(ap_teams, by = "Team") |>
    left_join(ncaa_teams, by = c("Team" = "current_team"))
  
  # Debug print
  cat("\nTeams missing logos:\n")
  missing_logos <- eff_stats_ap25 |> 
    filter(is.na(logo)) |>
    select(Team)
  print(missing_logos)
  
  # Use top 100 means for AP Top 25 plot
  top_100_means <- eff_stats |> slice(1:100)
  p3 <- create_base_plot(eff_stats_ap25, top_100_means,
                        "Men's CBB Landscape | AP Top 25 Teams")
  
  ggsave("plots/kenpom_ap25_eff.png", plot = p3, width = 14, height = 10, dpi = "retina")
}

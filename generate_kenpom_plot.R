# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Function to create base plot with specific means
create_base_plot <- function(data, means_data, title_prefix = "") {
  # Validate required columns exist in data
  required_cols <- c("ORtg_value", "DRtg_value", "logo")
  missing_cols <- setdiff(required_cols, colnames(data))
  if (length(missing_cols) > 0) {
    stop(paste("Missing required columns in data:", paste(missing_cols, collapse=", ")))
  }
  
  # Validate required columns exist in means_data
  required_mean_cols <- c("ORtg_value", "DRtg_value")
  missing_mean_cols <- setdiff(required_mean_cols, colnames(means_data))
  if (length(missing_mean_cols) > 0) {
    stop(paste("Missing required columns in means_data:", paste(missing_mean_cols, collapse=", ")))
  }
  
  # Calculate means using provided data
  mean_ORtg <- mean(means_data$ORtg_value, na.rm = TRUE)
  mean_DRtg <- mean(means_data$DRtg_value, na.rm = TRUE)
  
  # Current timestamp
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")
  
  ggplot(data, aes(x = ORtg_value, y = DRtg_value)) +
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

# Load KenPom data (columns already have _value and _rank suffixes from Python scraper)
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
cat("Actual column names in kenpom_stats.csv:\n")
print(colnames(eff_stats))

# Load NCAA teams data
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Debug print available team names
cat("\nFirst few NCAA team names in logo file:\n")
print(head(ncaa_teams$current_team, 20))

# Load AP Top 25 data if available
# Team names are already in KenPom format from Python scraper
ap_teams <- tryCatch({
  read_csv("ap_top25.csv", show_col_types = FALSE)
}, error = function(e) NULL)

# 1. Top 100 Plot (using top 100 means, original team names)
eff_stats_top100 <- eff_stats |> 
  slice(1:100) |>  
  left_join(ncaa_teams, by = c("Team" = "current_team"))

# Use top 100 means for this plot
p1 <- create_base_plot(eff_stats_top100, eff_stats_top100, 
                      "Men's CBB Landscape | Top 100 Teams")

ggsave("plots/kenpom_top100_eff.png", plot = p1, width = 14, height = 10, dpi = "retina")

# 2. Individual Conference Plots (using conference-specific means, original team names)
# Create plots directory if it doesn't exist
dir.create("plots/conferences", showWarnings = FALSE, recursive = TRUE)

# Get all conferences and sort alphabetically
conferences <- sort(unique(eff_stats$Conf))

# Generate plot for each conference
for(conf in conferences) {
  # Filter data for current conference (uses original KenPom team names)
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

# 3. AP Top 25 Plot (using top 100 means, standardized team names for AP data only)
if (!is.null(ap_teams)) {
  # Debug print AP teams (already in KenPom format from Python)
  cat("\nAP Top 25 Teams (KenPom format):\n")
  print(ap_teams)
  
  # Join with KenPom stats
  cat("\nAfter joining with KenPom stats:\n")
  eff_stats_ap25 <- eff_stats |> 
    inner_join(ap_teams, by = "Team")
  print(eff_stats_ap25$Team)
  
  # Debug print NCAA teams data for these teams
  cat("\nLooking up these teams in NCAA logos data:\n")
  for(team in eff_stats_ap25$Team) {
    cat(sprintf("Team: %s, Logo found: %s\n", 
                team, 
                ifelse(team %in% ncaa_teams$current_team, "YES", "NO")))
  }
  
  # Final join with logos
  eff_stats_ap25 <- eff_stats_ap25 |>
    left_join(ncaa_teams, by = c("Team" = "current_team"))
  
  # Debug print teams missing logos
  cat("\nTeams missing logos after final join:\n")
  missing_logos <- eff_stats_ap25 |> 
    filter(is.na(logo)) |>
    select(Team)
  print(missing_logos)
  
  # Debug print final data
  cat("\nFinal data for plotting:\n")
  print(eff_stats_ap25 |> select(Team, logo))
  
  # Use top 100 means for AP Top 25 plot
  top_100_means <- eff_stats |> slice(1:100)
  
  # Identify teams with overlapping stats (identical ORtg_value and DRtg_value)
  # Group by ORtg_value and DRtg_value to find duplicates
  overlapping_teams <- eff_stats_ap25 |>
    group_by(ORtg_value, DRtg_value) |>
    filter(n() > 1) |>
    arrange(ORtg_value, DRtg_value, Rank) |>
    mutate(overlap_position = row_number()) |>
    ungroup()
  
  # Pre-compute non-overlapping teams for efficiency
  non_overlapping_teams <- anti_join(eff_stats_ap25, overlapping_teams, by = "Team")
  
  # Base plot with text for non-overlapping teams
  p3 <- create_base_plot(eff_stats_ap25, top_100_means,
                        "Men's CBB Landscape | AP Top 25 Teams") +
    geom_text(data = non_overlapping_teams,
              aes(x = ORtg_value, y = DRtg_value - 1.5, label = Rank),
              color = "red",
              fontface = "bold",
              size = 4,
              vjust = 1.2)  # Position text above logos (y-axis is reversed)
  
  # Add text layers for overlapping teams with horizontal offsets
  if (nrow(overlapping_teams) > 0) {
    # Add first team in each overlap group (normal position)
    p3 <- p3 +
      geom_text(data = overlapping_teams |> filter(overlap_position == 1),
                aes(x = ORtg_value, y = DRtg_value - 1.5, label = Rank),
                color = "red",
                fontface = "bold",
                size = 4,
                vjust = 1.2)
    
    # Add subsequent teams with horizontal offset
    p3 <- p3 +
      geom_text(data = overlapping_teams |> filter(overlap_position > 1),
                aes(x = ORtg_value, y = DRtg_value - 1.5, label = Rank),
                color = "red",
                fontface = "bold",
                size = 4,
                vjust = 1.2,
                hjust = -0.5)  # Offset horizontally for overlapping teams
  }
  
  ggsave("plots/kenpom_ap25_eff.png", plot = p3, width = 14, height = 10, dpi = "retina")
}

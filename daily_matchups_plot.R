# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

# Get today's date in different formats
today <- Sys.Date()
today_str <- format(today, "%Y-%m-%d")
today_formatted <- format(today, "%B %d, %Y")  # Month Day, Year format

cat("\nCreating plot for date:", today_formatted, "\n")

# Set timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Create docs/plots directory if it doesn't exist
dir.create("docs/plots", recursive = TRUE, showWarnings = FALSE)
cat("Created/verified docs/plots directory\n")

# Load and prepare KenPom stats
cat("\nLoading KenPom stats...\n")
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
cat("Actual column names in kenpom_stats.csv:\n")
print(colnames(eff_stats))

eff_stats <- eff_stats %>%
  rename(
    ORtg_rank = `ORtg...2`,
    DRtg_rank = `DRtg...2`,
    AdjT_rank = `AdjT...2`,
    Luck_rank = `Luck...2`
  )
cat("Loaded", nrow(eff_stats), "teams from KenPom stats\n")

# Calculate means using ALL teams
mean_ORtg <- mean(eff_stats$ORtg, na.rm = TRUE)
mean_DRtg <- mean(eff_stats$DRtg, na.rm = TRUE)

cat("\nMean ORtg (all teams):", mean_ORtg, "\n")
cat("Mean DRtg (all teams):", mean_DRtg, "\n")

# Load NCAA teams data for logos
cat("\nLoading NCAA teams data...\n")
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE)
cat("Loaded", nrow(ncaa_teams), "teams with logos\n")

# Load matchups data
cat("\nLoading matchups data...\n")
if (file.exists("daily_matchups.csv")) {
  matchups <- read_csv("daily_matchups.csv", show_col_types = FALSE)
  cat("Matchups data contents:\n")
  print(matchups)
  
  # Get all teams playing today
  teams_playing <- c(matchups$Team1, matchups$Team2) %>%
    unique() %>%
    .[!grepl("^NR ", .)]  # Remove teams starting with "NR"
} else {
  warning("⚠️ No daily_matchups.csv found. Creating empty dataframe.")
  teams_playing <- character(0)
}

cat("\nFound", length(teams_playing), "teams playing today:\n")
print(teams_playing)

# Filter stats for teams playing today and join with logos
matchup_stats <- eff_stats %>%
  filter(Team %in% teams_playing) %>%
  left_join(ncaa_teams, by = c("Team" = "current_team"))

cat("\nSuccessfully matched", nrow(matchup_stats), "teams with stats and logos\n")
if (nrow(matchup_stats) > 0) {
  cat("Sample of matched teams:\n")
  print(head(matchup_stats %>% select(Team, ORtg, DRtg, logo)))
}

if (nrow(matchup_stats) > 0) {
  cat("\nCreating plot...\n")
  # Create the plot
  p <- ggplot() +
    # Add quadrant shading based on all teams' means
    annotate("rect", xmin = mean_ORtg, xmax = max(eff_stats$ORtg), 
             ymin = min(eff_stats$DRtg), ymax = mean_DRtg,
             alpha = 0.1, fill = "green") +
    annotate("rect", xmin = min(eff_stats$ORtg), xmax = mean_ORtg, 
             ymin = mean_DRtg, ymax = max(eff_stats$DRtg),
             alpha = 0.1, fill = "red") +
    # Add reference lines at means
    geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
    geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
    # Add team logos only for teams playing today
    geom_image(data = matchup_stats, 
              aes(x = ORtg, y = DRtg, image = logo), 
              size = 0.04, asp = 16/9) +
    # Set plot limits based on all teams' data
    scale_x_continuous(limits = c(min(eff_stats$ORtg), max(eff_stats$ORtg)),
                       breaks = pretty_breaks(n = 6)) +
    scale_y_reverse(limits = c(max(eff_stats$DRtg), min(eff_stats$DRtg)),
                    breaks = pretty_breaks(n = 8)) +
    theme_bw() +
    labs(
      x = "Adjusted Offensive Efficiency",
      y = "Adjusted Defensive Efficiency",
      title = paste("College Basketball Matchups For", today_formatted),
      subtitle = paste(length(teams_playing), "Teams Playing"),
      caption = timestamp
    ) +
    theme(
      plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(size = 18, hjust = 0.5),
      axis.title = element_text(size = 16),
      plot.caption = element_text(size = 10, hjust = 1)
    )

  # Save the plot
  output_file <- file.path("docs", "plots", paste0("daily_matchups_", today_str, ".png"))
  cat("\nSaving plot to:", output_file, "\n")
  ggsave(output_file, p, width = 14, height = 10, dpi = "retina")
  cat("Plot saved successfully\n")
} else {
  warning("⚠️ No teams with matchup data found. Skipping plot generation.")
}

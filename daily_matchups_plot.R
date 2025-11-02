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
    "Iowa State" = "Iowa St.",
    "St. John's" = "St. John's",
    "UConn" = "Connecticut",
    "Florida St." = "Florida State",
    "Michigan State" = "Michigan St.",
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
    "BYU" = "BYU",
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

# Load KenPom data for all teams (for calculating means)
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
  )

# Load NCAA teams data for logos
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Load daily matchups (teams playing tomorrow)
daily_matchups <- tryCatch({
  read_csv("daily_matchups.csv", show_col_types = FALSE)
}, error = function(e) {
  cat("⚠️ No daily_matchups.csv found. Creating empty dataframe.\n")
  data.frame(Team = character(0))
})

# Standardize team names in matchups to match KenPom format
if (nrow(daily_matchups) > 0) {
  daily_matchups <- daily_matchups |>
    mutate(Team = sapply(Team, standardize_team_name))
}

cat(sprintf("\nFound %d teams playing tomorrow:\n", nrow(daily_matchups)))
if (nrow(daily_matchups) > 0) {
  print(daily_matchups$Team)
}

# Calculate means using ALL teams in KenPom data
mean_ORtg <- mean(eff_stats$ORtg, na.rm = TRUE)
mean_DRtg <- mean(eff_stats$DRtg, na.rm = TRUE)

cat(sprintf("\nMean ORtg (all teams): %.2f\n", mean_ORtg))
cat(sprintf("Mean DRtg (all teams): %.2f\n", mean_DRtg))

# Filter to only teams playing tomorrow and join with logos
# Note: inner_join automatically filters out NR (non-ranked) teams that aren't in KenPom stats
eff_stats_matchups <- eff_stats |>
  inner_join(daily_matchups, by = "Team") |>
  left_join(ncaa_teams, by = c("Team" = "current_team"))

cat(sprintf("\nSuccessfully matched %d teams with stats and logos\n", nrow(eff_stats_matchups)))

# Only create plot if we have matchup data
if (nrow(eff_stats_matchups) > 0) {
  # Current timestamp
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")
  
  # Create the plot
  p <- ggplot(eff_stats_matchups, aes(x = ORtg, y = DRtg)) +
    # Add quadrant shading using all teams' means
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
      title = "Tomorrow's College Basketball Matchups",
      subtitle = "Using data from kenpom.com",
      caption = timestamp
    )
  
  # Create docs/plots directory if it doesn't exist
  dir.create("docs/plots", showWarnings = FALSE, recursive = TRUE)
  
  # Save plot with date in filename
  date_str <- format(Sys.time(), "%Y-%m-%d")
  filename <- sprintf("docs/plots/daily_matchups_%s.png", date_str)
  ggsave(filename, plot = p, width = 14, height = 10, dpi = "retina")
  
  cat(sprintf("\n✅ Plot saved to: %s\n", filename))
} else {
  cat("\n⚠️ No teams with matchup data found. Skipping plot generation.\n")
}

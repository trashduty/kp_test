# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Load KenPom data
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

# Load championship odds
championship_odds <- tryCatch({
  read_csv("championship_odds.csv", show_col_types = FALSE)
}, error = function(e) {
  cat("⚠️  Warning: Could not load championship_odds.csv\n")
  print(e)
  NULL
})

# Load team name crosswalk
crosswalk <- tryCatch({
  read_csv("team_name_crosswalk.csv", show_col_types = FALSE)
}, error = function(e) {
  cat("⚠️  Warning: Could not load team_name_crosswalk.csv\n")
  print(e)
  NULL
})

if (is.null(championship_odds)) {
  cat("❌ Cannot create March Madness plot without championship odds data\n")
  quit(status = 1)
}

cat("\n📊 Championship Odds Data:\n")
print(head(championship_odds, 10))

# If crosswalk exists, standardize OddsAPI team names to KenPom format
if (!is.null(crosswalk)) {
  cat("\n🔄 Applying team name crosswalk...\n")
  
  # Create a lookup vector from the crosswalk
  name_lookup <- setNames(crosswalk$KenPom_Name, crosswalk$OddsAPI_Name)
  
  # Apply the crosswalk to championship odds
  championship_odds <- championship_odds |>
    mutate(
      Team_Original = Team,
      Team = ifelse(Team %in% names(name_lookup), 
                   name_lookup[Team], 
                   Team)
    )
  
  cat("\n✅ Crosswalk applied. Sample mappings:\n")
  print(championship_odds |> 
        filter(Team_Original != Team) |> 
        select(Team_Original, Team) |> 
        head(10))
}

# Filter teams based on ORtg_rank and DRtg_rank
# Select top teams (e.g., top 50 in both offensive and defensive efficiency)
# This creates a March Madness contender plot
ORTG_RANK_THRESHOLD <- 75
DRTG_RANK_THRESHOLD <- 75

cat(sprintf("\n🎯 Filtering teams with ORtg_rank <= %d AND DRtg_rank <= %d\n", 
            ORTG_RANK_THRESHOLD, DRTG_RANK_THRESHOLD))

march_madness_teams <- eff_stats |>
  filter(ORtg_rank <= ORTG_RANK_THRESHOLD & DRtg_rank <= DRTG_RANK_THRESHOLD) |>
  left_join(ncaa_teams, by = c("Team" = "current_team"))

cat(sprintf("\n✅ Filtered to %d teams\n", nrow(march_madness_teams)))

# Join with championship odds
march_madness_teams <- march_madness_teams |>
  left_join(championship_odds |> select(Team, ImpliedProbability), 
            by = "Team")

# Debug: Show teams with and without odds
teams_with_odds <- march_madness_teams |> 
  filter(!is.na(ImpliedProbability))
teams_without_odds <- march_madness_teams |> 
  filter(is.na(ImpliedProbability))

cat(sprintf("\n📈 Teams with championship odds: %d\n", nrow(teams_with_odds)))
cat(sprintf("⚠️  Teams without championship odds: %d\n", nrow(teams_without_odds)))

if (nrow(teams_without_odds) > 0) {
  cat("\nTeams missing odds:\n")
  print(teams_without_odds$Team)
}

# Calculate means using the filtered dataset
mean_ORtg <- mean(march_madness_teams$ORtg, na.rm = TRUE)
mean_DRtg <- mean(march_madness_teams$DRtg, na.rm = TRUE)

# Current timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Define constants for plot positioning
ODDS_TEXT_OFFSET <- -1.5  # Vertical offset for odds text above logos

cat("\n🎨 Creating March Madness Championship Odds plot...\n")

# Create the plot
p <- ggplot(march_madness_teams, aes(x = ORtg, y = DRtg)) +
  # Add quadrant backgrounds
  annotate("rect", xmin = mean_ORtg, xmax = Inf, ymin = -Inf, ymax = mean_DRtg, 
           alpha = 0.1, fill = "green") +
  annotate("rect", xmin = -Inf, xmax = mean_ORtg, ymin = mean_DRtg, ymax = Inf, 
           alpha = 0.1, fill = "red") +
  # Add mean lines
  geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
  geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
  # Add team logos
  geom_image(aes(image = logo), size = 0.04, asp = 16/9) +
  # Add championship odds above logos (for teams that have odds)
  geom_text(data = march_madness_teams |> filter(!is.na(ImpliedProbability)),
            aes(x = ORtg, y = DRtg + ODDS_TEXT_OFFSET, 
                label = paste0(round(ImpliedProbability, 1), "%")),
            color = "darkblue",
            fontface = "bold",
            size = 3.5,
            vjust = 1.2) +
  # Styling
  theme_bw() +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5, size = 12),
    axis.title = element_text(size = 25),
    plot.caption = element_text(size = 10, hjust = 1)
  ) +
  scale_x_continuous(breaks = pretty_breaks(n = 6)) +
  scale_y_reverse(breaks = pretty_breaks(n = 6)) +
  labs(
    x = "Adjusted Offensive Efficiency",
    y = "Adjusted Defensive Efficiency",
    title = "March Madness Championship Contenders",
    subtitle = "Championship odds shown above team logos | Data from KenPom.com & The Odds API",
    caption = timestamp
  )

# Save the plot
output_dir <- "plots"
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

output_path <- file.path(output_dir, "march_madness_championship_odds.png")
ggsave(output_path, plot = p, width = 14, height = 10, dpi = "retina")

cat(sprintf("\n✅ Plot saved to %s\n", output_path))

# Also copy to docs/plots for GitHub Pages
docs_output_dir <- "docs/plots"
dir.create(docs_output_dir, showWarnings = FALSE, recursive = TRUE)

docs_output_path <- file.path(docs_output_dir, "march_madness_championship_odds.png")
file.copy(output_path, docs_output_path, overwrite = TRUE)

cat(sprintf("✅ Plot copied to %s\n", docs_output_path))

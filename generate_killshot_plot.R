# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Create docs/plots directory if it doesn't exist
dir.create("docs/plots", showWarnings = FALSE, recursive = TRUE)

# Load killshot data (file is named "Killshot" without extension inside "MM Vids" directory)
killshot_path <- "MM Vids/Killshot"
if (!file.exists(killshot_path)) {
  stop(paste("❌ Killshot data file not found at:", killshot_path))
}
killshot <- read_csv(killshot_path, show_col_types = FALSE)

cat("Actual column names in Killshot file:\n")
print(colnames(killshot))

# Validate required columns
required_cols <- c("rank", "team", "runs_per_game", "runs_conceded_per_game")
missing_cols <- setdiff(required_cols, colnames(killshot))
if (length(missing_cols) > 0) {
  stop(paste("❌ Missing required columns in Killshot file:", paste(missing_cols, collapse = ", ")))
}

cat(sprintf("\n📊 Total teams in Killshot data: %d\n", nrow(killshot)))

# Load 2026 Crosswalk for team name conversion (hasla -> kenpom)
crosswalk_path <- "2026 Crosswalk.csv"
if (!file.exists(crosswalk_path)) {
  stop(paste("❌ Crosswalk file not found at:", crosswalk_path))
}
crosswalk <- read_csv(crosswalk_path, show_col_types = FALSE)

cat("Crosswalk columns:\n")
print(colnames(crosswalk))

# Validate crosswalk has required columns
if (!"hasla" %in% colnames(crosswalk) || !"kenpom" %in% colnames(crosswalk)) {
  stop("❌ Crosswalk must contain 'hasla' and 'kenpom' columns")
}

# Convert team names: match killshot 'team' column to crosswalk 'hasla' column,
# then use corresponding 'kenpom' names for logo lookup
killshot <- killshot |>
  left_join(crosswalk |> select(hasla, kenpom), by = c("team" = "hasla"))

cat("\nTeams without kenpom name match:\n")
missing_kenpom <- killshot |> filter(is.na(kenpom)) |> select(team)
print(missing_kenpom)

# Load NCAA teams data for logos
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

cat("\nFirst few NCAA team names in logo file:\n")
print(head(ncaa_teams$current_team, 20))

# Join logos using kenpom names
killshot <- killshot |>
  left_join(ncaa_teams, by = c("kenpom" = "current_team"))

cat(sprintf("\nTeams with logos: %d / %d\n",
            sum(!is.na(killshot$logo)), nrow(killshot)))

# Calculate means from ALL teams (for reference lines and axis ranges)
mean_runs_per_game <- mean(killshot$runs_per_game, na.rm = TRUE)
mean_runs_conceded_per_game <- mean(killshot$runs_conceded_per_game, na.rm = TRUE)

cat(sprintf("\nMean runs per game (all teams): %.3f\n", mean_runs_per_game))
cat(sprintf("Mean runs conceded per game (all teams): %.3f\n", mean_runs_conceded_per_game))

# Filter to top 70 teams for display (rank is ascending: rank=1 is best)
top70 <- killshot |>
  filter(rank <= 70)

cat(sprintf("\nTop 70 teams selected for display: %d\n", nrow(top70)))

# Validate top70 has logo column
if (!"logo" %in% colnames(top70)) {
  stop("❌ 'logo' column not found after joining with ncaa_teams")
}

# Current timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Build the scatter plot
# X-axis: runs_per_game (higher is better - more scoring runs)
# Y-axis: runs_conceded_per_game (lower is better - fewer runs conceded)
# scale_y_reverse so better defensive teams appear at top of chart

p <- ggplot(top70, aes(x = runs_per_game, y = runs_conceded_per_game)) +
  # Quadrant shading using all-team means
  # Green: high runs_per_game (right) AND low runs_conceded_per_game (good defense)
  annotate("rect",
           xmin = mean_runs_per_game, xmax = Inf,
           ymin = -Inf, ymax = mean_runs_conceded_per_game,
           alpha = 0.1, fill = "green") +
  # Red: low runs_per_game (left) AND high runs_conceded_per_game (bad defense)
  annotate("rect",
           xmin = -Inf, xmax = mean_runs_per_game,
           ymin = mean_runs_conceded_per_game, ymax = Inf,
           alpha = 0.1, fill = "red") +
  # Mean reference lines (dashed)
  geom_hline(yintercept = mean_runs_conceded_per_game, linetype = "dashed") +
  geom_vline(xintercept = mean_runs_per_game, linetype = "dashed") +
  # Team logos
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
    x = "Scoring Runs Per Game",
    y = "Scoring Runs Allowed Per Game",
    title = "Men's CBB Landscape | Top 70 Teams - Scoring Runs",
    subtitle = "Using data from killshot analysis",
    caption = timestamp
  )

# Save the plot
output_path <- "docs/plots/killshot_scoring_runs.png"
ggsave(output_path, plot = p, width = 14, height = 10, dpi = "retina")
cat(sprintf("\n✅ Saved: %s\n", output_path))

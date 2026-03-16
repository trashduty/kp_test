# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Load March Madness KenPom data
mm_stats <- read_csv("MM Vids/kenpom_mm.csv", show_col_types = FALSE)

cat("Actual column names in kenpom_mm.csv:\n")
print(colnames(mm_stats))

# Validate required columns
if (!"ORtg_value" %in% colnames(mm_stats) || !"DRtg_value" %in% colnames(mm_stats)) {
  stop("❌ ORtg_value or DRtg_value columns not found in kenpom_mm.csv")
}

# Calculate means from ALL rows (including those without team names)
mean_ORtg <- mean(mm_stats$ORtg_value, na.rm = TRUE)
mean_DRtg <- mean(mm_stats$DRtg_value, na.rm = TRUE)

cat(sprintf("\nMean ORtg (all rows): %.4f\n", mean_ORtg))
cat(sprintf("Mean DRtg (all rows): %.4f\n", mean_DRtg))

# Load NCAA teams logo data
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Filter to only rows with a non-empty Team name for logo plotting
mm_named <- mm_stats |>
  filter(!is.na(Team) & Team != "") |>
  left_join(ncaa_teams, by = c("Team" = "current_team"))

cat(sprintf("\nTeams with names: %d\n", nrow(mm_named)))

# Debug: teams missing logos
missing_logos <- mm_named |> filter(is.na(logo)) |> select(Team)
if (nrow(missing_logos) > 0) {
  cat("\nTeams missing logos:\n")
  print(missing_logos)
}

# Current timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Build the plot
p <- ggplot(mm_named, aes(x = ORtg_value, y = DRtg_value)) +
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
    title = "Men's CBB Landscape | March Madness Teams",
    subtitle = "Using data from kenpom.com",
    caption = timestamp
  )

# Save the plot
dir.create("plots", showWarnings = FALSE, recursive = TRUE)
ggsave("plots/kenpom_mm_eff.png", plot = p, width = 14, height = 10, dpi = "retina")

cat("\n✅ Plot saved to plots/kenpom_mm_eff.png\n")

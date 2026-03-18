# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Set timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Generalized plot creation function.
# plot_data  : rows with logos, used for plotting team images
# means_data : all rows (incl. those without names), used for quadrant means
# x_col / y_col     : column names in the data frames
# x_label / y_label : axis labels
# x_good_high       : TRUE if higher x values are "good" (green quadrant)
# y_good_high       : TRUE if higher y values are "good" (green quadrant)
# reverse_y         : TRUE to flip the y-axis (useful for defensive efficiency)
create_stats_plot <- function(plot_data, means_data, x_col, y_col,
                              x_label, y_label, title_prefix,
                              x_good_high = TRUE, y_good_high = TRUE,
                              reverse_y = FALSE) {
  mean_x <- mean(means_data[[x_col]], na.rm = TRUE)
  mean_y <- mean(means_data[[y_col]], na.rm = TRUE)

  # Determine the "good" (green) and "bad" (red) quadrant boundaries
  if (x_good_high) {
    green_xmin <- mean_x; green_xmax <- Inf
    red_xmin   <- -Inf;   red_xmax   <- mean_x
  } else {
    green_xmin <- -Inf;   green_xmax <- mean_x
    red_xmin   <- mean_x; red_xmax   <- Inf
  }

  if (y_good_high) {
    green_ymin <- mean_y; green_ymax <- Inf
    red_ymin   <- -Inf;   red_ymax   <- mean_y
  } else {
    green_ymin <- -Inf;   green_ymax <- mean_y
    red_ymin   <- mean_y; red_ymax   <- Inf
  }

  p <- ggplot(plot_data, aes(x = .data[[x_col]], y = .data[[y_col]])) +
    annotate("rect",
             xmin = green_xmin, xmax = green_xmax,
             ymin = green_ymin, ymax = green_ymax,
             alpha = 0.1, fill = "green") +
    annotate("rect",
             xmin = red_xmin, xmax = red_xmax,
             ymin = red_ymin, ymax = red_ymax,
             alpha = 0.1, fill = "red") +
    geom_hline(yintercept = mean_y, linetype = "dashed") +
    geom_vline(xintercept = mean_x, linetype = "dashed") +
    geom_image(aes(image = logo), size = 0.04, asp = 16/9) +
    theme_bw() +
    theme(
      plot.title    = element_text(size = 25, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title    = element_text(size = 25),
      plot.caption  = element_text(size = 10, hjust = 1)
    ) +
    scale_x_continuous(breaks = pretty_breaks(n = 6)) +
    labs(
      x        = x_label,
      y        = y_label,
      title    = title_prefix,
      subtitle = "Using data from kenpom.com",
      caption  = timestamp
    )

  if (reverse_y) {
    p <- p + scale_y_reverse(breaks = pretty_breaks(n = 6))
  } else {
    p <- p + scale_y_continuous(breaks = pretty_breaks(n = 6))
  }

  p
}

# ── Load data ────────────────────────────────────────────────────────────────

# All rows (including those without team names) – used for quadrant means
stats_all <- read_csv("kenpom_stats.csv", show_col_types = FALSE)

cat("Actual column names in kenpom_stats.csv:\n")
print(colnames(stats_all))
cat("\nTotal rows in kenpom_stats.csv:", nrow(stats_all), "\n")

# NCAA logo data
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

cat("\nFirst few NCAA team names in logo file:\n")
print(head(ncaa_teams$current_team, 20))

# Rows with team names joined with logos – used for plotting team images only
stats_plot_data <- stats_all |>
  filter(!is.na(Team) & Team != "") |>
  left_join(ncaa_teams, by = c("Team" = "current_team")) |>
  filter(!is.na(logo))

cat("\nTeams with names:", nrow(stats_all |> filter(!is.na(Team) & Team != "")), "\n")
cat("Teams with logos:", nrow(stats_plot_data), "\n")

# ── Create output directory ──────────────────────────────────────────────────
dir.create("docs/plots/kenpom_stats_axes", showWarnings = FALSE, recursive = TRUE)

# ── Plot 1: Rebounding ───────────────────────────────────────────────────────
# Higher OR_Pct (offensive) = better; lower DOR_Pct (defensive/allowed) = better
p_reb <- create_stats_plot(
  plot_data    = stats_plot_data,
  means_data   = stats_all,
  x_col        = "OR_Pct",
  y_col        = "DOR_Pct",
  x_label      = "Offensive Rebounding %",
  y_label      = "Offensive Rebounding Allowed %",
  title_prefix = "Season Stats | Rebounding",
  x_good_high  = TRUE,
  y_good_high  = FALSE,
  reverse_y    = TRUE
)
ggsave("docs/plots/kenpom_stats_axes/kenpom_stats_rebounding.png", plot = p_reb, width = 14, height = 10, dpi = "retina")
cat("✅ Plot saved to docs/plots/kenpom_stats_axes/kenpom_stats_rebounding.png\n")

# ── Plot 2: Offensive Efficiency vs Tempo ────────────────────────────────────
p_off_tempo <- create_stats_plot(
  plot_data    = stats_plot_data,
  means_data   = stats_all,
  x_col        = "AdjT_value",
  y_col        = "ORtg_value",
  x_label      = "Adjusted Tempo",
  y_label      = "Adjusted Offensive Efficiency",
  title_prefix = "Season Stats | Offensive Efficiency vs. Tempo",
  x_good_high  = TRUE,
  y_good_high  = TRUE
)
ggsave("docs/plots/kenpom_stats_axes/kenpom_stats_oe_tempo.png", plot = p_off_tempo, width = 14, height = 10, dpi = "retina")
cat("✅ Plot saved to docs/plots/kenpom_stats_axes/kenpom_stats_oe_tempo.png\n")

# ── Plot 3: Defensive Efficiency vs Tempo ────────────────────────────────────
# Lower DRtg_value = better defense → y_good_high = FALSE, reverse_y = TRUE
p_def_tempo <- create_stats_plot(
  plot_data    = stats_plot_data,
  means_data   = stats_all,
  x_col        = "AdjT_value",
  y_col        = "DRtg_value",
  x_label      = "Adjusted Tempo",
  y_label      = "Adjusted Defensive Efficiency",
  title_prefix = "Season Stats | Defensive Efficiency vs. Tempo",
  x_good_high  = FALSE,
  y_good_high  = FALSE,
  reverse_y    = TRUE
)
ggsave("docs/plots/kenpom_stats_axes/kenpom_stats_de_tempo.png", plot = p_def_tempo, width = 14, height = 10, dpi = "retina")
cat("✅ Plot saved to docs/plots/kenpom_stats_axes/kenpom_stats_de_tempo.png\n")

# ── Plot 4: Free Throw Rate ──────────────────────────────────────────────────
# Higher FT_Rate (offensive) = better; lower DFT_Rate (defensive) = better
p_ft <- create_stats_plot(
  plot_data    = stats_plot_data,
  means_data   = stats_all,
  x_col        = "FT_Rate",
  y_col        = "DFT_Rate",
  x_label      = "Offensive Free Throw Rate",
  y_label      = "Defensive Free Throw Rate",
  title_prefix = "Season Stats | Free Throw Rate",
  x_good_high  = TRUE,
  y_good_high  = FALSE
)
ggsave("docs/plots/kenpom_stats_axes/kenpom_stats_ft_rate.png", plot = p_ft, width = 14, height = 10, dpi = "retina")
cat("✅ Plot saved to docs/plots/kenpom_stats_axes/kenpom_stats_ft_rate.png\n")

# ── Plot 5: Turnover Percentage ──────────────────────────────────────────────
# Lower TO_Pct (offensive) = better; higher DTO_Pct (defensive/forced) = better
p_to <- create_stats_plot(
  plot_data    = stats_plot_data,
  means_data   = stats_all,
  x_col        = "TO_Pct",
  y_col        = "DTO_Pct",
  x_label      = "Offensive Turnover %",
  y_label      = "Defensive Turnover % (Forced)",
  title_prefix = "Season Stats | Turnover Percentage",
  x_good_high  = FALSE,
  y_good_high  = TRUE
)
ggsave("docs/plots/kenpom_stats_axes/kenpom_stats_turnover.png", plot = p_to, width = 14, height = 10, dpi = "retina")
cat("✅ Plot saved to docs/plots/kenpom_stats_axes/kenpom_stats_turnover.png\n")

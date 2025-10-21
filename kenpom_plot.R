# kenpom_plot.R — 2025 version using summary26.csv

library(tidyverse)
library(ggimage)

message("Starting KenPom plot process...")

# --- Load summary CSV ---
eff_stats <- read_csv("summary26.csv", show_col_types = FALSE)
message("Loaded summary file with ", nrow(eff_stats), " rows.")

# --- Load team colors and logos ---
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# --- Join logos/colors ---
eff_stats_selected <- eff_stats |>
  slice(2:101) |>  # skip KenPom header row if present
  left_join(ncaa_teams, by = c("Team" = "current_team")) |>
  mutate(NetEfficiency = adj_oe - adj_de)

message("Merged top 100 teams and joined logos.")

# --- Calculate mean lines ---
mean_adjOE <- mean(eff_stats_selected$adj_oe, na.rm = TRUE)
mean_adjDE <- mean(eff_stats_selected$adj_de, na.rm = TRUE)

# --- Create quadrant plot ---
p <- eff_stats_selected |>
  ggplot(aes(x = adj_oe, y = adj_de)) +
  # Quadrant shading
  annotate("rect", xmin = mean_adjOE, xmax = Inf, ymin = -Inf, ymax = mean_adjDE,
           alpha = 0.1, fill = "green") +
  annotate("rect", xmin = -Inf, xmax = mean_adjOE, ymin = mean_adjDE, ymax = Inf,
           alpha = 0.1, fill = "red") +
  # Mean lines
  geom_hline(yintercept = mean_adjDE, linetype = "dashed") +
  geom_vline(xintercept = mean_adjOE, linetype = "dashed") +
  # Logos
  geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
  # Labels and theme
  theme_bw() +
  labs(
    x = "Adjusted Offensive Efficiency (adj_oe)",
    y = "Adjusted Defensive Efficiency (adj_de)",
    title = "Men's CBB Landscape | Top 100 Teams",
    subtitle = "Using data from KenPom.com (summary26.csv)"
  ) +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title = element_text(size = 25)
  ) +
  scale_x_continuous(breaks = scales::pretty_breaks(n = 6)) +
  scale_y_reverse(breaks = scales::pretty_breaks(n = 6))

# --- Save output ---
ggsave("kenpom_top100_eff.png", plot = p, width = 14, height = 10, dpi = "retina")

message("Plot saved successfully: kenpom_top100_eff.png")

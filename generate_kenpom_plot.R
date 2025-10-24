# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)

cat("🔎 .libPaths():\n")
print(.libPaths())

cat("🔍 Checking if 'ggimage' is installed...\n")
if (!requireNamespace("ggimage", quietly = TRUE)) {
  stop("❌ ggimage is NOT installed in the visible lib paths.")
} else {
  cat("✅ ggimage is installed. Proceeding to load.\n")
  library(ggimage)
}


# Load data
eff_stats <- read_csv("kenpom_stats.csv", show_col_types = FALSE)
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Select teams
eff_stats_selected <- eff_stats |> 
  slice(1:100) |>  # now row 1 is first team
  left_join(ncaa_teams, by = c("Team" = "current_team")) |> 
  mutate(NetEfficiency = `AdjOE` - `AdjDE`)

# Means for quadrant lines
mean_adjOE <- mean(eff_stats_selected$`AdjOE`, na.rm = TRUE)
mean_adjDE <- mean(eff_stats_selected$`AdjDE`, na.rm = TRUE)

# Plot
p <- eff_stats_selected |> 
  ggplot(aes(x = `AdjOE`, y = `AdjDE`)) +
  annotate("rect", xmin = mean_adjOE, xmax = Inf, ymin = -Inf, ymax = mean_adjDE, alpha = 0.1, fill = "green") +
  annotate("rect", xmin = -Inf, xmax = mean_adjOE, ymin = mean_adjDE, ymax = Inf, alpha = 0.1, fill = "red") +
  geom_hline(yintercept = mean_adjDE, linetype = "dashed") +
  geom_vline(xintercept = mean_adjOE, linetype = "dashed") +
  geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
  theme_bw() +
  labs(
    x = "Adjusted Offensive Efficiency",
    y = "Adjusted Defensive Efficiency",
    title = "Men's CBB Landscape | Top 100 Teams",
    subtitle = "Using data from kenpom.com"
  ) +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title = element_text(size = 25),
    plot.caption = element_text(size = 25)
  ) +
  scale_x_continuous(breaks = scales::pretty_breaks(n = 6)) +
  scale_y_reverse(breaks = scales::pretty_breaks(n = 6))

# Save
ggsave("kenpom_top100_eff.png", plot = p, width = 14, height = 10, dpi = "retina")

# kenpom_plot.R

library(tidyverse)
library(ggimage)

message("Starting KenPom merge + plot process...")

# --- Load offense & defense CSVs you uploaded ---
off <- read_csv("offense26.csv", show_col_types = FALSE)
def <- read_csv("defense26.csv", show_col_types = FALSE)

message("Loaded offense (", nrow(off), " rows) and defense (", nrow(def), " rows).")

# --- Join on team column ---
eff_stats <- off %>%
  rename_with(~paste0(., "_O"), -Team) %>%
  inner_join(def %>% rename_with(~paste0(., "_D"), -Team),
             by = c("Team" = "Team"))

# --- Compute simple efficiency stats ---
eff_stats <- eff_stats %>%
  mutate(AdjOE = `AdjEM_O`, AdjDE = `AdjEM_D`) %>%
  mutate(NetEfficiency = AdjOE - AdjDE)

# --- Save merged dataset for reference ---
write_csv(eff_stats, "four_factors.csv")

# --- Load logos/colors crosswalk ---
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# --- Filter Top 100 (skip first row header if KenPom format includes summary row) ---
eff_stats_selected <- eff_stats |>
  slice(2:101) |>
  left_join(ncaa_teams, by = c("Team" = "current_team"))

message("Filtered top 100 teams.")

# --- Calculate means for quadrant lines ---
mean_adjOE <- mean(eff_stats_selected$AdjOE, na.rm = TRUE)
mean_adjDE <- mean(eff_stats_selected$AdjDE, na.rm = TRUE)

# --- Create plot ---
p <- eff_stats_selected |>
  ggplot(aes(x = AdjOE, y = AdjDE)) +
  annotate("rect", xmin = mean_adjOE, xmax = Inf, ymin = -Inf, ymax = mean_adjDE,
           alpha = 0.1, fill = "green") +
  annotate("rect", xmin = -Inf, xmax = mean_adjOE, ymin = mean_adjDE, ymax = Inf,
           alpha = 0.1, fill = "red") +
  geom_hline(yintercept = mean_adjDE, linetype = "dashed") +
  geom_vline(xintercept = mean_adjOE, linetype = "dashed") +
  geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
  theme_bw() +
  labs(
    x = "Adjusted Offensive Efficiency",
    y = "Adjusted Defensive Efficiency",
    title = "Men's CBB Landscape | Top 100 Teams",
    subtitle = "Using data from KenPom.com"
  ) +
  theme(
    plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title = element_text(size = 25)
  ) +
  scale_x_continuous(breaks = scales::pretty_breaks(n = 6)) +
  scale_y_reverse(breaks = scales::pretty_breaks(n = 6))

# --- Save plot ---
ggsave("kenpom_top100_eff.png", plot = p, width = 14, height = 10, dpi = "retina")

message("Plot saved successfully.")

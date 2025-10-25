# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Function to create base plot using ALL teams' means
create_base_plot <- function(data, full_data, title_prefix = "") {
  # Calculate means using ALL teams
  mean_ORtg <- mean(full_data$ORtg, na.rm = TRUE)
  mean_DRtg <- mean(full_data$DRtg, na.rm = TRUE)
  
  # Current timestamp
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")
  
  ggplot(data, aes(x = ORtg, y = DRtg)) +
    annotate("rect", xmin = mean_ORtg, xmax = Inf, ymin = -Inf, ymax = mean_DRtg, 
             alpha = 0.1, fill = "green") +
    annotate("rect", xmin = -Inf, xmax = mean_ORtg, ymin = mean_DRtg, ymax = Inf, 
             alpha = 0.1, fill = "red") +
    geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
    geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
    geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
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
      title = paste0(title_prefix, " | ", format(Sys.time(), "%Y-%m-%d")),
      subtitle = "Using data from kenpom.com",
      caption = timestamp
    )
}

# Load data
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

ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Load AP Top 25 data if available
ap_teams <- tryCatch(
  read_csv("ap_top25.csv", show_col_types = FALSE),
  error = function(e) NULL
)

# 1. Top 100 Plot (only plot top 100, but use all teams for means)
eff_stats_top100 <- eff_stats |> 
  slice(1:100) |>  
  left_join(ncaa_teams, by = c("Team" = "current_team"))

p1 <- create_base_plot(eff_stats_top100, eff_stats, 
                      "Men's CBB Landscape | Top 100 Teams")

ggsave("plots/kenpom_top100_eff.png", plot = p1, width = 14, height = 10, dpi = "retina")

# 2. Individual Conference Plots
# Create plots directory if it doesn't exist
dir.create("plots/conferences", showWarnings = FALSE, recursive = TRUE)

# Get all conferences
conferences <- unique(eff_stats$Conf)

# Generate plot for each conference
for(conf in conferences) {
  # Filter data for current conference
  conf_data <- eff_stats |> 
    filter(Conf == conf) |>
    left_join(ncaa_teams, by = c("Team" = "current_team"))
  
  # Only create plot if conference has teams
  if(nrow(conf_data) > 0) {
    p_conf <- create_base_plot(conf_data, eff_stats,
                              paste("Men's CBB Landscape |", conf, "Conference"))
    
    # Save plot with conference name in filename
    filename <- paste0("plots/conferences/kenpom_", 
                      tolower(gsub("[^[:alnum:]]", "_", conf)), 
                      "_eff.png")
    ggsave(filename, plot = p_conf, width = 14, height = 10, dpi = "retina")
  }
}

# 3. AP Top 25 Plot (if data available)
if (!is.null(ap_teams)) {
  eff_stats_ap25 <- eff_stats |> 
    inner_join(ap_teams, by = "Team") |>
    left_join(ncaa_teams, by = c("Team" = "current_team"))
  
  p3 <- create_base_plot(eff_stats_ap25, eff_stats,
                        "Men's CBB Landscape | AP Top 25 Teams")
  
  ggsave("plots/kenpom_ap25_eff.png", plot = p3, width = 14, height = 10, dpi = "retina")
}

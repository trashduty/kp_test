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

# Create plots directory structure
if (!dir.exists("plots")) {
  dir.create("plots")
  cat("✅ Created plots/ directory\n")
}
if (!dir.exists("plots/conferences")) {
  dir.create("plots/conferences")
  cat("✅ Created plots/conferences/ directory\n")
}

# Load and clean data
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

# Join all stats with team logos
eff_stats_all <- eff_stats |> 
  left_join(ncaa_teams, by = c("Team" = "current_team")) |> 
  mutate(NetEfficiency = ORtg - DRtg)

# Calculate means from top 100 teams (for consistent quadrants across all plots)
eff_stats_top100 <- eff_stats_all |> slice(1:100)
mean_ORtg <- mean(eff_stats_top100$ORtg, na.rm = TRUE)
mean_DRtg <- mean(eff_stats_top100$DRtg, na.rm = TRUE)

cat(sprintf("📊 Using Top 100 means: ORtg=%.2f, DRtg=%.2f\n", mean_ORtg, mean_DRtg))

# Function to create a consistent plot
create_plot <- function(data, title, subtitle) {
  data |> 
    ggplot(aes(x = ORtg, y = DRtg)) +
    annotate("rect", xmin = mean_ORtg, xmax = Inf, ymin = -Inf, ymax = mean_DRtg, 
             alpha = 0.1, fill = "green") +
    annotate("rect", xmin = -Inf, xmax = mean_ORtg, ymin = mean_DRtg, ymax = Inf, 
             alpha = 0.1, fill = "red") +
    geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
    geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
    geom_image(aes(image = logo), size = 0.05, asp = 16/9) +
    theme_bw() +
    labs(
      x = "Adjusted Offensive Efficiency",
      y = "Adjusted Defensive Efficiency",
      title = title,
      subtitle = subtitle
    ) +
    theme(
      plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title = element_text(size = 25),
      plot.caption = element_text(size = 25)
    ) +
    scale_x_continuous(breaks = scales::pretty_breaks(n = 6)) +
    scale_y_reverse(breaks = scales::pretty_breaks(n = 6))
}

# 1. Generate Top 100 plot
cat("\n[1/3] Generating Top 100 plot...\n")
p_top100 <- create_plot(
  eff_stats_top100,
  "Men's CBB Landscape | Top 100 Teams",
  "Using data from kenpom.com"
)
ggsave("plots/kenpom_top100_eff.png", plot = p_top100, width = 14, height = 10, dpi = "retina")
cat("✅ Saved: plots/kenpom_top100_eff.png\n")

# 2. Generate AP Top 25 plot (if ap_top25.csv exists)
cat("\n[2/3] Generating AP Top 25 plot...\n")
if (file.exists("ap_top25.csv")) {
  ap_teams <- read_csv("ap_top25.csv", show_col_types = FALSE)
  
  eff_stats_ap <- eff_stats_all |> 
    filter(Team %in% ap_teams$Team)
  
  if (nrow(eff_stats_ap) > 0) {
    p_ap25 <- create_plot(
      eff_stats_ap,
      "Men's CBB Landscape | AP Top 25 Teams",
      "Using data from kenpom.com and AP rankings from ESPN"
    )
    ggsave("plots/kenpom_ap25_eff.png", plot = p_ap25, width = 14, height = 10, dpi = "retina")
    cat(sprintf("✅ Saved: plots/kenpom_ap25_eff.png (%d teams)\n", nrow(eff_stats_ap)))
  } else {
    cat("⚠️ No AP teams found in KenPom data\n")
  }
} else {
  cat("⚠️ ap_top25.csv not found, skipping AP Top 25 plot\n")
}

# 3. Generate conference plots
cat("\n[3/3] Generating conference plots...\n")
conferences <- eff_stats_all |> 
  filter(!is.na(Conf)) |> 
  pull(Conf) |> 
  unique() |> 
  sort()

cat(sprintf("Found %d conferences: %s\n", length(conferences), paste(conferences, collapse=", ")))

for (conf in conferences) {
  conf_data <- eff_stats_all |> filter(Conf == conf)
  
  if (nrow(conf_data) > 0) {
    # Create filename-safe conference name by replacing spaces and special chars
    conf_safe <- tolower(conf)
    conf_safe <- gsub("[^a-z0-9]", "", conf_safe)
    filename <- sprintf("plots/conferences/kenpom_%s_eff.png", conf_safe)
    
    p_conf <- create_plot(
      conf_data,
      sprintf("Men's CBB Landscape | %s Conference", conf),
      "Using data from kenpom.com"
    )
    
    ggsave(filename, plot = p_conf, width = 14, height = 10, dpi = "retina")
    cat(sprintf("  ✅ %s: %d teams -> %s\n", conf, nrow(conf_data), filename))
  }
}

cat("\n🎉 All plots generated successfully!\n")

# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

cat("🔎 .libPaths():\n")
print(.libPaths())

# Function to create base plot with specific means
create_base_plot <- function(data, means_data, title_prefix = "") {
  # Validate required columns exist in data
  required_cols <- c("ORtg", "DRtg", "logo")
  missing_cols <- setdiff(required_cols, colnames(data))
  if (length(missing_cols) > 0) {
    stop(paste("Missing required columns in data:", paste(missing_cols, collapse=", ")))  
  }
  
  # Validate required columns exist in means_data
  required_mean_cols <- c("ORtg", "DRtg")
  missing_mean_cols <- setdiff(required_mean_cols, colnames(means_data))
  if (length(missing_mean_cols) > 0) {
    stop(paste("Missing required columns in means_data:", paste(missing_mean_cols, collapse=", ")))  
  }
  
  # Calculate means using provided data
  mean_ORtg <- mean(means_data$ORtg, na.rm = TRUE)
  mean_DRtg <- mean(means_data$DRtg, na.rm = TRUE)
  
  # Current timestamp
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")  
  
ggplot(data, aes(x = ORtg, y = DRtg)) +
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
      title = paste0(title_prefix),
      subtitle = "Using data from kenpom.com",
      caption = timestamp
    )
}

# Load March Madness data from the CSV
mm_stats <- read_csv("MM Vids/kenpom_mm.csv", show_col_types = FALSE)

cat("Actual column names in kenpom_mm.csv:\n")
print(colnames(mm_stats))

# Load NCAA teams data
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |> 
  distinct(current_team, .keep_all = TRUE)

cat("\nFirst few NCAA team names in logo file:\n")
print(head(ncaa_teams$current_team, 20))

# Rename columns for MM data
mm_stats <- mm_stats |> 
  rename(
    ORtg = ORtg_value,
    DRtg = DRtg_value,
    AdjT = AdjT_value,
    Luck = Luck_value
  )

# Join MM teams with NCAA logos
mm_stats_with_logos <- mm_stats |> 
  left_join(ncaa_teams, by = c("Team" = "current_team"))

# Filter to only teams that have logos (remove rows with missing logo data)
mm_stats_complete <- mm_stats_with_logos |> 
  filter(!is.na(logo))

cat("\nNumber of teams with logos:", nrow(mm_stats_complete), "\n")
cat("Number of teams without logos:", nrow(mm_stats_with_logos) - nrow(mm_stats_complete), "\n")

# Create plot using only teams with logos for both plotting AND calculating means
p_mm <- create_base_plot(mm_stats_complete, mm_stats_complete,
                        "Men's CBB Landscape | March Madness Teams")

# Save to docs/plots
ggsave("docs/plots/kenpom_mm_top100_eff.png", plot = p_mm, width = 14, height = 10, dpi = "retina")

cat("✅ Plot saved to docs/plots/kenpom_mm_top100_eff.png\n")

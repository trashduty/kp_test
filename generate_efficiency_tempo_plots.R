# Force R to use the correct library path set by GitHub Actions
.libPaths(c(Sys.getenv("R_LIBS_USER"), .libPaths()))

# Load libraries
library(tidyverse)
library(scales)

# Try to load ggimage (available in GitHub Actions)
ggimage_available <- tryCatch({
  library(ggimage)
  TRUE
}, error = function(e) {
  cat("Note: ggimage not available, will use fallback rendering\n")
  FALSE
})

cat("🔎 .libPaths():\n")
print(.libPaths())
cat(sprintf("ggimage available: %s\n", ggimage_available))

# Create docs/plots directory if it doesn't exist
dir.create("docs/plots", showWarnings = FALSE, recursive = TRUE)

# Load KenPom data
# Note: Column names in kenpom_stats.csv have duplicates, so read_csv adds suffixes
# ORtg...6 = Offensive Rating value, ORtg...7 = Offensive Rating rank, etc.
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

# Validate required columns exist
required_cols <- c("Team", "ORtg", "DRtg", "AdjT")
missing_cols <- setdiff(required_cols, names(eff_stats))
if (length(missing_cols) > 0) {
  stop(sprintf("Missing required columns in kenpom_stats.csv: %s", 
               paste(missing_cols, collapse = ", ")))
}

# Load NCAA teams data for logos
ncaa_teams <- read_csv("ncaa_teams_colors_logos_CBB.csv", show_col_types = FALSE) |>
  distinct(current_team, .keep_all = TRUE)

# Join with logos
all_teams_data <- eff_stats |>
  left_join(ncaa_teams, by = c("Team" = "current_team"))

cat(sprintf("\n📊 Total teams: %d\n", nrow(all_teams_data)))

# Current timestamp
timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")

# Function to determine which teams should show logos
# Based on top/bottom 10% for the efficiency metric and AdjT
get_logo_teams <- function(data, eff_col, higher_is_better = TRUE) {
  n <- nrow(data)
  n_10pct <- ceiling(n * 0.10)
  
  # Get teams in top/bottom 10% for efficiency metric
  if (higher_is_better) {
    # For ORtg, higher is better
    eff_top <- data |> slice_max(order_by = .data[[eff_col]], n = n_10pct) |> pull(Team)
    eff_bottom <- data |> slice_min(order_by = .data[[eff_col]], n = n_10pct) |> pull(Team)
  } else {
    # For DRtg, lower is better (so "top" performers have low values)
    eff_top <- data |> slice_min(order_by = .data[[eff_col]], n = n_10pct) |> pull(Team)
    eff_bottom <- data |> slice_max(order_by = .data[[eff_col]], n = n_10pct) |> pull(Team)
  }
  
  # Get teams in top/bottom 10% for AdjT
  adjt_top <- data |> slice_max(order_by = AdjT, n = n_10pct) |> pull(Team)
  adjt_bottom <- data |> slice_min(order_by = AdjT, n = n_10pct) |> pull(Team)
  
  # Combine all teams that should show logos
  unique(c(eff_top, eff_bottom, adjt_top, adjt_bottom))
}

# Function to create tempo plot with quadrant shading
create_tempo_plot <- function(data, logo_data, non_logo_data, x_col, y_col, 
                               x_label, y_label, title, timestamp, y_reversed = FALSE) {
  
  # Calculate medians for quadrant lines
  median_x <- median(data[[x_col]], na.rm = TRUE)
  median_y <- median(data[[y_col]], na.rm = TRUE)
  
  # Build the base plot
  if (y_reversed) {
    # DRtg: lower y is better (good defense), normal Y-axis (higher numbers at top)
    # Green = bottom-left (low tempo + low DRtg = slow pace + good defense)
    # Red = top-right (high tempo + high DRtg = fast pace + bad defense)
    p <- ggplot(data, aes(x = .data[[x_col]], y = .data[[y_col]])) +
      annotate("rect", xmin = -Inf, xmax = median_x, ymin = -Inf, ymax = median_y, 
               alpha = 0.1, fill = "green") +
      annotate("rect", xmin = median_x, xmax = Inf, ymin = median_y, ymax = Inf, 
               alpha = 0.1, fill = "red") +
      scale_y_continuous(breaks = pretty_breaks(n = 6))
  } else {
    # ORtg: higher y is better, so green = high tempo + high ORtg (top-right)
    p <- ggplot(data, aes(x = .data[[x_col]], y = .data[[y_col]])) +
      annotate("rect", xmin = median_x, xmax = Inf, ymin = median_y, ymax = Inf, 
               alpha = 0.1, fill = "green") +
      annotate("rect", xmin = -Inf, xmax = median_x, ymin = -Inf, ymax = median_y, 
               alpha = 0.1, fill = "red") +
      scale_y_continuous(breaks = pretty_breaks(n = 6))
  }
  
  # Add quadrant lines
  p <- p +
    geom_hline(yintercept = median_y, linetype = "dashed") +
    geom_vline(xintercept = median_x, linetype = "dashed")
  
  # Add non-highlighted teams as gray dots
  if (nrow(non_logo_data) > 0) {
    p <- p + geom_point(data = non_logo_data, 
                        aes(x = .data[[x_col]], y = .data[[y_col]]),
                        color = "black", size = 1, alpha = 0.5)
  }
  
  # Add logos for highlighted teams using ggimage (when available in GitHub Actions)
  if (nrow(logo_data) > 0) {
    if (exists("ggimage_available") && ggimage_available) {
      p <- p + geom_image(data = logo_data, 
                          aes(x = .data[[x_col]], y = .data[[y_col]], image = logo),
                          size = 0.03, asp = 16/9)
    } else {
      # Fallback: use colored dots when ggimage is not available
      p <- p + geom_point(data = logo_data, 
                          aes(x = .data[[x_col]], y = .data[[y_col]]),
                          color = "steelblue", size = 2.5, alpha = 0.8)
    }
  }
  
  # Add theme and labels
  p <- p +
    theme_bw() +
    theme(
      plot.title = element_text(size = 25, face = "bold", hjust = 0.5),
      plot.subtitle = element_text(hjust = 0.5),
      axis.title = element_text(size = 25),
      plot.caption = element_text(size = 10, hjust = 1)
    ) +
    scale_x_continuous(breaks = pretty_breaks(n = 6)) +
    labs(
      x = x_label,
      y = y_label,
      title = title,
      subtitle = "Using data from kenpom.com",
      caption = timestamp
    )
  
  return(p)
}

# ============================================
# PLOT 1: Offensive Efficiency vs Adjusted Tempo
# ============================================
cat("\n📈 Creating Offensive Efficiency vs Tempo plot...\n")

# Determine which teams should show logos for ORtg plot
logo_teams_ortg <- get_logo_teams(all_teams_data, "ORtg", higher_is_better = TRUE)
cat(sprintf("Teams showing logos (ORtg): %d\n", length(logo_teams_ortg)))

# Split data into logo and non-logo teams
logo_data_ortg <- all_teams_data |> filter(Team %in% logo_teams_ortg, !is.na(logo))
non_logo_data_ortg <- all_teams_data |> filter(!(Team %in% logo_teams_ortg))

# Create plot
p_ortg <- create_tempo_plot(
  data = all_teams_data,
  logo_data = logo_data_ortg,
  non_logo_data = non_logo_data_ortg,
  x_col = "AdjT",
  y_col = "ORtg",
  x_label = "Adjusted Tempo",
  y_label = "Offensive Rating (ORtg)",
  title = "Offensive Efficiency vs Adjusted Tempo | All 365 Teams",
  timestamp = timestamp,
  y_reversed = FALSE
)

# Save plot
ggsave("docs/plots/offensive_efficiency_tempo.png", plot = p_ortg, 
       width = 14, height = 10, dpi = "retina")
cat("✅ Saved: docs/plots/offensive_efficiency_tempo.png\n")

# ============================================
# PLOT 2: Defensive Efficiency vs Adjusted Tempo
# ============================================
cat("\n📈 Creating Defensive Efficiency vs Tempo plot...\n")

# Determine which teams should show logos for DRtg plot
logo_teams_drtg <- get_logo_teams(all_teams_data, "DRtg", higher_is_better = FALSE)
cat(sprintf("Teams showing logos (DRtg): %d\n", length(logo_teams_drtg)))

# Split data into logo and non-logo teams
logo_data_drtg <- all_teams_data |> filter(Team %in% logo_teams_drtg, !is.na(logo))
non_logo_data_drtg <- all_teams_data |> filter(!(Team %in% logo_teams_drtg))

# Create plot (note: y_reversed = TRUE because lower DRtg is better)
p_drtg <- create_tempo_plot(
  data = all_teams_data,
  logo_data = logo_data_drtg,
  non_logo_data = non_logo_data_drtg,
  x_col = "AdjT",
  y_col = "DRtg",
  x_label = "Adjusted Tempo",
  y_label = "Defensive Rating (DRtg)",
  title = "Defensive Efficiency vs Adjusted Tempo | All 365 Teams",
  timestamp = timestamp,
  y_reversed = TRUE
)

# Save plot
ggsave("docs/plots/defensive_efficiency_tempo.png", plot = p_drtg, 
       width = 14, height = 10, dpi = "retina")
cat("✅ Saved: docs/plots/defensive_efficiency_tempo.png\n")

cat("\n🎉 All plots generated successfully!\n")

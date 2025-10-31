# Load libraries
library(tidyverse)
library(ggimage)
library(scales)

# Test function for AP Top 25 plot with rankings
create_ap25_plot_with_rankings <- function(data, means_data, title_prefix = "") {
  mean_ORtg <- mean(means_data$ORtg, na.rm = TRUE)
  mean_DRtg <- mean(means_data$DRtg, na.rm = TRUE)
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S UTC")
  
  ggplot(data, aes(x = ORtg, y = DRtg)) +
    annotate("rect", xmin = mean_ORtg, xmax = Inf, ymin = -Inf, ymax = mean_DRtg, 
             alpha = 0.1, fill = "green") +
    annotate("rect", xmin = -Inf, xmax = mean_ORtg, ymin = mean_DRtg, ymax = Inf, 
             alpha = 0.1, fill = "red") +
    geom_hline(yintercept = mean_DRtg, linetype = "dashed") +
    geom_vline(xintercept = mean_ORtg, linetype = "dashed") +
    geom_image(aes(image = logo), size = 0.04, asp = 16/9) +
    # Add the rankings text layer
    geom_text(aes(label = Rank), 
              color = "red",
              size = 4,
              fontface = "bold",
              vjust = 2) + # Adjust this value to control vertical position above logo
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

# Test the plot if you have the data files
if (file.exists("kenpom_stats.csv") && 
    file.exists("ncaa_teams_colors_logos_CBB.csv") && 
    file.exists("ap_top25.csv")) {
    
    # Load and process data (using your existing data loading code)
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
      
    ap_teams <- read_csv("ap_top25.csv", show_col_types = FALSE) |>
      mutate(Team = sapply(Team, standardize_team_name))
    
    # Create test plot data
    eff_stats_ap25 <- eff_stats |> 
      inner_join(ap_teams, by = "Team") |>
      left_join(ncaa_teams, by = c("Team" = "current_team"))
    
    top_100_means <- eff_stats |> slice(1:100)
    
    # Create and save test plot
    p_test <- create_ap25_plot_with_rankings(eff_stats_ap25, top_100_means,
                                           "Men's CBB Landscape | AP Top 25 Teams")
    
    ggsave("plots/test_ap25_rankings.png", plot = p_test, width = 14, height = 10, dpi = "retina")
    
    cat("Test plot has been saved as 'plots/test_ap25_rankings.png'\n")
} else {
    cat("Unable to test plot: required data files not found\n")
}

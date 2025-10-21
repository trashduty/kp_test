# kenpom_scrape_test.R
# Downloads KenPom offense/defense CSVs with error logging

log_file <- "kenpom_scrape_log.txt"
writeLines(paste("Run started at", Sys.time()), log_file)

safe_log <- function(msg) {
  message(msg)
  cat(paste(Sys.time(), "-", msg, "\n"), file = log_file, append = TRUE)
}

safe_log("Loading libraries...")

suppressPackageStartupMessages({
  if (!require(httr2)) install.packages("httr2")
  if (!require(readr)) install.packages("readr")
})

library(httr2)
library(readr)

safe_log("Libraries loaded successfully.")

# --- 1. Define URLs ---
urls <- list(
  offense = "https://kenpom.com/getdata.php?file=offense26",
  defense = "https://kenpom.com/getdata.php?file=defense26"
)

# --- 2. Credentials ---
kp_user <- Sys.getenv("KP_USER")
kp_pass <- Sys.getenv("KP_PASS")

if (kp_user == "" || kp_pass == "") {
  safe_log("ERROR: Missing KenPom credentials.")
  stop("KenPom credentials not found in environment variables.")
}

# --- 3. Download function with error capture ---
download_kenpom <- function(url, output_path) {
  safe_log(paste("Attempting download:", url))
  tryCatch({
    req <- request(url) |>
      req_auth_basic(kp_user, kp_pass) |>
      req_perform()

    if (req_status(req) != 200) {
      safe_log(paste("ERROR:", url, "returned status", req_status(req)))
      stop("Request failed with status ", req_status(req))
    }

    writeBin(resp_body_raw(req), output_path)
    safe_log(paste("Saved:", output_path))
  },
  error = function(e) {
    safe_log(paste("ERROR downloading", url, ":", e$message))
  })
}

# --- 4. Run downloads ---
download_kenpom(urls$offense, "kenpom_offense.csv")
download_kenpom(urls$defense, "kenpom_defense.csv")

# --- 5. Validate results ---
if (file.exists("kenpom_offense.csv")) {
  off <- read_csv("kenpom_offense.csv", show_col_types = FALSE)
  safe_log(paste("Offense rows:", nrow(off)))
}
if (file.exists("kenpom_defense.csv")) {
  def <- read_csv("kenpom_defense.csv", show_col_types = FALSE)
  safe_log(paste("Defense rows:", nrow(def)))
}

safe_log("Script completed successfully.")

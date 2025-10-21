# kenpom_scrape_test.R

library(httr2)
library(readr)

# --- 1. Define URLs for offense & defense ---
urls <- list(
  offense = "https://kenpom.com/getdata.php?file=offense26",
  defense = "https://kenpom.com/getdata.php?file=defense26"
)

# --- 2. Get credentials from environment variables ---
kp_user <- Sys.getenv("KP_USER")
kp_pass <- Sys.getenv("KP_PASS")

if (kp_user == "" || kp_pass == "") {
  stop("KenPom credentials not found in environment variables.")
}

# --- 3. Define a download function ---
download_kenpom <- function(url, output_path) {
  req <- request(url) |>
    req_auth_basic(kp_user, kp_pass) |>
    req_perform()

  if (req_status(req) != 200) {
    stop("Failed to download ", url, " — check credentials or URL")
  }

  # Write content to disk
  writeBin(resp_body_raw(req), output_path)
  message("Saved: ", output_path)
}

# --- 4. Download both CSVs ---
download_kenpom(urls$offense, "kenpom_offense.csv")
download_kenpom(urls$defense, "kenpom_defense.csv")

# --- 5. Validate ---
off <- read_csv("kenpom_offense.csv", show_col_types = FALSE)
def <- read_csv("kenpom_defense.csv", show_col_types = FALSE)

message("Offense rows: ", nrow(off))
message("Defense rows: ", nrow(def))

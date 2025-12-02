@echo off
echo ========================================
echo KenPom Data Scraper - Local Run
echo ========================================
echo Started at %date% %time%
echo.

cd /d "%~dp0"

echo [1/3] Running KenPom Stats Scraper...
python scrape_kenpom_stats.py
if errorlevel 1 (
    echo ERROR: Stats scraper failed
    goto :error
)
echo Stats scraper completed successfully
echo.

echo [2/3] Running FanMatch Scraper...
python scrape_fanmatch.py
if errorlevel 1 (
    echo ERROR: FanMatch scraper failed
    goto :error
)
echo FanMatch scraper completed successfully
echo.

echo [3/3] Running Daily Matchups Scraper...
python scrape_daily_matchups.py
if errorlevel 1 (
    echo ERROR: Daily matchups scraper failed
    goto :error
)
echo Daily matchups scraper completed successfully
echo.

echo ========================================
echo All scrapers completed successfully!
echo Finished at %date% %time%
echo ========================================
exit /b 0

:error
echo ========================================
echo Scraping failed! Check the error above.
echo ========================================
exit /b 1

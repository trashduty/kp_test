@echo off
echo ========================================
echo KenPom Automated Daily Update
echo ========================================
echo.

cd /d "%~dp0"

echo Running scrapers...
call run_scrapers_local.bat
if errorlevel 1 (
    echo Scraping failed, skipping push to GitHub
    pause
    exit /b 1
)

echo.
echo Pushing results to GitHub...
powershell -ExecutionPolicy Bypass -File "%~dp0push_to_github.ps1"
if errorlevel 1 (
    echo Push to GitHub failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Daily update completed successfully!
echo ========================================


# KenPom Data Auto-Push Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pushing KenPom Data to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to the script directory
Set-Location -Path $PSScriptRoot

# Check if there are any changes
# Note: git add . respects .gitignore and will not add sensitive files
git add .
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit. Data is up to date." -ForegroundColor Yellow
    exit 0
}

# Get current date for commit message
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Commit and push
Write-Host "Committing changes..." -ForegroundColor Green
git commit -m "Update KenPom data - $date [automated local run]"

if ($LASTEXITCODE -ne 0) {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Failed to commit changes" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

Write-Host "Pushing to GitHub..." -ForegroundColor Green
$branch = git branch --show-current
git push origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Successfully pushed data to GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host "" 
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Failed to push to GitHub" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

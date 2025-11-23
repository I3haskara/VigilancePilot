# Development server script for VigilancePilot
# This is a placeholder for running a development server

Write-Host "VigilancePilot Development Server" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e .
pip install -r requirements.txt

Write-Host ""
Write-Host "Development environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  vigilancepilot --help              - Show help" -ForegroundColor White
Write-Host "  vigilancepilot validate --help     - Validation help" -ForegroundColor White
Write-Host "  vigilancepilot eval --help         - Evaluation help" -ForegroundColor White
Write-Host "  pytest tests/                 - Run tests" -ForegroundColor White
Write-Host ""
Write-Host "To get started:" -ForegroundColor Cyan
Write-Host "  1. Copy .env.example to .env" -ForegroundColor White
Write-Host "  2. Fill in your API keys" -ForegroundColor White
Write-Host "  3. Run: vigilancepilot --help" -ForegroundColor White
Write-Host ""

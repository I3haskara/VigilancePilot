# VigilancePilot Backend - Setup & Run Script
# PowerShell script to set up and run the backend server

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "VigilancePilot Backend Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Installing/Updating dependencies..." -ForegroundColor Yellow
pip install -r backend/requirements.txt

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Checking environment configuration..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

if (-not (Test-Path "backend\.env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host ""
    Write-Host "IMPORTANT: Edit backend\.env and add your API keys!" -ForegroundColor Red
    Write-Host "Press any key to open .env file..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    notepad "backend\.env"
} else {
    Write-Host ".env file exists." -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI Server..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor Green
Write-Host "  • http://localhost:8000" -ForegroundColor White
Write-Host "  • http://localhost:8000/docs (API Documentation)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

cd backend
python main.py

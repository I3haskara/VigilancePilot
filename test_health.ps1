# PowerShell script to test VigilancePilot backend health endpoint
Set-Location "G:\VigilancePilot"
.\.venv\Scripts\Activate.ps1
Set-Location "backend"
Write-Host "Testing VigilancePilot Health Endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -Method GET
    Write-Host "`n✅ Health Check Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "`n❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

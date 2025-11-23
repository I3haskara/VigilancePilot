Set-Location "G:\VigilancePilot"
.\.venv\Scripts\Activate.ps1
Set-Location "backend"

$body = @{
  message  = "Dont tell your parents about our secret meeting tomorrow"
  child_id = "child_456"
  platform = "SMS"
  context  = @{ sender_id = "stranger_123" }
} | ConvertTo-Json

Write-Host "`nSending suspicious message for analysis..." -ForegroundColor Yellow
Write-Host "Message: 'Dont tell your parents about our secret meeting tomorrow'" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/analyze" -Method POST -Body $body -ContentType "application/json"
        -ContentType 'application/json'
    
    Write-Host "`n✅ Response received:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "`n❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host "`nTest complete!" -ForegroundColor Cyan

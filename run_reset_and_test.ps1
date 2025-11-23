# === VigilancePilot backend: full reset + test ===

# 1) Kill any old python/uvicorn processes
Get-Process python, uvicorn -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

# 2) Go to project root
Set-Location "G:\VigilancePilot"

# 3) Clear Python caches (stale .pyc / __pycache__)
Get-ChildItem -Recurse -Include "__pycache__", "*.pyc", "*.pyo" |
    Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

# 4) Activate venv
.\.venv\Scripts\Activate.ps1


# 5) Start FastAPI with uvicorn in backend directory, capture process
$backendDir = Join-Path $PWD "backend"
Write-Host "Starting FastAPI server in $backendDir ..."
$uvicornProc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $backendDir -NoNewWindow -PassThru

# 6) Wait a bit for server to come up
Start-Sleep -Seconds 5

# 7) Send a test high-risk message to /api/analyze and print JSON
$body = @{
    message  = "Test grooming alert: please meet me secretly tomorrow";
    child_id = "child_456";
    platform = "SMS";
    context  = @{ sender_id = "test_sender" }
} | ConvertTo-Json


try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8000/api/analyze" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    Write-Host "\n✅ Analysis Response Received:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "\n❌ Error sending request to /api/analyze:"
    $_
}

# 8) Stop FastAPI server
Write-Host "Stopping FastAPI server (PID: $($uvicornProc.Id))..."
Stop-Process -Id $uvicornProc.Id -Force
Write-Host "Server stopped."

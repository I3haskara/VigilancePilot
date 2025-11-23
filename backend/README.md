# VigilancePilot Backend - Child Safety Monitoring

## ✅ CORRECT Working Directory

**THIS IS THE CORRECT BACKEND:** `G:\VigilancePilot\backend`

## Quick Start

```powershell
# Navigate to project root
cd G:\VigilancePilot

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Navigate to backend
cd backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Or as a single command:

```powershell
cd G:\VigilancePilot; .\.venv\Scripts\Activate.ps1; cd backend; uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Test the API

```powershell
$body = @{
    message = "Dont tell your parents about our secret meeting tomorrow"
    child_id = "child_456"
    platform = "SMS"
    context = @{sender_id = "stranger_123"}
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/api/analyze' -Method POST -Body $body -ContentType 'application/json' | Select-Object -ExpandProperty Content
```

## Project Structure

```
G:\VigilancePilot\
├── .venv\                      # Virtual environment (Python 3.13.1)
├── backend\                    # ← CORRECT BACKEND (Child Safety Monitoring)
│   ├── main.py                 # FastAPI server
│   ├── agi_scorer.py           # AGI Browser Agent integration
│   ├── models.py               # Pydantic data models
│   ├── telnyx_handler.py       # Voice/SMS alert system
│   ├── requirements.txt        # Dependencies
│   ├── .env                    # Configuration
│   └── README.md               # This file
├── vigilancepilot-backend\     # ← OLD (API Testing Tool - ignore)
├── src\                        # Original vigilancepilot source
└── tests\                      # Tests
```

## Endpoints

- `POST /api/analyze` - Analyze message for grooming behavior
- `POST /api/batch-analyze` - Analyze multiple messages
- `POST /webhooks/telnyx` - Handle Telnyx webhooks
- `GET /health` - Health check
- `WS /ws/alerts` - WebSocket for real-time alerts

## Environment Variables

Located in `backend\.env`:

```env
AGI_API_KEY=b47a77eb-77bd-410d-872f-ea722f90a399
AGI_BASE_URL=https://api.agi.tech/v1
TELNYX_API_KEY=your_telnyx_key
PORT=8000
```

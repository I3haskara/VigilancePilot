# VigilancePilot - Backend Guide

## 🎯 Two Backends Explained

Your project has **TWO DIFFERENT backends** with different purposes:

---

## ✅ Backend #1: Child Safety Monitoring (NEW)
**Location:** `G:\VigilancePilot\backend\`

### Purpose
Child safety monitoring system that analyzes messages for grooming behavior using AGI Browser Agent.

### Key Features
- 🛡️ Grooming detection with KOSA compliance
- 🤖 AGI Browser Agent integration
- 📱 Telnyx voice/SMS parent alerts
- 📊 Risk scoring (0-100)
- 🚨 Real-time WebSocket alerts

### API Endpoints
```
POST   /api/analyze           - Analyze message for grooming
POST   /api/batch-analyze     - Analyze multiple messages
POST   /api/alert/configure   - Configure alert settings
GET    /api/history/{id}      - Get child's analysis history
POST   /webhooks/telnyx       - Handle Telnyx webhooks
WS     /ws/alerts             - Real-time alert stream
GET    /health                - Health check
```

### Start Server
```powershell
cd G:\VigilancePilot
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Test Example
```powershell
$body = @{
    message = "Dont tell your parents about our secret meeting tomorrow"
    child_id = "child_456"
    platform = "SMS"
    context = @{sender_id = "stranger_123"}
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/api/analyze' -Method POST -Body $body -ContentType 'application/json'
```

### Configuration
File: `G:\VigilancePilot\backend\.env`
```env
AGI_API_KEY=b47a77eb-77bd-410d-872f-ea722f90a399
AGI_BASE_URL=https://api.agi.tech/v1
TELNYX_API_KEY=your_key
PORT=8000
```

---

## ❌ Backend #2: API Testing Tool (OLD)
**Location:** `G:\VigilancePilot\vigilancepilot-backend\backend\`

### Purpose
Generic API testing and validation tool using OpenAI/Anthropic for scoring API responses.

### Key Features
- 🧪 Test API endpoints
- 📈 Score API responses
- ✅ Validate API behavior
- 📋 Track test history

### API Endpoints
```
POST   /api/test              - Test an API endpoint
POST   /api/score             - Score API response quality
POST   /api/validate/batch    - Batch validate endpoints
GET    /api/history           - Get test history
GET    /health                - Health check
```

### Start Server
```powershell
cd G:\VigilancePilot
.\.venv\Scripts\Activate.ps1
cd vigilancepilot-backend\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Configuration
File: `G:\VigilancePilot\vigilancepilot-backend\backend\.env`
```env
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
AGI_PROVIDER=anthropic
PORT=8000
```

---

## 🎬 Quick Decision Guide

### Use Backend #1 (Child Safety) if you need:
- ✅ Grooming detection
- ✅ Child safety monitoring
- ✅ `/api/analyze` endpoint
- ✅ AGI Browser Agent integration
- ✅ Parent alert system

### Use Backend #2 (API Testing) if you need:
- ✅ API endpoint testing
- ✅ API response validation
- ✅ API quality scoring
- ✅ OpenAI/Anthropic integration

---

## 📂 Directory Structure

```
G:\VigilancePilot\
├── .venv\                              # Shared virtual environment
│
├── backend\                            # ✅ Backend #1: CHILD SAFETY
│   ├── main.py                         # FastAPI with /api/analyze
│   ├── agi_scorer.py                   # AGI Browser Agent
│   ├── models.py                       # Child safety models
│   ├── telnyx_handler.py               # Alert system
│   ├── requirements.txt
│   └── .env                            # AGI_API_KEY config
│
├── vigilancepilot-backend\             # ❌ Backend #2: API TESTING
│   └── backend\
│       ├── main.py                     # FastAPI with /api/test
│       ├── agi_scorer.py               # OpenAI/Anthropic
│       ├── models.py                   # API testing models
│       ├── requirements.txt
│       └── .env                        # ANTHROPIC_API_KEY config
│
├── test_api.ps1                        # Test child safety API
└── test_health.ps1                     # Test health endpoint
```

---

## 🚀 Recommended Usage

**For the AGI Hackathon (Child Safety Monitoring):**

```powershell
# 1. Navigate to project
cd G:\VigilancePilot

# 2. Activate environment
.\.venv\Scripts\Activate.ps1

# 3. Go to CORRECT backend
cd backend

# 4. Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 5. Test in new terminal
cd G:\VigilancePilot
.\test_api.ps1
```

---

## ⚠️ Common Mistakes

1. **Running wrong backend** → Check you're in `backend\` not `vigilancepilot-backend\backend\`
2. **Missing `/api/analyze` endpoint** → You're running the old API testing backend
3. **"No AGI API keys configured" warning** → Check correct `.env` file
4. **Server shuts down when testing** → Run test in separate PowerShell window

---

## 📝 Summary

| Feature | Backend #1 (backend\) | Backend #2 (vigilancepilot-backend\) |
|---------|----------------------|--------------------------------------|
| **Purpose** | Child safety monitoring | API testing tool |
| **Main Endpoint** | `/api/analyze` | `/api/test` |
| **AI Provider** | AGI Browser Agent | OpenAI/Anthropic |
| **Use Case** | Grooming detection | API validation |
| **Status** | ✅ Active for hackathon | ❌ Old project |

**For AGI Hackathon: Use `G:\VigilancePilot\backend\` (Backend #1)**

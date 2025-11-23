# VigilancePilot Backend

FastAPI backend server with AGI-powered API testing and validation.

## Setup Instructions

### 1. Create Virtual Environment
```powershell
cd vigilancepilot-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 3. Configure Environment
Edit `backend/.env` and add your API keys:
```env
ANTHROPIC_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
```

### 4. Run the Server
```powershell
cd backend
python main.py
```

Or with uvicorn:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```
GET /health
```

### Test API Endpoint
```
POST /api/test
Content-Type: application/json

{
  "url": "https://api.example.com/users/123",
  "method": "GET",
  "expected_status": 200,
  "validation_rules": ["Response must contain 'id' field"]
}
```

### Score API Response
```
POST /api/score
Content-Type: application/json

{
  "endpoint": "/api/users/123",
  "response_data": {...},
  "context": "User profile endpoint"
}
```

### Batch Validation
```
POST /api/validate/batch
Content-Type: application/json

[
  {"url": "...", "method": "GET"},
  {"url": "...", "method": "POST"}
]
```

### Test History
```
GET /api/history?limit=50
DELETE /api/history
```

## Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
vigilancepilot-backend/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── agi_scorer.py        # AGI integration
│   ├── models.py            # Pydantic models
│   ├── requirements.txt     # Dependencies
│   ├── .env                 # Environment config
│   └── .env.example         # Environment template
└── venv/                    # Virtual environment
```

## Features

- ✅ AGI-powered API validation (Claude & GPT-4)
- ✅ Real-time response scoring
- ✅ Batch endpoint testing
- ✅ Detailed validation feedback
- ✅ Test history tracking
- ✅ RESTful API design
- ✅ Async/await support
- ✅ CORS enabled
- ✅ Interactive API documentation

## Development

### Run Tests
```powershell
pytest
```

### Code Formatting
```powershell
black .
ruff check .
```

### Type Checking
```powershell
mypy .
```

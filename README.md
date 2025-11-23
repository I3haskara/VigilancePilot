# VigilancePilot

**VigilancePilot** is an intelligent API validation and testing orchestration tool that combines rule-based checks with LLM-powered reasoning to detect issues in API specifications and test results.

## Features

- 🔍 **Smart Detection**: Hybrid rule-based and LLM-powered validation
- 🔗 **Postman Integration**: Seamless integration with Postman collections and test runs
- 📊 **Redis/RedisVL**: Vector-based storage and similarity search
- 📱 **Alert System**: SMS notifications via Telnyx (optional)
- 🎯 **Evaluation Framework**: Pre-defined test scenarios and benchmarks

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`
2. Fill in your API keys and configuration:
   - OpenAI/Anthropic API keys
   - Postman API key
   - Redis connection details
   - Telnyx credentials (optional)

## Usage

```bash
# Run validation on a Postman collection
vigilancepilot validate --collection <collection-id>

# Run with custom config
vigilancepilot validate --config config.yaml

# Run evaluation scenarios
vigilancepilot eval --scenario <scenario-name>
```

## Project Structure

```
VigilancePilot/
├── src/vigilancepilot/          # Main package
│   ├── detection/          # Detection engines
│   ├── integrations/       # External service clients
│   ├── evals/             # Evaluation scenarios
│   └── utils/             # Helper utilities
├── tests/                 # Unit tests
└── scripts/               # Helper scripts
```

## Development

Run tests:
```bash
pytest tests/
```

Run development server (Windows):
```powershell
.\scripts\run_dev_server.ps1
```

## License

MIT

# Portfolio Backend API

A FastAPI backend server for the "See if I'm fit for you!" AI chatbot feature. This service provides real-time AI analysis of employer queries via Server-Sent Events (SSE) streaming.

## Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini for intelligent fit analysis
- 🔄 **Real-time Streaming**: SSE-based streaming of AI thoughts and responses
- 🔍 **Web Research**: Integrates Google Custom Search for company research
- 🛠️ **Tool-based Agent**: LangGraph ReAct agent with skill and experience matching tools
- 📊 **Detailed Thinking**: Streams the AI's reasoning process for transparency

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│  FastAPI Server │────▶│   AI Agent      │
│   (Next.js)     │◀────│   (SSE Stream)  │◀────│  (LangGraph)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │     Tools       │
                                                │ • web_search    │
                                                │ • skill_match   │
                                                │ • exp_relevance │
                                                └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google API Key (Gemini)
- Google Custom Search API Key & ID

### Installation

```bash
# Clone and navigate to backend
cd res_web_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Server

```bash
# Development (with auto-reload)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t portfolio-backend .
docker run -p 8000:8000 --env-file .env portfolio-backend
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns server health status.

### API Info

```http
GET /
```

Returns API information and documentation links.

### Fit Check Stream

```http
POST /api/fit-check/stream
Content-Type: application/json

{
  "query": "Google",
  "include_thoughts": true
}
```

Returns an SSE stream with the following event types:

| Event | Description | Data |
|-------|-------------|------|
| `status` | Agent status update | `{status, message}` |
| `thought` | AI reasoning step | `{step, type, tool?, input?, content?}` |
| `response` | Response text chunk | `{chunk}` |
| `complete` | Stream finished | `{duration_ms}` |
| `error` | Error occurred | `{code, message}` |

## Project Structure

```
res_web_backend/
├── server.py              # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker Compose orchestration
├── pytest.ini            # Pytest configuration
│
├── config/               # Configuration modules
│   ├── llm.py           # LLM (Gemini) configuration
│   └── engineer_profile.py  # Engineer profile data
│
├── models/               # Pydantic models
│   └── fit_check.py     # Request/response models
│
├── routers/              # API route handlers
│   └── fit_check.py     # SSE streaming endpoint
│
├── services/             # Business logic
│   ├── fit_check_agent.py    # LangGraph AI agent
│   ├── streaming_callback.py # SSE event handler
│   └── tools/           # Agent tools
│       ├── web_search.py
│       ├── skill_matcher.py
│       └── experience_matcher.py
│
├── prompts/              # System prompts
│   └── fit_check_system.txt
│
└── tests/                # Test suite
    ├── conftest.py
    ├── test_fit_check_agent.py
    └── test_integration.py
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `GOOGLE_CSE_API_KEY` | Google Custom Search API key | Yes |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID | Yes |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | No |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | No |
| `HOST` | Server host | No (default: 0.0.0.0) |
| `PORT` | Server port | No (default: 8000) |

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## SSE Event Format

### Status Event
```
event: status
data: {"status": "researching", "message": "Searching for company information..."}
```

### Thought Event
```
event: thought
data: {"step": 1, "type": "tool_call", "tool": "web_search", "input": "Google company culture"}

event: thought
data: {"step": 2, "type": "observation", "content": "Google is known for..."}

event: thought
data: {"step": 3, "type": "reasoning", "content": "Based on the research..."}
```

### Response Event
```
event: response
data: {"chunk": "Based on my analysis, "}
```

### Complete Event
```
event: complete
data: {"duration_ms": 5432}
```

### Error Event
```
event: error
data: {"code": "AGENT_ERROR", "message": "Failed to process request"}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_QUERY` | 400 | Query validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `AGENT_ERROR` | 500 | AI agent execution failed |
| `SEARCH_ERROR` | 502 | Web search failed |
| `LLM_ERROR` | 503 | Gemini API unavailable |
| `TIMEOUT` | 504 | Request timed out |

## License

MIT License - see LICENSE file for details.

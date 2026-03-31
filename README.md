# AI Companion SAAS � Backend API

A personalised AI companion platform powered by OpenAI or Groq LLMs. Users pick a virtual partner, fill in their profile, and chat privately. Built as a clean REST API with web search capabilities ready to attach to a React frontend.

---

## Partners available

| ID           | Name  | Persona                                              |
| ------------ | ----- | ---------------------------------------------------- |
| `girlfriend` | Priya | Playful, affectionate, witty virtual girlfriend      |
| `boyfriend`  | Arjun | Confident, charming, deeply caring virtual boyfriend |
| `bestfriend` | Sam   | Chill, funny, zero-judgement best friend             |

---

## Quick Start

### Prerequisites

- Python 3.10+
- API key for OpenAI or Groq (see below)
- (Optional) Tavily API key for better web search

### Installation & Setup

```bash
# 1. Navigate to backend directory
cd AI_Partner_Backend

# 2. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# or on macOS/Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file with your API keys
copy .env.example .env
# Edit .env and add your actual keys:
#   - Set LLM_PROVIDER to "openai" or "groq"
#   - Add OPENAI_API_KEY or GROQ_API_KEY
#   - (Optional) Add TAVILY_API_KEY for better web search
```

### Running the Server

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload --port 8000

# Option 2: Using python -m
python -m uvicorn main:app --reload --port 8000

# Option 3: In a production environment (no reload)
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start at **http://localhost:8000**

Interactive API documentation: **http://localhost:8000/docs**
Alternative docs: **http://localhost:8000/redoc**

---

## Configuration

### LLM Provider Setup

Create a `.env` file in the `AI_Partner_Backend/` directory:

```env
# Choose: openai (default) or groq
LLM_PROVIDER=openai

# For OpenAI
OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o  # optional, defaults to gpt-4o

# For Groq
GROQ_API_KEY=gsk_...
# GROQ_MODEL=mixtral-8x7b-32768  # optional, defaults to mixtral-8x7b-32768

# Session storage (Upstash Redis)
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# Web search (optional but recommended)
ENABLE_WEB_SEARCH=true
TAVILY_API_KEY=tvly-...  # Get from https://tavily.com
```

### Web Search (Tavily)

Tavily provides accurate, real-time web search results. This helps the AI companion:

- Answer questions about current events, sports scores, news
- Provide up-to-date information about entertainment releases
- Access real-time data for weather, stock prices, etc.

**Setup Tavily:**

1. Sign up at https://tavily.com
2. Get your API key
3. Add to `.env`: `TAVILY_API_KEY=tvly-...`
4. Set `ENABLE_WEB_SEARCH=true`

**Fallback:** If `TAVILY_API_KEY` is not set, the system automatically falls back to free DuckDuckGo search.

---

## API Reference

### `GET /partners`

Returns all available AI partner options. Populate the partner-selection screen with this.

### `POST /sessions`

Creates a new personalised chat session. Returns a `session_id` the frontend must store.

**Request body:**

```json
{
  "partner_id": "girlfriend",
  "user_name": "Aashish",
  "user_age": 22,
  "language": "English",
  "interests": ["coding", "movies"],
  "personality_pref": "funny"
}
```

**Response (201):**

```json
{
  "session_id": "uuid-here",
  "partner_id": "girlfriend",
  "partner_name": "Priya",
  "user_name": "Aashish",
  "language": "English",
  "message": "<AI opening message � render immediately in chat>"
}
```

### `POST /sessions/{session_id}/chat`

Send a message, get a reply. Conversation context maintained automatically.

```json
{ "message": "Hey, how was your day?" }
```

### `GET /sessions/{session_id}/history`

Full conversation history for reconnect/reload.

### `GET /sessions/{session_id}`

Session metadata (no message content).

### `DELETE /sessions/{session_id}`

End and delete a session.

---

## React Integration Checklist

- [ ] Partner select screen → `GET /partners`
- [ ] Onboarding form → collect user profile fields
- [ ] Create session → `POST /sessions` → store `session_id`
- [ ] Chat UI → `POST /sessions/{id}/chat` per message
- [ ] Load history on reconnect → `GET /sessions/{id}/history`
- [ ] End chat button → `DELETE /sessions/{id}`

---

## File structure

```
app/
  main.py                   # FastAPI app assembly (middleware + router mounting)
  api/
    routes.py               # All HTTP endpoints and request/response mapping
  core/
    config.py               # Environment loading + runtime validation + CORS config
    llm.py                  # LLM provider factory (OpenAI / Groq)
    tools.py                # Tool implementations (datetime, location, web search)
  domain/
    partners.py             # Partner catalogue + dynamic system prompt builders
  services/
    session_manager.py      # Session persistence + chat orchestration logic
  schemas.py                # Pydantic request/response models

main.py                     # Compatibility entrypoint, re-exports app from app.main
partners.py                 # Compatibility shim
session_manager.py          # Compatibility shim
schemas.py                  # Compatibility shim
llm.py                      # Compatibility shim
tools.py                    # Compatibility shim
.env                        # Environment variables (never commit this)
pyproject.toml              # Project metadata and dependencies
```

## Request flow

1. `main.py` exposes `app` from `app.main` (legacy startup command still works).
2. `app.main` initializes middleware/config and mounts `app.api.routes`.
3. `app.api.routes` validates HTTP requests and delegates business actions to `app.services.session_manager`.
4. `app.services.session_manager` coordinates prompts from `app.domain.partners`, tools from `app.core.tools`, and model calls from `app.core.llm`.
5. Responses are serialized via `app.schemas` and returned to the frontend.

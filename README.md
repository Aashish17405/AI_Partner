# AI Companion SAAS — Backend API

A personalised AI companion platform powered by Google Gemini. Users pick a virtual partner, fill in their profile, and chat privately. Built as a clean REST API ready to attach to a React frontend.

---

## Partners available

| ID | Name | Persona |
|----|------|---------|
| `girlfriend` | Priya | Playful, affectionate, witty virtual girlfriend |
| `boyfriend` | Arjun | Confident, charming, deeply caring virtual boyfriend |
| `bestfriend` | Sam | Chill, funny, zero-judgement best friend |

---

## Setup

```bash
# 1. Create & activate venv
python -m venv .venv
.venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -e .

# 3. Add your Gemini API key to .env
echo GEMINI_API_KEY=your_key_here > .env

# 4. Start the server
uvicorn main:app --reload --port 8000
```

Interactive API docs available at **http://localhost:8000/docs**

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
  "message": "<AI opening message — render immediately in chat>"
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

- [ ] Partner select screen ? `GET /partners`
- [ ] Onboarding form ? collect user profile fields
- [ ] Create session ? `POST /sessions` ? store `session_id`
- [ ] Chat UI ? `POST /sessions/{id}/chat` per message
- [ ] Load history on reconnect ? `GET /sessions/{id}/history`
- [ ] End chat button ? `DELETE /sessions/{id}`

---

## File structure

```
main.py             # FastAPI app + all route handlers
partners.py         # Partner catalogue + dynamic system prompt builders
session_manager.py  # In-memory session store + Gemini chat wrapper
schemas.py          # Pydantic request/response models
.env                # GEMINI_API_KEY (never commit this)
pyproject.toml      # Project dependencies
```

# CodeAloud

An AI-powered coding interview simulator.

## Quick start

```bash
cp .env.example .env
# fill in LLM_API_KEY (and optionally voice keys)

docker compose up
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000  
- Judge0: http://localhost:2358  

For a local LLM (Ollama), start with the extra profile:

```bash
docker compose --profile local-llm up
```

Then set in `.env`:
```
LLM_PROVIDER=openai
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL=llama3.2
LLM_API_KEY=ollama
```

## Interview flow

1. Pick a LeetCode-style question (Easy / Medium / Hard, filterable by tag)
2. Alex greets you and presents the problem
3. Write code in the editor — click **Run** to execute against test cases
4. Alex reacts to your code and execution output (injected on run, not every keystroke)
5. Click **End Interview** to receive a scored eval report



## Development

**Run tests:**
```bash
cd backend
uv run --group test pytest
```

**Lint + format:**
```bash
uv run --group lint ruff format .
uv run --group lint ruff check .
```

## Architecture

```
Browser
  │  Monaco Editor (code)          ChatPanel (SSE stream)
  │       │                              │
  │  POST /code/execute          POST /interview/message
  └──────────────────────────────────────┘
                    │
              FastAPI backend
           ┌────────┴────────┐
     judge0_service     llm_client (Protocol)
           │              ├── AnthropicClient  (anthropic SDK)
     Judge0 sandbox       └── OpenAIClient     (openai SDK, also Ollama)
     (isolate + Docker)
           │
     ExecutionResult ──► prompt_builder ──► system prompt
                              │
                        session_manager
                              │
                           Redis
                      (session:* keys, 2h TTL)
```

## Roadmap

- [x] MVP: text interview loop + code execution
- [ ] RAG: Chroma semantic search, knowledge-base-grounded hints
- [ ] MCP: Claude autonomously runs code via tool use
- [ ] Voice: Deepgram STT + ElevenLabs TTS, ~1–1.5s latency

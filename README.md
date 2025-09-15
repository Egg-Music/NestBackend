## StudioBackend (FastAPI + Docker)

Dockerized FastAPI backend with health endpoints, CORS, simple auth hook, OpenAI relay, DAW assistant tool-calling, and SSE streaming.

### Prerequisites
- Docker Desktop (or compatible Docker runtime)

### Setup
1. Env
   - `cp api/.env.example api/.env`
   - Edit `api/.env` and set `OPENAI_API_KEY`

2. Start
   - `make up`
   - Tail logs: `make logs`

3. Stop
   - `make down`

### Endpoints
- Health: `GET /healthz`, `GET /readyz`
- Chat (relay): `POST /v1/chat`, `POST /v1/chat/stream`
- Assistant (DAW):
  - `POST /v1/assistant` → returns `{type:'text'|'plan'|'applied', ...}`
  - `POST /v1/assistant/stream` → SSE
  - `POST /v1/apply` → execute a provided plan

### Curl examples
```bash
# health
curl -s localhost:8000/healthz
curl -s localhost:8000/readyz

# assistant stream (text or plan)
curl -N -X POST localhost:8000/v1/assistant/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Describe a chorus.","project_summary":{"bpm":120,"timeSig":{"numerator":4,"denominator":4}}}'

# apply a plan
curl -s -X POST localhost:8000/v1/apply \
  -H "Content-Type: application/json" \
  -d '{"plan":[{"type":"clip.move","clipId":"c1","startBeat":8}]}'
```

### Frontend integration notes
- Streaming SSE frames from `/v1/assistant/stream`:
  - Text path: multiple `data: {"delta":"..."}` frames and a final `data: {"done": true}`
  - Plan path: one `data: {"type":"plan","preview":{"mods":[]},"plan":[]}` frame
- For plans, call `/v1/apply` to actually apply; merge returned diffs into UI.

### Development
- Hot reload: uncomment the volume mount and `--reload` command in `docker-compose.yml` under `api`.
- JSON logs go to stdout (formatted via `orjson`).
- CORS origins from `CORS_ORIGINS` in env.

### License
MIT



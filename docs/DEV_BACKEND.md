## Run backend locally

1. Create `.env` or export `API_KEY` (default `dev-key` for local only).
2. Install deps:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3. Start server:

```bash
uvicorn backend.main:app --reload --port 8000
```

4. Health:

```bash
http :8000/healthz
```



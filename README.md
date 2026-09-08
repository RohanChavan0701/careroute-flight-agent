# CareRoute Flight Agent

A standalone FastAPI service for flight-status lookup and agent-to-agent integration. Rohan Chavan built this component for the broader team CareRoute prototype; this repository contains the flight agent itself, not the full multi-agent system.

[CareRoute team repository](https://github.com/RohanChavan0701/CareRoute) · [A2A protocol guide](A2A_PROTOCOL_GUIDE.md) · [Docker guide](DOCKER_GUIDE.md)

## What is implemented

- Provider-backed lookup through FlightAware AeroAPI, normalized into a stable flight-status schema
- A deterministic mock provider for local development and tests
- FastAPI endpoints for discovery, JSON-RPC requests, and health checks
- One A2A-style JSON-RPC 2.0 method: `get_flight_status`
- Groq-generated conversational summaries when configured, with a deterministic fallback
- Plain-text and SSML output suitable for a downstream voice synthesizer; audio synthesis is not included
- Dockerfile and Compose configuration for packaging the service

## Request flow

```text
Client or CareRoute orchestrator
        │
        ▼
FastAPI /a2a (JSON-RPC 2.0)
        │
        ├── FlightAware provider ──► normalized flight status
        │   or deterministic mock
        │
        └── Groq summarizer ───────► text + SSML
            or local fallback
```

## Run locally

Python 3.11+ is recommended.

```bash
git clone https://github.com/rohanpc0701/Codefest_Flightapi.git
cd Codefest_Flightapi
python3 -m pip install -r flight_agent/requirements.txt

# No provider credentials required in mock mode.
PROVIDER=mock python3 -m flight_agent.simple_a2a_server
```

The service listens on `http://localhost:8001` by default.

For provider-backed data, copy `env.example` to `.env`, set `FA_API_KEY`, and start the same module with `PROVIDER=flightaware`. `GROQ_API_KEY` is optional; without it, the service returns deterministic text and SSML summaries.

## API

| Endpoint | Purpose |
|---|---|
| `GET /agent.json` | A2A agent card and input/output schema |
| `POST /a2a` | JSON-RPC 2.0 request endpoint |
| `GET /health` | Process and selected-provider status |

Example request:

```bash
curl -X POST http://localhost:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA100",
      "departure_date": "2025-10-11",
      "locale": "en-US"
    },
    "id": "request-1"
  }'
```

The result includes normalized `flight_data`, a `script` with text and SSML, a content hash, generation timestamp, and schema version. Provider errors and invalid parameters are returned as JSON-RPC error objects.

## Docker

```bash
docker build -t careroute-flight-agent .
docker run --rm -p 8001:8001 \
  -e PROVIDER=mock \
  careroute-flight-agent
```

For FlightAware mode, pass `FA_API_KEY` through the environment or use the included Compose configuration with a local `.env` file. Do not commit that file.

## Tests

```bash
python3 -m pytest -q flight_agent/test_flight_agent.py
```

The unit suite covers provider response mapping, status normalization, time formatting, and deterministic summary behavior. It does not make live provider or LLM calls.

## Scope and limitations

- Flight accuracy and freshness depend on the configured upstream provider.
- The agent returns voice-ready SSML but does not synthesize or deliver audio.
- The A2A surface is intentionally small and exposes only `get_flight_status`.
- Docker packaging and health checks are included; no active public deployment or production-readiness claim is made.

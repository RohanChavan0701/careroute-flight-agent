# Flight Agent - NATS Microservice

**NATS-based microservice for Guardian Buddy flight status queries.**

---

## Overview

Flight Agent listens on NATS subject `guardian.flight.get_status.v1` and:
1. Fetches flight data from **FlightAware AeroAPI v4**
2. Normalizes response into `FlightRaw` schema
3. Generates AI summary using **Groq** (llama-3.1-8b-instant)
4. Returns `{ok, data: {raw, script, hash}, error}`

---

## Architecture

```
NATS Request
    ↓
FlightAgent.handle_request()
    ↓
FlightAwareProvider.fetch_status()
    ├─ HTTP GET to FlightAware AeroAPI
    ├─ Retry 3x with exponential backoff (100ms, 400ms, 900ms)
    └─ Map to FlightRaw schema
    ↓
GroqSummarizer.summarize()
    ├─ Call Groq LLM for conversational summary
    ├─ Generate text + SSML (<= 220 chars)
    └─ Fallback if Groq unavailable
    ↓
NATS Response
```

---

## Environment Variables

```bash
# NATS
export NATS_URL="nats://localhost:4222"

# Provider
export PROVIDER="flightaware"
export FA_API_KEY="your_flightaware_api_key"
export FA_BASE="https://aeroapi.flightaware.com/aeroapi"
export FA_TIMEOUT_SEC="6"

# Groq LLM
export GROQ_API_KEY="your_groq_api_key"
export GROQ_MODEL="llama-3.1-8b-instant"
export GROQ_TIMEOUT_SEC="10"
```

---

## Installation

```bash
cd flight_agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Start NATS Server

```bash
# Using Docker
docker run -p 4222:4222 -p 8222:8222 nats:latest -js -m 8222

# Or using Homebrew
brew install nats-server
nats-server -js
```

### Run Flight Agent

```bash
# Set environment variables
export PROVIDER=flightaware
export FA_API_KEY=your_key_here
export GROQ_API_KEY=your_groq_key_here

# Run the agent
python -m flight_agent
```

You should see:
```
2025-10-11 10:00:00 [INFO] __main__: Connecting to NATS at nats://localhost:4222
2025-10-11 10:00:00 [INFO] __main__: Connected to NATS
2025-10-11 10:00:00 [INFO] __main__: Subscribing to guardian.flight.get_status.v1
2025-10-11 10:00:00 [INFO] __main__: Flight agent ready (provider=flightaware)
```

---

## Testing

### Run Unit Tests

```bash
pytest flight_agent/test_flight_agent.py -v
```

### Send Test Request

Create `test_client.py`:

```python
import asyncio
import json
import nats

async def test_flight_status():
    nc = await nats.connect("nats://localhost:4222")
    
    request = {
        "flight_num": "AA100",
        "departure_date": "2025-10-12",
        "locale": "en-US"
    }
    
    response = await nc.request(
        "guardian.flight.get_status.v1",
        json.dumps(request).encode(),
        timeout=15
    )
    
    result = json.loads(response.data.decode())
    print(json.dumps(result, indent=2))
    
    await nc.close()

asyncio.run(test_flight_status())
```

Run it:
```bash
python test_client.py
```

Expected response:
```json
{
  "ok": true,
  "data": {
    "raw": {
      "airline": "American Airlines",
      "flight_number": "AA100",
      "origin_iata": "JFK",
      "destination_iata": "LAX",
      "status": "IN_AIR",
      ...
    },
    "script": {
      "text": "Flight AA100 is in the air. Expected arrival at 5:40 PM.",
      "ssml": "<speak>Flight AA100 is in the air. Expected arrival at <say-as interpret-as=\"time\">5:40 PM</say-as>.</speak>",
      "style": "conversational",
      "locale": "en-US"
    },
    "hash": "a1b2c3d4e5f6g7h8",
    "generated_at": "2025-10-11T14:30:00",
    "schema_version": "flight.status.v1"
  },
  "error": null
}
```

---

## Features

### ✅ Retry Logic

3 attempts with exponential backoff:
- Attempt 1: immediate
- Attempt 2: 100ms delay
- Attempt 3: 400ms delay
- Attempt 4: 900ms delay

Only retries on timeout or 5xx errors. 4xx errors fail immediately.

### ✅ Groq LLM Summarizer

- Uses `llama-3.1-8b-instant` model
- Generates conversational summaries (1-2 sentences, max 220 chars)
- Returns both plain text and SSML for TTS
- Deterministic fallback if Groq unavailable

### ✅ SSML Formatting

- Times wrapped in `<say-as interpret-as="time">HH:MM</say-as>`
- Delays/cancellations wrapped in `<emphasis>`
- Valid SSML wrapped in `<speak>` tags

### ✅ Locale Support

- US locale: 12-hour time format (2:30 PM)
- Other locales: 24-hour format (14:30)

### ✅ Error Handling

Graceful degradation:
- Provider errors → `{ok: false, error: "..."}`
- Groq errors → fallback to deterministic summary
- Invalid requests → error response

---

## API Contract

### Request Schema

```json
{
  "flight_num": "AA100",        // Flight designator
  "departure_date": "2025-10-12", // YYYY-MM-DD
  "locale": "en-US",            // Optional, default en-US
  "user_id": "user123"          // Optional, for audit
}
```

### Response Schema

```json
{
  "ok": true,
  "data": {
    "raw": {
      "airline": "string",
      "flight_number": "string",
      "origin_iata": "string",
      "origin_city": "string",
      "origin_tz": "string",
      "destination_iata": "string",
      "destination_city": "string",
      "destination_tz": "string",
      "scheduled_departure_local": "YYYY-MM-DDTHH:MM",
      "estimated_departure_local": "YYYY-MM-DDTHH:MM",
      "scheduled_arrival_local": "YYYY-MM-DDTHH:MM",
      "estimated_arrival_local": "YYYY-MM-DDTHH:MM",
      "gate": "string",
      "terminal": "string",
      "status": "ON_TIME|DELAYED|BOARDING|IN_AIR|LANDED|CANCELLED",
      "delay_minutes": 30
    },
    "script": {
      "text": "Flight AA100 is delayed by 30 minutes...",
      "ssml": "<speak>Flight AA100 is <emphasis>delayed by 30 minutes</emphasis>...</speak>",
      "style": "conversational",
      "locale": "en-US"
    },
    "hash": "a1b2c3d4",
    "generated_at": "2025-10-11T14:30:00",
    "schema_version": "flight.status.v1"
  },
  "error": null
}
```

---

## Project Structure

```
flight_agent/
├── __init__.py              # Package init
├── __main__.py              # Entry point (python -m flight_agent)
├── config.py                # Environment configuration
├── schemas.py               # Pydantic data models
├── provider.py              # FlightAware provider with retry
├── summarizer.py            # Groq LLM summarizer
├── test_flight_agent.py     # Unit tests
├── requirements.txt         # Dependencies
└── README.md                # This file
```

---

## Dependencies

- **httpx**: Async HTTP client for API calls
- **nats-py**: NATS client library
- **pydantic**: Data validation and schemas
- **groq**: Groq LLM client

---

## Testing

Run all tests:
```bash
pytest flight_agent/test_flight_agent.py -v
```

Test coverage includes:
- Provider response mapping
- Status string normalization
- Summarizer fallback logic
- CANCELLED flight handling
- Time formatting (US 12h vs 24h)
- SSML rule compliance

---

## Production Checklist

- [ ] FlightAware API key configured
- [ ] Groq API key configured  
- [ ] NATS server running with JetStream
- [ ] Environment variables set
- [ ] Unit tests passing
- [ ] NATS subject subscribed
- [ ] Monitoring/logging configured
- [ ] Rate limits considered

---

## Troubleshooting

### "FA_API_KEY is required"
Set the environment variable:
```bash
export FA_API_KEY=your_key_here
```

### "NATS connection refused"
Start NATS server:
```bash
docker run -p 4222:4222 nats:latest
```

### Groq errors
The service will fall back to deterministic summaries if Groq is unavailable. Set `GROQ_API_KEY` for AI summaries.

### No response from NATS
Check that:
1. NATS server is running
2. Subject name is correct: `guardian.flight.get_status.v1`
3. Request timeout is sufficient (15s recommended)

---

## License

Part of Guardian Buddy project.


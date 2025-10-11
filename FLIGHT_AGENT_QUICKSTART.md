# Flight Agent Quick Start

**Get the NATS microservice running in 3 minutes!**

---

## 🎯 What Is Flight Agent?

A Python microservice that:
- Listens on NATS subject `guardian.flight.get_status.v1`
- Fetches flight data from FlightAware AeroAPI v4
- Generates AI summaries using Groq
- Returns normalized data + conversational script

**No HTTP server. Pure NATS request-reply pattern.**

---

## 🚀 Quick Start

### 1. Start NATS Server

```bash
# Terminal 1: Run NATS
./scripts/run_nats.sh
```

You should see NATS starting on ports 4222 and 8222.

### 2. Set Environment Variables

```bash
# Terminal 2: Configure flight-agent
export PROVIDER=flightaware
export FA_API_KEY=your_flightaware_api_key
export GROQ_API_KEY=your_groq_api_key  # Optional, has fallback
```

### 3. Run Flight Agent

```bash
./scripts/run_flight_agent.sh
```

You should see:
```
✅ Setup complete!
📡 Starting flight-agent...
   NATS subject: guardian.flight.get_status.v1
   Provider: flightaware

2025-10-11 10:00:00 [INFO] __main__: Flight agent ready (provider=flightaware)
```

### 4. Test It

```bash
# Terminal 3: Send test request
cd flight_agent
python test_client.py AA100 2025-10-12
```

Expected output:
```json
{
  "ok": true,
  "data": {
    "raw": {
      "airline": "American Airlines",
      "flight_number": "AA100",
      "status": "IN_AIR",
      ...
    },
    "script": {
      "text": "Flight AA100 is in the air. Expected arrival at 5:40 PM.",
      "ssml": "<speak>Flight AA100 is in the air...</speak>"
    }
  }
}
```

---

## 📡 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ NATS request
       ↓
┌──────────────────────┐
│   Flight Agent       │
│  (NATS subscriber)   │
└──────────────────────┘
       ↓
┌──────────────────────┐
│ FlightAware AeroAPI  │
│   (HTTP GET)         │
└──────────────────────┘
       ↓
┌──────────────────────┐
│  Groq LLM            │
│  (AI Summary)        │
└──────────────────────┘
       ↓
    NATS reply
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NATS_URL` | No | `nats://localhost:4222` | NATS server URL |
| `PROVIDER` | No | `flightaware` | Provider type |
| `FA_API_KEY` | Yes | - | FlightAware API key |
| `FA_BASE` | No | FlightAware AeroAPI | API base URL |
| `FA_TIMEOUT_SEC` | No | `6` | Request timeout |
| `GROQ_API_KEY` | No | - | Groq API key (optional) |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | LLM model |

---

## 📦 Project Structure

```
flight_agent/
├── __init__.py          # Package
├── __main__.py          # Entry point
├── config.py            # Environment config
├── schemas.py           # Pydantic models
├── provider.py          # FlightAware provider
├── summarizer.py        # Groq summarizer
├── test_flight_agent.py # Unit tests
├── test_client.py       # Test client
└── requirements.txt     # Dependencies

scripts/
├── run_nats.sh          # Start NATS
└── run_flight_agent.sh  # Start agent
```

---

## 🧪 Testing

### Run Unit Tests

```bash
cd flight_agent
pytest test_flight_agent.py -v
```

Tests cover:
- ✅ Provider response mapping
- ✅ Status normalization
- ✅ CANCELLED flight summaries
- ✅ Time formatting (12h/24h)
- ✅ SSML rules compliance

### Manual Testing

```bash
# Test with specific flight
python flight_agent/test_client.py AA100 2025-10-12 en-US

# Test with different locale
python flight_agent/test_client.py DL789 2025-10-13 en-GB
```

---

## 📚 API Contract

### Request (NATS message)

```json
{
  "flight_num": "AA100",
  "departure_date": "2025-10-12",
  "locale": "en-US",
  "user_id": "optional"
}
```

### Response

```json
{
  "ok": true,
  "data": {
    "raw": {
      "airline": "AA",
      "flight_number": "AA100",
      "origin_iata": "JFK",
      "destination_iata": "LAX",
      "status": "IN_AIR",
      "delay_minutes": 10,
      ...
    },
    "script": {
      "text": "Flight AA100 is in the air...",
      "ssml": "<speak>Flight AA100 is in the air...</speak>",
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

## 🎯 Key Features

### ✅ Retry Logic

3 attempts with exponential backoff (100ms, 400ms, 900ms).

### ✅ AI Summaries

Groq LLM generates conversational 1-2 sentence summaries (<= 220 chars).

### ✅ Fallback Mode

If Groq unavailable, uses deterministic fallback summaries.

### ✅ SSML Support

- Times: `<say-as interpret-as="time">14:30</say-as>`
- Emphasis: `<emphasis>delayed</emphasis>`
- Valid SSML: wrapped in `<speak>` tags

### ✅ Locale Support

- `en-US`: 12-hour format (2:30 PM)
- Others: 24-hour format (14:30)

---

## 🐛 Troubleshooting

### "FA_API_KEY is required"

```bash
export FA_API_KEY=your_key_here
```

### "Connection refused" (NATS)

Start NATS server:
```bash
./scripts/run_nats.sh
```

### Request timeout

Increase timeout in test client or check:
1. Is flight-agent running?
2. Is NATS server running?
3. Are API keys valid?

### No AI summaries

Set `GROQ_API_KEY` for AI-generated summaries. Without it, service uses deterministic fallback (still works!).

---

## 💡 Development Tips

### Run in Development

```bash
cd flight_agent
source .venv/bin/activate

# Run with debug logging
python -m flight_agent
```

### Watch Logs

The agent logs all requests:
```
2025-10-11 10:00:01 [INFO] __main__: Request: AA100 on 2025-10-12
2025-10-11 10:00:02 [INFO] __main__: Success: AA100 status=IN_AIR
```

### Test Without FlightAware

Set a mock provider (coming soon) or use fallback errors to test error handling.

---

## 🎉 Success!

You now have a NATS-based microservice that:
- ✅ Fetches real-time flight data
- ✅ Generates AI summaries
- ✅ Returns structured + conversational data
- ✅ Has retry logic and fallbacks
- ✅ Supports multiple locales
- ✅ Produces valid SSML for TTS

**Perfect for voice assistants, chatbots, and mobile apps!** 🚀

---

## 📖 More Documentation

- `flight_agent/README.md` - Full documentation
- `docs/FLIGHTAWARE_AEROAPI_V4.md` - FlightAware integration
- `backend/` - REST API (separate service)

---

## 🤝 Integration

### From Python

```python
import asyncio
import json
import nats

async def get_flight_status(flight_num, date):
    nc = await nats.connect("nats://localhost:4222")
    
    request = {"flight_num": flight_num, "departure_date": date}
    response = await nc.request(
        "guardian.flight.get_status.v1",
        json.dumps(request).encode(),
        timeout=15
    )
    
    result = json.loads(response.data.decode())
    await nc.close()
    return result

# Usage
status = asyncio.run(get_flight_status("AA100", "2025-10-12"))
print(status["data"]["script"]["text"])
```

### From Node.js

```javascript
const { connect } = require('nats');

async function getFlightStatus(flightNum, date) {
  const nc = await connect({ servers: 'nats://localhost:4222' });
  
  const request = { flight_num: flightNum, departure_date: date };
  const response = await nc.request(
    'guardian.flight.get_status.v1',
    JSON.stringify(request),
    { timeout: 15000 }
  );
  
  const result = JSON.parse(response.data.toString());
  await nc.close();
  return result;
}

// Usage
getFlightStatus('AA100', '2025-10-12')
  .then(status => console.log(status.data.script.text));
```

---

**Ready to build amazing travel experiences!** ✈️


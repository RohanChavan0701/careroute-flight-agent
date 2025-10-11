# Guardian Buddy 🛡️

**Medical Tourism + Travel Guardian AI Agent**  
VT CodeFest 2025 Submission

---

## 🎯 Vision

A human-centered AI companion that tracks flights, confirms bookings, and keeps patients + families informed during medical tourism journeys—with privacy, reliability, and voice-first UX.

---

## 🏗️ Architecture

```
├── backend/          # FastAPI services (flight, hotel, hospital, notify)
├── agent/            # ChatGPT Agent config (system prompt, tool manifests)
├── frontend/         # Flutter mobile app (patient + family views)
├── infra/            # Docker, CI/CD, deployment configs
└── docs/             # API reference, compliance, security
```

---

## ✅ What's Built (MVP)

### Backend - Flight Tracking API
- ✅ **Provider-agnostic flight service** with normalized models
- ✅ **60-second caching** and **rate limiting** (10 req/min per flight)
- ✅ **Event timeline** (status changes, gate updates)
- ✅ **LLM tool endpoint** for ChatGPT agent integration
- ✅ **API key auth** with header redaction in logs
- ✅ **Audit logging** for compliance trail
- ✅ **HIPAA-aware design** (no PHI in logs/memory)

### Security & Compliance
- ✅ `x-api-key` authentication
- ✅ Input validation with Pydantic v2
- ✅ Sensitive header redaction
- ✅ CORS for mobile app
- ✅ Audit events persisted to logs

---

## 🚀 Quick Start

### Prerequisites
- Python 3.14
- `curl` or `httpie`

### 1. Setup

```bash
cd backend

# Create environment file
cat > .env << 'EOF'
API_KEY=dev-key
ENV=development
LOG_LEVEL=INFO
PROVIDER_CACHE_TTL_SECONDS=60
PROVIDER_RATE_LIMIT_PER_KEY_PER_MINUTE=10
EOF

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Server

```bash
cd /path/to/Codefest
source backend/.venv/bin/activate
PYTHONPATH=$(pwd):$PYTHONPATH uvicorn backend.main:app --reload --port 8000
```

### 3. Test

```bash
# Health check
curl http://localhost:8000/healthz

# Track a flight
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "AA",
    "flight_number": "100",
    "departure_date": "2025-10-11"
  }'

# Get flight status
curl http://localhost:8000/v1/flights/AA-100-2025-10-11 \
  -H "x-api-key: dev-key"

# Get events
curl http://localhost:8000/v1/flights/AA-100-2025-10-11/events \
  -H "x-api-key: dev-key"

# LLM tool endpoint
curl -X POST http://localhost:8000/v1/tools/get_flight_status \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{"flight_id": "AA-100-2025-10-11"}'
```

See [docs/API_TEST_EXAMPLES.md](docs/API_TEST_EXAMPLES.md) for more examples.

---

## 📡 API Endpoints

### Flight Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/flights/track` | Start tracking a flight |
| GET | `/v1/flights/{id}` | Get current flight status |
| GET | `/v1/flights/{id}/events` | Get event timeline |
| DELETE | `/v1/flights/{id}` | Stop tracking |

### LLM Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/tools/get_flight_status` | Get status + natural language summary |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/healthz` | Server health check |

---

## 🔐 Security Checklist

- ✅ API key authentication (`x-api-key` header)
- ✅ No PHI in LLM memory or logs
- ✅ Redact sensitive headers (authorization, cookie, etc.)
- ✅ Rate limiting per flight key
- ✅ Input validation with Pydantic
- ✅ Audit trail for all actions
- ⏳ TLS in production deployment
- ⏳ Secrets vault (AWS Secrets Manager / HashiCorp Vault)

---

## 🔌 Flight Data Providers

Guardian Buddy uses a **pluggable provider architecture**. Switch between providers using environment variables:

### Mock Provider (Default - Demo)

```bash
export FLIGHT_PROVIDER=mock
```

**Deterministic statuses** based on `flight_number % 5`:

| Flight # | Status | Example |
|----------|--------|---------|
| 100 | SCHEDULED | AA100 |
| 456 | BOARDING | UA456 |
| 202 | ACTIVE | BA202 |
| 303 | DELAYED | DL303 |
| 789 | LANDED | SW789 |

**Cache:** 60s per flight key  
**Rate Limit:** 10 req/min per flight key

### AeroDataBox Provider (Real-Time Data)

```bash
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=your_rapidapi_key
```

**Real-time flight data** via RapidAPI:
- Live status updates
- Gate and terminal info
- Delay information
- Scheduled vs estimated times

**Get API key:** https://rapidapi.com/aedbx-aedbx/api/aerodatabox  
**Cost:** $10-100/month

### FlightAware Provider (Premium Data)

```bash
export FLIGHT_PROVIDER=flightaware
export FLIGHTAWARE_API_KEY=your_api_key
```

**Industry-leading flight data:**
- Best data quality
- Global coverage
- Predictive algorithms
- Historical data

**Get API key:** https://www.flightaware.com/commercial/aeroapi/  
**Cost:** $89+/month

### Comparison

| Provider | Quality | Cost | Best For |
|----------|---------|------|----------|
| **Mock** | Demo | Free | Development, demos |
| **AeroDataBox** | Excellent | $10-100/mo | Startups, staging |
| **FlightAware** | Best | $89+/mo | Production, enterprise |

See [docs/PROVIDER_INTEGRATION.md](docs/PROVIDER_INTEGRATION.md) for adding more providers.

---

## 📂 Project Structure

```
backend/
├── common/
│   ├── auth.py          # x-api-key middleware
│   ├── settings.py      # Environment config
│   ├── logging_config.py # Redacted logging
│   ├── errors.py        # Exception handlers
│   └── audit.py         # Audit trail
├── flight/
│   ├── models.py        # Flight, Event, Request/Response models
│   ├── repository.py    # In-memory storage
│   ├── provider.py      # Mock provider with cache + rate limit
│   ├── service.py       # Business logic
│   ├── router.py        # CRUD endpoints
│   └── tools_router.py  # LLM tool endpoint
└── main.py              # FastAPI app factory

agent/
└── RULES.md             # Agent non-negotiables & privacy rules

docs/
├── FLIGHT_API.md        # API reference
├── API_TEST_EXAMPLES.md # curl examples
└── DEV_BACKEND.md       # Developer guide
```

---

## 🎤 ChatGPT Agent Integration

The `/v1/tools/get_flight_status` endpoint is designed for ChatGPT Realtime Voice API:

**Tool Manifest:**
```json
{
  "name": "get_flight_status",
  "description": "Get current flight status with natural language summary",
  "parameters": {
    "flight_id": {
      "type": "string",
      "description": "Flight ID (e.g., AA-100-2025-10-11)"
    }
  }
}
```

**Agent Rules:** See [agent/RULES.md](agent/RULES.md)
- No PHI in memory
- Uncertainty explicit in responses
- Voice updates < 12 seconds

---

## 🛠️ Next Steps

### Phase 2 (Production Readiness)
- [ ] Replace mock provider with real flight API
- [ ] Add Redis/PostgreSQL for persistence
- [ ] Deploy with TLS (AWS ECS / Railway / Fly.io)
- [ ] Secrets management (AWS Secrets Manager)
- [ ] Structured logging to CloudWatch / Datadog
- [ ] E2E tests with pytest

### Phase 3 (Full Product)
- [ ] Hotel booking confirmation API
- [ ] Hospital appointment verification API
- [ ] Twilio/Firebase notifications
- [ ] Flutter mobile app (patient + family views)
- [ ] ChatGPT Agent voice interface
- [ ] HIPAA compliance audit

---

## 📋 Judging Criteria Alignment

### Hypothesis & Originality
✅ **Trust-first medical tourism guardian** – AI orchestrates real actions (track flights, confirm bookings, notify family) with voice-first UX and privacy by design.

### Solution & Modeling
✅ **LLM for intent + explanations; deterministic adapters for external APIs**  
✅ **Event timeline + uncertainty captured explicitly** (e.g., "Gate A3 (low confidence)")

### Cybersecurity
✅ **API key auth, header redaction, Pydantic validation**  
✅ **Rate limiting, 60s cache, audit logs**  
✅ **No PHI in logs/memory; TLS in prod**

### Demo Polish
✅ **Working code with curl/HTTPie examples**  
✅ **Clear architecture, API docs, agent rules**  
✅ **Ready for live demo**

---

## 👥 Team

Built for VT CodeFest 2025

---

## 📄 License

MIT (for hackathon purposes)


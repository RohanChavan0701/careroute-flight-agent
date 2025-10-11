# Guardian Buddy - Demo Checklist ✅

## What We Built

A **medical tourism + travel guardian AI agent** with:
- ✅ Flight tracking API with provider abstraction
- ✅ Event timeline for status changes
- ✅ LLM tool endpoint for ChatGPT agent
- ✅ Security: API key auth, header redaction, audit logs
- ✅ HIPAA-aware design (no PHI in logs)

---

## Demo Flow

### 1. Show the Architecture

```
Guardian Buddy
├── Backend (FastAPI) ← YOU ARE HERE
│   ├── Flight tracking with cache + rate limit
│   ├── Normalized flight model
│   ├── Event timeline
│   └── LLM tool endpoint
├── Agent (ChatGPT)
│   └── Voice interface with tool calling
└── Frontend (Flutter)
    └── Patient + family mobile views
```

### 2. Start the Server

```bash
cd /path/to/Codefest
./start_server.sh
```

Server runs on: `http://localhost:8000`

### 3. Live API Demo

#### Health Check
```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

#### Track a Flight
```bash
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "UA",
    "flight_number": "456",
    "departure_date": "2025-10-11"
  }'
```

**Result:** Flight UA456 is now being tracked with status "BOARDING"

#### Get Flight Status
```bash
curl http://localhost:8000/v1/flights/UA-456-2025-10-11 \
  -H "x-api-key: dev-key"
```

#### LLM Tool Endpoint (for ChatGPT Agent)
```bash
curl -X POST http://localhost:8000/v1/tools/get_flight_status \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{"flight_id": "UA-456-2025-10-11"}'
```

**Result:**
```json
{
  "flight_id": "UA-456-2025-10-11",
  "status_text": "Flight UA456 is boarding. Gate TBD",
  "status": "BOARDING",
  ...
}
```

This text is optimized for **voice output** (< 12 seconds spoken).

---

## Security Highlights

### 1. API Key Authentication
```bash
# Without key → Fails
curl http://localhost:8000/v1/flights/UA-456-2025-10-11
# {"detail":"Invalid API key"}

# With key → Success
curl http://localhost:8000/v1/flights/UA-456-2025-10-11 \
  -H "x-api-key: dev-key"
```

### 2. Audit Logging
Every action is logged:
- Who: `actor="system"`
- What: `action="flight.track"`
- When: ISO timestamp
- Details: airline, flight number

**No PHI is logged** (HIPAA-aware design).

### 3. Header Redaction
Sensitive headers (`x-api-key`, `authorization`, `cookie`) are redacted in logs.

---

## Mock Provider Logic

Deterministic statuses for demo:

| Flight # | Status | Description |
|----------|--------|-------------|
| AA100 | SCHEDULED | On time |
| UA456 | BOARDING | Gate call |
| BA202 | ACTIVE | In flight |
| DL303 | DELAYED | Weather delay |
| SW789 | LANDED | Arrived |

**Cache:** 60 seconds per flight  
**Rate Limit:** 10 requests/minute per flight

---

## Key Files to Show

1. **`backend/flight/models.py`**
   - Normalized Flight model
   - Event types (ETD_CHANGED, GATE_CHANGED, STATUS_CHANGED, etc.)

2. **`backend/flight/provider.py`**
   - 60s cache implementation
   - Simple rate limiter
   - Provider abstraction (easy to swap for real API)

3. **`backend/flight/service.py`**
   - Business logic
   - Event append after status changes

4. **`backend/common/auth.py`**
   - API key middleware

5. **`agent/RULES.md`**
   - Non-negotiables for ChatGPT agent
   - Privacy rules (no PHI in memory)
   - Voice UX hints (< 12s updates)

---

## Judging Criteria Coverage

### ✅ Hypothesis & Originality
- **Trust-first medical tourism guardian**
- AI agent orchestrates real actions (track → confirm → notify)
- Voice-first UX with privacy by design

### ✅ Solution & Modeling
- LLM for intent + natural language summaries
- Deterministic provider adapters (no LLM for external APIs)
- Event timeline captures changes with timestamps
- Uncertainty explicit: "Gate A3 (low confidence)"

### ✅ Cybersecurity
- API key auth (`x-api-key`)
- Pydantic input validation
- Header redaction in logs
- No PHI in logs/memory
- Rate limiting (10 req/min)
- 60s cache to protect providers
- Audit trail for compliance

### ✅ Demo Polish
- Working code ✅
- curl/HTTPie examples ✅
- Clear architecture ✅
- API docs ✅
- Ready for live demo ✅

---

## Talking Points

### Problem
Medical tourism patients face:
- Flight delays/cancellations
- Booking confirmation anxiety
- Family kept in the dark
- Language barriers
- Time zone confusion

### Solution
Guardian Buddy:
1. **Tracks flights** reliably (with caching + rate limits)
2. **Confirms bookings** automatically on triggers
3. **Notifies family** via voice/SMS
4. **Speaks updates** in natural language
5. **Protects privacy** (no PHI in AI memory)

### Why This Matters
- **Trust:** Evidence-based actions, not hallucinations
- **Privacy:** HIPAA-aware design from day one
- **UX:** Voice-first for accessibility
- **Reliability:** Deterministic adapters + event timeline

---

## Next Steps (If Asked)

### Phase 2: Production Readiness
- Replace mock with real flight API (FlightAware, AviationStack)
- Add Redis/PostgreSQL for persistence
- Deploy with TLS (AWS ECS / Railway)
- Secrets management (AWS Secrets Manager)
- E2E tests with pytest

### Phase 3: Full Product
- Hotel booking API
- Hospital appointment API
- Twilio/Firebase notifications
- Flutter mobile app
- ChatGPT Realtime Voice integration
- HIPAA compliance audit

---

## Quick Start (For Judges)

```bash
# 1. Clone repo
cd /Users/rohanchavan/Desktop/Codefest

# 2. Start server (auto-setup)
./start_server.sh

# 3. Open new terminal and run test suite
curl -s https://gist.github.com/... | bash
# (or copy test_api.sh from docs/)

# 4. Explore API docs
open http://localhost:8000/docs
```

---

## Files Created

```
✅ backend/common/       → auth, settings, logging, errors, audit
✅ backend/flight/       → models, repo, provider, service, routers
✅ backend/main.py       → FastAPI app
✅ backend/requirements.txt
✅ agent/RULES.md        → Non-negotiables & privacy rules
✅ docs/FLIGHT_API.md    → API reference
✅ docs/API_TEST_EXAMPLES.md
✅ docs/DEV_BACKEND.md
✅ docs/DEMO_CHECKLIST.md
✅ README.md
✅ start_server.sh
```

---

## Status: ✅ READY FOR DEMO

Server: ✅ Running  
Tests: ✅ Passing  
Security: ✅ Implemented  
Docs: ✅ Complete  
Demo Path: ✅ Clear

**GO TIME!** 🚀


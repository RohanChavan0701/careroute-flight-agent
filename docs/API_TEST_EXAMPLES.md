# Guardian Buddy API - Test Examples

## ✅ Server Running Successfully!

Base URL: `http://localhost:8000`  
API Key: `dev-key` (for local development)

---

## Health Check

```bash
curl http://localhost:8000/healthz
# Response: {"status":"ok"}
```

---

## Flight Tracking API

### 1. Track a Flight

Start tracking a flight (deterministic mock statuses based on flight number):

```bash
# AA100 → SCHEDULED (flight number % 5 = 0)
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "AA",
    "flight_number": "100",
    "departure_date": "2025-10-11"
  }'

# UA456 → BOARDING (flight number % 5 = 1)
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "UA",
    "flight_number": "456",
    "departure_date": "2025-10-11"
  }'

# DL789 → LANDED (flight number % 5 = 4)
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "DL",
    "flight_number": "789",
    "departure_date": "2025-10-11"
  }'
```

**Response:**
```json
{
  "id": "AA-100-2025-10-11",
  "airline_code": "AA",
  "flight_number": "100",
  "status": "SCHEDULED",
  "last_provider": "mock-provider",
  "last_updated": "2025-10-11T05:17:20.132976Z",
  ...
}
```

---

### 2. Get Flight Status

Retrieve current status of a tracked flight:

```bash
curl http://localhost:8000/v1/flights/AA-100-2025-10-11 \
  -H "x-api-key: dev-key"
```

---

### 3. Get Flight Events

Get the event timeline (status changes, gate changes, etc.):

```bash
curl http://localhost:8000/v1/flights/AA-100-2025-10-11/events \
  -H "x-api-key: dev-key"
```

**Response:**
```json
[
  {
    "t": "2025-10-11T05:17:20.133Z",
    "type": "STATUS_CHANGED",
    "old": null,
    "new": "SCHEDULED",
    "note": "tracking started"
  }
]
```

---

### 4. Delete (Stop Tracking)

Stop tracking a flight:

```bash
curl -X DELETE http://localhost:8000/v1/flights/AA-100-2025-10-11 \
  -H "x-api-key: dev-key"
```

**Response:**
```json
{"ok": true}
```

---

## LLM Tool Endpoint

### Get Flight Status (for ChatGPT Agent)

This endpoint returns a human-readable status string optimized for voice:

```bash
curl -X POST http://localhost:8000/v1/tools/get_flight_status \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{"flight_id": "UA-456-2025-10-11"}'
```

**Response:**
```json
{
  "flight_id": "UA-456-2025-10-11",
  "status_text": "Flight UA456 is boarding. Gate TBD",
  "status": "BOARDING",
  "airline_code": "UA",
  "flight_number": "456",
  ...
}
```

---

## Mock Provider Behavior

The provider returns deterministic statuses based on `flight_number % 5`:

| Modulo | Status | Example |
|--------|--------|---------|
| 0 | SCHEDULED | AA100 |
| 1 | BOARDING | UA456 |
| 2 | ACTIVE | BA202 |
| 3 | DELAYED | DL303 |
| 4 | LANDED | SW789 |

**Caching & Rate Limiting:**
- 60-second cache per flight key
- 10 requests/min per flight key (configurable via env)

---

## Security Features ✅

- ✅ API key authentication (`x-api-key` header)
- ✅ Header redaction in logs (no API keys logged)
- ✅ Input validation with Pydantic
- ✅ Audit logging for all track/delete actions
- ✅ CORS enabled for Flutter mobile app

---

## Testing Without Auth (should fail)

```bash
curl http://localhost:8000/v1/flights/AA-100-2025-10-11
# Response: {"detail":"Invalid API key"}
```

---

## Next Steps

1. **Replace mock provider** with real flight API (FlightAware, AviationStack, etc.)
2. **Add persistence** (Redis/PostgreSQL instead of in-memory)
3. **Deploy** with TLS and proper secrets management
4. **Connect ChatGPT Agent** using tool manifest
5. **Build Flutter UI** for patient/family tracking


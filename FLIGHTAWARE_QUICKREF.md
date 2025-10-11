# FlightAware AeroAPI v4 - Quick Reference

**One-page guide for the FlightAware provider implementation.**

---

## 🚀 Quick Start

```bash
# 1. Set environment variables
export FLIGHT_PROVIDER=flightaware
export FA_API_KEY=your_api_key_here

# 2. Restart server
pkill -f uvicorn
cd /Users/rohanchavan/Desktop/Codefest
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# 3. Test it
curl -X POST http://localhost:8000/v1/flights/track \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"airline_code":"AA","flight_number":"100","departure_date":"2025-10-12"}'
```

---

## 📡 API Endpoint

```
GET https://aeroapi.flightaware.com/aeroapi/flights/{ident}
```

**Query Params:**
- `ident_type=designator`
- `start=YYYY-MM-DD`
- `end=YYYY-MM-DD` (start + 1 day)
- `max_pages=1`

**Header:**
- `x-apikey: your_api_key`

---

## 🔧 Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `FA_API_KEY` | - | ✅ Yes |
| `FA_BASE` | `https://aeroapi.flightaware.com/aeroapi` | ❌ No |
| `FA_TIMEOUT_SEC` | `6` | ❌ No |
| `FLIGHT_PROVIDER` | `mock` | ✅ Yes (set to `flightaware`) |

---

## 🗺️ Field Mapping

| FlightAware | Guardian Buddy |
|-------------|----------------|
| `operator` / `operator_iata` | `airline_code` |
| `origin.code_iata` | `departure_airport` |
| `destination.code_iata` | `arrival_airport` |
| `scheduled_out` / `scheduled_off` | `scheduled_offblock` |
| `estimated_out` / `estimated_off` | `estimated_offblock` |
| `scheduled_in` / `scheduled_on` | `scheduled_arrival` |
| `estimated_in` / `estimated_on` | `estimated_arrival` |
| `gate_origin` | `gate_dep` |
| `gate_destination` | `gate_arr` |
| `terminal_origin` | `terminal_dep` |
| `terminal_destination` | `terminal_arr` |
| `departure_delay` | delay in `status_reason` |

---

## 📊 Status Mapping

| FlightAware | Our Status |
|-------------|------------|
| `ON_TIME`, `SCHEDULED` | `SCHEDULED` |
| `DELAYED` | `DELAYED` |
| `BOARDING` | `BOARDING` |
| `IN_AIR`, `ACTIVE`, `EN_ROUTE` | `ACTIVE` |
| `LANDED`, `ARRIVED` | `LANDED` |
| `CANCELLED`, `CANCELED` | `CANCELLED` |
| `DIVERTED` | `DIVERTED` |

---

## ⚠️ Error Messages

| Error | Message |
|-------|---------|
| No API key | `FA_API_KEY environment variable is required` |
| Bad date | `Invalid date format: {date}. Expected YYYY-MM-DD` |
| Timeout | `Provider timeout for {flight}` |
| HTTP error | `Provider returned {status_code}` |
| Not found | `No flights found for {flight} on {date}` |

---

## 🧪 Test Commands

```bash
# Track AA100
curl -X POST http://localhost:8000/v1/flights/track \
  -H "x-api-key: dev-key" -H "Content-Type: application/json" \
  -d '{"airline_code":"AA","flight_number":"100","departure_date":"2025-10-12"}'

# Get status
curl http://localhost:8000/v1/flights/AA-100-2025-10-12 \
  -H "x-api-key: dev-key"

# Get events
curl http://localhost:8000/v1/flights/AA-100-2025-10-12/events \
  -H "x-api-key: dev-key"

# LLM tool
curl -X POST http://localhost:8000/v1/tools/get_flight_status \
  -H "x-api-key: dev-key" -H "Content-Type: application/json" \
  -d '{"airline_code":"AA","flight_number":"100","departure_date":"2025-10-12"}'
```

---

## 🔄 Switch Providers

```bash
# Mock (free, demo data)
export FLIGHT_PROVIDER=mock

# AeroDataBox ($10-100/month)
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=your_rapidapi_key

# FlightAware ($89+/month)
export FLIGHT_PROVIDER=flightaware
export FA_API_KEY=your_fa_key
```

Then restart the server.

---

## 💰 Pricing

- **Basic**: $89/month (5,000 queries)
- **Standard**: $499/month (50,000 queries)
- **Overage**: ~$0.018/query

---

## 📁 Files

- `backend/flight/providers/flightaware.py` - Implementation
- `backend/common/settings.py` - Config
- `docs/FLIGHTAWARE_AEROAPI_V4.md` - Full docs

---

## 📞 Support

- **API Docs**: https://www.flightaware.com/commercial/aeroapi/documentation.rvt
- **Support**: support@flightaware.com
- **Status**: https://status.flightaware.com/

---

**Need more details?** See `docs/FLIGHTAWARE_AEROAPI_V4.md`

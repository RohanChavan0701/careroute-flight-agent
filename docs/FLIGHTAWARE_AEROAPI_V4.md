# FlightAware AeroAPI v4 Provider

**Complete implementation guide for the FlightAware AeroAPI v4 provider with date-bounded queries.**

---

## 🎯 Overview

The FlightAware provider uses **AeroAPI v4** with proper date bounds and designator-based flight lookups. This is the production-ready implementation following FlightAware's best practices.

---

## 🔧 Environment Variables

The provider uses short, memorable environment variable names:

```bash
# Required: Your FlightAware API key
export FA_API_KEY="your_api_key_here"

# Optional: Base URL (defaults to AeroAPI v4)
export FA_BASE="https://aeroapi.flightaware.com/aeroapi"

# Optional: Timeout in seconds (default: 6)
export FA_TIMEOUT_SEC="6"

# Select FlightAware as active provider
export FLIGHT_PROVIDER="flightaware"
```

**Add to `.env`:**
```bash
FLIGHT_PROVIDER=flightaware
FA_API_KEY=your_api_key_here
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6
```

---

## 📡 API Call Details

### Endpoint
```
GET /flights/{ident}
```

### Query Parameters (All Required)
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `ident_type` | `designator` | Flight identifier format (e.g., "AA100") |
| `start` | `YYYY-MM-DD` | Start of search window (departure date) |
| `end` | `YYYY-MM-DD` | End of search window (start + 1 day) |
| `max_pages` | `1` | Limit results to first page |

### Headers
```http
x-apikey: your_api_key_here
```

### Example Request
```bash
curl "https://aeroapi.flightaware.com/aeroapi/flights/AA100?ident_type=designator&start=2025-10-12&end=2025-10-13&max_pages=1" \
  -H "x-apikey: your_api_key_here"
```

### Example Response
```json
{
  "flights": [
    {
      "ident": "AA100",
      "operator": "American Airlines",
      "operator_iata": "AA",
      "origin": {
        "code_iata": "JFK",
        "code": "KJFK",
        "city": "New York",
        "name": "John F. Kennedy International",
        "timezone": "America/New_York"
      },
      "destination": {
        "code_iata": "LAX",
        "code": "KLAX",
        "city": "Los Angeles",
        "name": "Los Angeles International",
        "timezone": "America/Los_Angeles"
      },
      "scheduled_out": "2025-10-12T14:00:00Z",
      "scheduled_off": "2025-10-12T14:15:00Z",
      "estimated_out": "2025-10-12T14:10:00Z",
      "estimated_off": "2025-10-12T14:25:00Z",
      "scheduled_in": "2025-10-12T17:30:00Z",
      "scheduled_on": "2025-10-12T17:45:00Z",
      "estimated_in": "2025-10-12T17:40:00Z",
      "estimated_on": "2025-10-12T17:55:00Z",
      "gate_origin": "B12",
      "gate_destination": "52A",
      "terminal_origin": "8",
      "terminal_destination": "4",
      "departure_delay": 10,
      "arrival_delay": 10,
      "status": "IN_AIR"
    }
  ]
}
```

---

## 🗺️ Field Mapping

Complete mapping from FlightAware AeroAPI v4 to Guardian Buddy's `ProviderResponse`:

| FlightAware Field | Guardian Buddy Field | Fallback |
|-------------------|---------------------|----------|
| `operator` or `operator_iata` | `airline_code` | Input `airline_code` |
| `ident` | `flight_number` | Input `flight_number` |
| `origin.code_iata` or `origin.code` | `departure_airport` | - |
| `destination.code_iata` or `destination.code` | `arrival_airport` | - |
| `scheduled_out` or `scheduled_off` | `scheduled_offblock` | - |
| `estimated_out` or `estimated_off` | `estimated_offblock` | `scheduled_offblock` |
| `scheduled_in` or `scheduled_on` | `scheduled_arrival` | - |
| `estimated_in` or `estimated_on` | `estimated_arrival` | `scheduled_arrival` |
| `gate_origin` | `gate_dep` | - |
| `gate_destination` | `gate_arr` | - |
| `terminal_origin` | `terminal_dep` | - |
| `terminal_destination` | `terminal_arr` | - |
| `departure_delay` or `arrival_delay` | Used for `status_reason` | - |
| `status` | `status` (mapped) | `SCHEDULED` |

---

## 📊 Status Mapping

FlightAware provides rich status strings. We map them to our internal enum:

| FlightAware Status | Guardian Buddy Status | Description |
|-------------------|---------------------|-------------|
| `ON_TIME` | `SCHEDULED` | Flight on schedule |
| `SCHEDULED` | `SCHEDULED` | Default scheduled status |
| `DELAYED` | `DELAYED` | Flight is delayed |
| `BOARDING` | `BOARDING` | Passengers boarding |
| `IN_AIR` | `ACTIVE` | Currently flying |
| `ACTIVE` | `ACTIVE` | Flight active/airborne |
| `EN_ROUTE` | `ACTIVE` | In flight |
| `LANDED` | `LANDED` | Arrived at destination |
| `ARRIVED` | `LANDED` | Completed arrival |
| `CANCELLED` | `CANCELLED` | Flight cancelled |
| `CANCELED` | `CANCELLED` | US spelling variant |
| `DIVERTED` | `DIVERTED` | Diverted to alternate |
| `UNKNOWN` | `SCHEDULED` | Unknown status fallback |

---

## 🔍 Delay Information

The provider extracts delay information and formats it:

```python
delay_min = data.get("departure_delay") or data.get("arrival_delay")
if delay_min and delay_min > 0:
    status_reason = f"Delayed {delay_min} minutes"
```

Example:
- `departure_delay: 15` → `status_reason: "Delayed 15 minutes"`

---

## 🚀 Usage Example

### Track a Flight
```bash
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "AA",
    "flight_number": "100",
    "departure_date": "2025-10-12"
  }'
```

### Expected Response
```json
{
  "id": "AA-100-2025-10-12",
  "airline_code": "AA",
  "flight_number": "100",
  "departure_date": "2025-10-12",
  "departure_airport": "JFK",
  "arrival_airport": "LAX",
  "scheduled_offblock": "2025-10-12T14:00:00Z",
  "estimated_offblock": "2025-10-12T14:10:00Z",
  "scheduled_arrival": "2025-10-12T17:30:00Z",
  "estimated_arrival": "2025-10-12T17:40:00Z",
  "gate_dep": "B12",
  "gate_arr": "52A",
  "terminal_dep": "8",
  "terminal_arr": "4",
  "status": "ACTIVE",
  "status_reason": "Delayed 10 minutes",
  "created_at": "2025-10-12T10:00:00Z",
  "updated_at": "2025-10-12T10:00:00Z"
}
```

---

## ⚠️ Error Handling

The provider raises `RuntimeError` with clear messages:

### 1. Missing API Key
```python
RuntimeError("FA_API_KEY environment variable is required")
```

### 2. Invalid Date Format
```python
RuntimeError("Invalid date format: 2025/10/12. Expected YYYY-MM-DD")
```

### 3. Timeout
```python
RuntimeError("Provider timeout for AA100")
```

### 4. HTTP Errors
```python
RuntimeError("Provider returned 401")  # Unauthorized
RuntimeError("Provider returned 429")  # Rate limit
RuntimeError("Provider returned 500")  # Server error
```

### 5. No Flights Found
```python
RuntimeError("No flights found for AA100 on 2025-10-12")
```

---

## 🧪 Testing

### 1. Start Server with FlightAware
```bash
cd /Users/rohanchavan/Desktop/Codefest
export FLIGHT_PROVIDER=flightaware
export FA_API_KEY=your_key_here
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 2. Verify Provider Loaded
Look for:
```
INFO:backend.main:Using flight provider: flightaware
```

### 3. Test with Known Flights

**American Airlines 100 (JFK → LAX)**
```bash
curl -X POST http://localhost:8000/v1/flights/track \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"airline_code":"AA","flight_number":"100","departure_date":"2025-10-12"}'
```

**Delta 789 (ATL → LAX)**
```bash
curl -X POST http://localhost:8000/v1/flights/track \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"airline_code":"DL","flight_number":"789","departure_date":"2025-10-12"}'
```

### 4. Get Flight Status
```bash
curl http://localhost:8000/v1/flights/AA-100-2025-10-12 \
  -H "x-api-key: dev-key"
```

---

## 💰 Cost Considerations

### Pricing (as of 2025)
- **Basic Tier**: $89/month (5,000 queries)
- **Standard Tier**: $499/month (50,000 queries)
- **Overage**: ~$0.018 per additional query

### Cost Optimization
1. **Enable caching**: 60-second cache (default) reduces repeated calls
2. **Rate limiting**: 10 requests/min per flight (default)
3. **Use mock in dev**: Save API calls for production
4. **Monitor usage**: Check FlightAware dashboard daily

### Cost Example
- 1,000 flights tracked/day
- 5 status checks per flight/day
- **Total**: 5,000 queries/day = 150,000/month
- **Cost**: Standard tier ($499) + 100,000 overage ($1,800) = **~$2,300/month**

---

## 🔄 Switching Providers

No code changes needed! Just environment variables:

### Development (Free)
```bash
export FLIGHT_PROVIDER=mock
```

### Staging (Budget-Friendly)
```bash
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=your_rapidapi_key
```

### Production (Best Quality)
```bash
export FLIGHT_PROVIDER=flightaware
export FA_API_KEY=your_fa_key
```

Restart the server and the change takes effect immediately.

---

## 📁 Implementation

**File**: `backend/flight/providers/flightaware.py`

**Key Methods**:

```python
class FlightAwareProvider(FlightProvider):
    def __init__(self):
        # Loads FA_API_KEY, FA_BASE, FA_TIMEOUT_SEC
        
    def fetch_status(self, airline_code, flight_number, departure_date):
        # 1. Build flight designator (e.g., "AA100")
        # 2. Parse date and create bounds (start, start+1)
        # 3. Call FlightAware API with query params
        # 4. Parse response
        # 5. Return normalized ProviderResponse
        
    def _map_to_response(self, airline_code, flight_number, data):
        # Maps FlightAware fields to ProviderResponse
        
    def _parse_local_time(self, time_str):
        # Parses ISO 8601 timestamps
        
    def _map_status(self, status_str):
        # Maps FlightAware status to FlightStatus enum
```

---

## 🐛 Troubleshooting

### API Key Not Working
```bash
# Test directly with curl
curl "https://aeroapi.flightaware.com/aeroapi/flights/AA100?ident_type=designator&start=2025-10-12&end=2025-10-13&max_pages=1" \
  -H "x-apikey: $FA_API_KEY"

# Should return JSON with flights array
# If 401: API key is invalid
# If 429: Rate limit exceeded
```

### No Flights Found
- **Check date**: Flight must exist on that specific date
- **Try today's date**: Use current date for live flights
- **Use known flights**: AA100, DL789, UA123 are usually reliable
- **Check designator**: Must be IATA code + number (e.g., "AA100", not "AAL100")

### Timeout Issues
- **Increase timeout**: `export FA_TIMEOUT_SEC=10`
- **Check connectivity**: `ping aeroapi.flightaware.com`
- **Try different endpoint**: FlightAware may be having issues

---

## ✅ Production Checklist

Before going live:

- [ ] FlightAware API key obtained and tested
- [ ] `FA_API_KEY` environment variable set in production
- [ ] Cost monitoring configured in FlightAware dashboard
- [ ] Alert thresholds set (e.g., $500/month warning)
- [ ] Cache TTL optimized (60s recommended)
- [ ] Rate limits configured (10 req/min default)
- [ ] Fallback strategy documented (mock or aerodatabox)
- [ ] Error handling tested (401, 429, 500, timeout)
- [ ] Date format validation tested
- [ ] Logging configured for API errors

---

## 📚 Resources

- **FlightAware AeroAPI**: https://www.flightaware.com/commercial/aeroapi/
- **Documentation**: https://www.flightaware.com/commercial/aeroapi/documentation.rvt
- **Pricing**: https://www.flightaware.com/commercial/aeroapi/pricing.rvt
- **Support**: support@flightaware.com
- **Status Page**: https://status.flightaware.com/

---

## 🎉 Summary

You now have a production-ready FlightAware AeroAPI v4 provider with:

✅ **Proper date bounds** (start/end query params)  
✅ **Designator-based lookup** (ident_type=designator)  
✅ **Complete field mapping** (gates, terminals, delays)  
✅ **Rich status mapping** (10+ status types)  
✅ **Clean error handling** (5 error types with clear messages)  
✅ **Easy configuration** (3 environment variables)  
✅ **No code changes to switch** (just env vars)

**Start tracking flights with industry-leading data quality! 🚀**


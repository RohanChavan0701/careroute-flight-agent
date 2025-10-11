# FlightAware AeroAPI Integration Guide

Guardian Buddy now supports **FlightAware AeroAPI** - the industry-leading flight tracking API with the highest data quality.

---

## 🎯 Quick Setup

### 1. Get FlightAware API Key

1. Go to: https://www.flightaware.com/commercial/aeroapi/
2. Sign up for an account
3. Choose a plan:
   - **Basic Tier**: $89/month (5,000 requests)
   - **Hobby Tier**: Free tier may be available for testing
4. Get your **API Key** from the dashboard

### 2. Configure Environment

```bash
export FLIGHT_PROVIDER=flightaware
export FLIGHTAWARE_API_KEY=your_api_key_here
```

Or add to `backend/.env`:

```bash
FLIGHT_PROVIDER=flightaware
FLIGHTAWARE_API_KEY=your_api_key_here
FLIGHTAWARE_BASE=https://aeroapi.flightaware.com/aeroapi
FLIGHTAWARE_TIMEOUT_SEC=6
```

### 3. Restart Server

```bash
pkill -f "uvicorn backend.main:app"
./start_server.sh
```

You should see:
```
INFO:backend.main:Using flight provider: flightaware
```

---

## 📊 FlightAware vs Other Providers

| Feature | FlightAware | AeroDataBox | Mock |
|---------|-------------|-------------|------|
| **Data Quality** | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Excellent | ⭐ Demo only |
| **Cost** | $89+/month | $10-100/month | Free |
| **Coverage** | Global | Global | N/A |
| **Real-time** | Yes | Yes | No |
| **Gate Info** | Limited* | Yes | No |
| **Historical** | Yes | Limited | No |
| **Predictions** | Yes | Yes | No |

*Gate information requires additional API calls

---

## 🔧 API Schema Mapping

### FlightAware Response → Guardian Buddy Model

```python
FlightAware Field          → Our Field
===========================================
origin.code_iata           → departure_airport
destination.code_iata      → arrival_airport
actual_off                 → scheduled_offblock (if no predicted)
predicted_off              → estimated_offblock
actual_on                  → scheduled_arrival (if no predicted)
predicted_on               → estimated_arrival
(not provided)             → gate_dep/gate_arr
(calculated)               → status
(calculated)               → status_reason
```

### Status Determination Logic

```python
actual_on exists           → LANDED
actual_off + no actual_on  → ACTIVE (in flight)
predicted_off < 30min      → BOARDING
predicted_off passed       → DELAYED
else                       → SCHEDULED
```

---

## 🧪 Testing

```bash
# Track a real flight
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "AA",
    "flight_number": "100",
    "departure_date": "2025-10-12"
  }'
```

**Expected Response:**
```json
{
  "id": "AA-100-2025-10-12",
  "airline_code": "AA",
  "flight_number": "100",
  "departure_airport": "JFK",
  "arrival_airport": "LAX",
  "scheduled_offblock": "2025-10-12T14:00:00+00:00",
  "estimated_offblock": "2025-10-12T14:15:00+00:00",
  "scheduled_arrival": "2025-10-12T17:30:00+00:00",
  "estimated_arrival": "2025-10-12T17:45:00+00:00",
  "status": "BOARDING",
  "status_reason": "Delayed approximately 15 minutes",
  "last_provider": "FlightAwareProvider",
  ...
}
```

---

## 🔍 API Endpoint Used

**Endpoint:** `/flights/{ident}`  
**Method:** GET  
**URL:** `https://aeroapi.flightaware.com/aeroapi/flights/AA100`

**Headers:**
```http
x-apikey: your_api_key_here
```

**Response Fields Used:**
- `flights[0].origin` - Departure airport
- `flights[0].destination` - Arrival airport
- `flights[0].actual_off` - Actual departure time
- `flights[0].actual_on` - Actual arrival time
- `flights[0].predicted_off` - Estimated departure
- `flights[0].predicted_on` - Estimated arrival
- `flights[0].ident` - Flight identifier
- `flights[0].aircraft_type` - Aircraft type

---

## 📝 Implementation

The provider is implemented in:
**`backend/flight/providers/flightaware.py`**

Key methods:
- `fetch_status()` - Makes API call to FlightAware
- `_map_to_response()` - Maps FlightAware schema to our normalized format
- `_determine_status()` - Calculates flight status from timestamps
- `_parse_time()` - Parses ISO 8601 timestamps

---

## 💰 Cost Management

### Pricing Tiers

**Basic:** $89/month
- 5,000 flight queries
- $0.018 per additional query

**Standard:** $499/month
- 50,000 queries
- Better rate for overages

### Optimization Tips

1. **Cache aggressively**: Default 60s cache saves money
2. **Rate limit clients**: Default 10 req/min per flight
3. **Monitor usage**: Check FlightAware dashboard daily
4. **Use mock in dev**: Save API calls for production

---

## 🚨 Limitations

### What's NOT Included

1. **Gate information**: Basic endpoint doesn't provide gates
   - Need to call additional endpoints for terminal/gate data
2. **Scheduled times**: Uses predicted times as proxy
3. **Live position**: Not exposed in our simplified model
4. **Route waypoints**: Available but not mapped

### Future Enhancements

To get gate information, you'd need to:

```python
# Additional API call
url = f"{self.base_url}/flights/{fa_flight_id}/route"
# This returns more detailed gate/terminal data
```

---

## 🔄 Switching Providers

```bash
# Development: Use mock
export FLIGHT_PROVIDER=mock

# Staging: Use AeroDataBox (cheaper)
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=...

# Production: Use FlightAware (best quality)
export FLIGHT_PROVIDER=flightaware
export FLIGHTAWARE_API_KEY=...
```

**No code changes required!**

---

## 📚 Resources

- **API Docs**: https://www.flightaware.com/commercial/aeroapi/documentation.rvt
- **Pricing**: https://www.flightaware.com/commercial/aeroapi/pricing.rvt
- **Support**: support@flightaware.com
- **Code**: `backend/flight/providers/flightaware.py`

---

## ✅ Checklist

Before going live with FlightAware:

- [ ] API key obtained from FlightAware
- [ ] Environment variable set (`FLIGHTAWARE_API_KEY`)
- [ ] Tested with real flight
- [ ] Cost alerts configured
- [ ] Usage monitoring enabled
- [ ] Fallback to mock configured
- [ ] Cache TTL optimized (60s recommended)
- [ ] Rate limits configured


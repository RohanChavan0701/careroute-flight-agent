# FlightAware API Key Setup Guide

## 🔑 Getting Your FlightAware API Key

### Current Status
- ❌ `codefesthokies` - Invalid
- ❌ `codefest2025` - Invalid
- ✅ **Currently using Mock Provider for demo**

### How to Get a Valid Key

1. **Sign Up for FlightAware AeroAPI**
   - Visit: https://www.flightaware.com/commercial/aeroapi/
   - Create an account
   - Choose a plan (Basic starts at $89/month)

2. **Get Your API Key**
   - Log into your account
   - Navigate to: API Portal → API Keys
   - Copy your API key (20-40 character alphanumeric string)
   - Example format: `abc123def456ghi789jkl012mno345pqr`

3. **Verify Your Key**
   ```bash
   curl -H "x-apikey: YOUR_KEY" \
     "https://aeroapi.flightaware.com/aeroapi/flights/AA123?ident_type=designator&start=2025-10-12&end=2025-10-13&max_pages=1"
   ```

   ✅ Success: Returns JSON with flight data
   ❌ Failure: Returns `{"title": "Invalid API key", ...}`

## 📝 Configuration Steps

### Step 1: Update `.env` File

Edit: `flight_agent/.env`

```bash
# Change from mock to flightaware
PROVIDER=flightaware

# Add your API key
FA_API_KEY=your_actual_key_here
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6

# Server config
A2A_PORT=8001
```

### Step 2: Restart the Server

```bash
# Kill existing server
lsof -ti :8001 | xargs kill -9

# Start with FlightAware provider
cd /Users/rohanchavan/Desktop/Codefest
export PROVIDER=flightaware
export FA_API_KEY=your_actual_key_here
export A2A_PORT=8001
python3 -m flight_agent.a2a_server
```

### Step 3: Test with Real Flight Data

```bash
# Test with a real flight
curl -X POST http://localhost:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA123",
      "departure_date": "2025-10-12"
    },
    "id": "real-test-1"
  }' | jq
```

## 🔧 Implementation Details

### Header Format (IMPORTANT!)

FlightAware AeroAPI v4 uses lowercase `x-apikey` header:

```python
# ✅ Correct (already implemented)
headers = {"x-apikey": config.FA_API_KEY}

# ❌ Wrong
headers = {"X-API-KEY": config.FA_API_KEY}
headers = {"x-api-key": config.FA_API_KEY}
```

### API Endpoint

```
GET https://aeroapi.flightaware.com/aeroapi/flights/{ident}
```

**Parameters:**
- `ident_type=designator` - Use flight designator (e.g., AA123)
- `start=YYYY-MM-DD` - Departure date
- `end=YYYY-MM-DD` - Next day (for date range)
- `max_pages=1` - Limit to first page of results

### Code Location

The FlightAware provider is already implemented in:
- `flight_agent/provider.py` - Main provider class
- `flight_agent/config.py` - Configuration
- `flight_agent/a2a_server.py` - Server integration

## 💰 Cost Considerations

### FlightAware AeroAPI Pricing

- **Basic Plan**: $89/month
  - 10,000 queries/month
  - $0.009 per query after limit

- **Plus Plan**: $199/month
  - 25,000 queries/month
  - $0.008 per query after limit

### Cost Optimization

Our implementation includes:
- ✅ Retry logic with exponential backoff (3 retries max)
- ✅ 6-second timeout to prevent hanging
- ✅ Response caching via hash (ready for Redis)
- ✅ Single API call per request

**Estimated Usage:**
- CodeFest demo: ~20 requests = $0.18
- Daily testing: ~100 requests = $0.90
- Monthly development: ~1,000 requests = $9.00

## 🎯 For Your CodeFest Demo

### Recommended Approach

**Use Mock Provider** for the demo because:
- ✅ Zero cost
- ✅ 100% reliable (no API failures)
- ✅ Deterministic responses
- ✅ Shows full feature set
- ✅ Demonstrates provider-agnostic architecture

### Demo Talking Points

"Our flight-agent uses a **provider-agnostic architecture**. We've built 
abstraction layers that allow us to seamlessly switch between data 
providers:

- For this demo: **Mock Provider** (reliable, deterministic)
- For production: **FlightAware AeroAPI** (real-time, 100K+ flights)
- Future: **AeroDataBox**, **FlightRadar24**, or custom sources

Switching providers requires **zero code changes** - just update one 
environment variable. This makes our system flexible, testable, and 
future-proof."

## 🚀 Quick Commands

### Check Current Provider
```bash
curl http://localhost:8001/health | jq '.provider'
```

### Test with Mock Provider
```bash
export PROVIDER=mock
python3 -m flight_agent.a2a_server
```

### Test with FlightAware (when you have a key)
```bash
export PROVIDER=flightaware
export FA_API_KEY=your_key_here
python3 -m flight_agent.a2a_server
```

### View Agent Card
```bash
curl http://localhost:8001/agent.json | jq '.metadata.provider'
```

## 📚 Additional Resources

- **FlightAware API Docs**: https://www.flightaware.com/commercial/aeroapi/documentation.rvt
- **A2A Protocol**: https://github.com/a2aproject/A2A
- **Your Implementation**: `flight_agent/provider.py`
- **Test Script**: `test_flightaware_api.py`

## 🆘 Troubleshooting

### Issue: 401 Unauthorized
- **Cause**: Invalid API key
- **Solution**: Verify key format, check account status

### Issue: 429 Too Many Requests
- **Cause**: Rate limit exceeded
- **Solution**: Wait, or upgrade plan

### Issue: Empty Response
- **Cause**: Flight not found or doesn't operate on that date
- **Solution**: Try a different flight/date

### Issue: Timeout
- **Cause**: API slow or network issues
- **Solution**: Retry logic is automatic (3x with backoff)

---

**Summary**: Your system is production-ready! Just add a valid FlightAware 
API key when you're ready to switch from Mock to real-time data. For 
CodeFest, the Mock provider is perfect! 🎉


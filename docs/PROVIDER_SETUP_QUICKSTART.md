# AeroDataBox Provider - Quick Setup Guide

Get real-time flight data in 5 minutes!

---

## 🚀 Quick Start

### 1. Get RapidAPI Key

1. Go to https://rapidapi.com/aedbx-aedbx/api/aerodatabox
2. Click **"Subscribe to Test"**
3. Choose a plan:
   - **Basic** ($9.99/mo): 500 requests
   - **Pro** ($49.99/mo): 5,000 requests
   - **Mega** ($99.99/mo): 25,000 requests
4. Copy your **API Key** from the dashboard

### 2. Configure Environment

```bash
cd /Users/rohanchavan/Desktop/Codefest

# Add to backend/.env
cat >> backend/.env << 'EOF'

# AeroDataBox Real-Time Flight Data
FLIGHT_PROVIDER=aerodatabox
AEROBOX_KEY=your_rapidapi_key_here
AEROBOX_HOST=aerodatabox.p.rapidapi.com
AEROBOX_BASE=https://aerodatabox.p.rapidapi.com
AEROBOX_TIMEOUT_SEC=6
EOF
```

### 3. Restart Server

```bash
pkill -f "uvicorn backend.main:app"
./start_server.sh
```

You should see:
```
INFO:backend.main:Using flight provider: aerodatabox
```

### 4. Test Real Flight

```bash
# Track a real flight (e.g., American Airlines 100)
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "AA",
    "flight_number": "100",
    "departure_date": "2025-10-12"
  }'
```

You'll get **real-time data**:
- Actual gates and terminals
- Live delay information
- Scheduled vs estimated times
- Current flight status

---

## 🔄 Switch Back to Mock

```bash
# Edit backend/.env
FLIGHT_PROVIDER=mock

# Restart
pkill -f "uvicorn backend.main:app"
./start_server.sh
```

---

## 🐛 Troubleshooting

### "Invalid API key"

Check that your RapidAPI key is correct:
```bash
grep AEROBOX_KEY backend/.env
```

### "Provider timeout"

Increase timeout:
```bash
export AEROBOX_TIMEOUT_SEC=10
```

### "No flights found"

- Verify flight number format: `AA100` (not `AA 100`)
- Check date format: `2025-10-12` (ISO 8601)
- Confirm flight exists for that date

### "Rate limit exceeded"

You've hit your RapidAPI plan limit. Either:
- Wait for reset (monthly)
- Upgrade plan
- Switch back to mock temporarily

---

## 📊 Monitoring Usage

Check your usage at:
https://rapidapi.com/developer/billing/subscriptions-and-usage

Set up alerts when you reach 80% of quota.

---

## 💰 Cost Optimization

1. **Cache aggressively**: Default 60s is good
2. **Rate limit clients**: Default 10 req/min per flight
3. **Monitor logs**: Track `AeroDataBox` calls
4. **Upgrade strategically**: Move to Pro when you hit 400 req/month

---

## 🎯 Production Checklist

Before going live:

- [ ] RapidAPI key in production secrets (not .env file)
- [ ] Timeout set to 6 seconds
- [ ] Error handling tested
- [ ] Cost alerts configured
- [ ] Fallback to mock on provider failure
- [ ] Logging enabled
- [ ] Rate limits enforced
- [ ] Cache enabled (60s)

---

## 🔗 Useful Links

- **API Docs**: https://rapidapi.com/aedbx-aedbx/api/aerodatabox
- **Provider Code**: `backend/flight/providers/aerodatabox.py`
- **Full Integration Guide**: `docs/PROVIDER_INTEGRATION.md`


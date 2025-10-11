# Flight Provider Integration Guide

Guardian Buddy uses a **pluggable provider architecture** that makes it easy to swap between mock data (for demos) and real flight APIs (for production).

---

## 🏗️ Architecture

```
FlightService
    ↓
FlightProvider (abstract interface)
    ↓
    ├── MockProvider (deterministic demo data)
    └── AeroDataBoxProvider (real-time via RapidAPI)
```

All providers implement the same interface and return normalized `ProviderResponse` objects, ensuring consistent behavior regardless of data source.

---

## 📦 Available Providers

### 1. MockProvider (Default)

**Purpose:** Demo, testing, offline development  
**Cost:** Free  
**Configuration:** None required

```bash
export FLIGHT_PROVIDER=mock
```

**Behavior:**
- Deterministic status based on flight number modulo 5
- 60-second caching
- Simple rate limiting (10 req/min per flight)
- No external API calls

**Status mapping:**
- Flight # % 5 = 0 → SCHEDULED (e.g., AA100, UA500)
- Flight # % 5 = 1 → BOARDING (e.g., UA456, DL101)
- Flight # % 5 = 2 → ACTIVE (e.g., BA202, AA102)
- Flight # % 5 = 3 → DELAYED (e.g., DL303, SW103)
- Flight # % 5 = 4 → LANDED (e.g., SW789, UA104)

### 2. AeroDataBoxProvider

**Purpose:** Production with real-time flight data  
**Cost:** RapidAPI subscription required  
**API:** https://rapidapi.com/aedbx-aedbx/api/aerodatabox

**Configuration:**

```bash
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=your_rapidapi_key_here
export AEROBOX_HOST=aerodatabox.p.rapidapi.com
export AEROBOX_BASE=https://aerodatabox.p.rapidapi.com
export AEROBOX_TIMEOUT_SEC=6
```

**Features:**
- Real-time flight status
- Gate and terminal information
- Delay information
- Scheduled vs estimated times
- Airport codes (IATA/ICAO)

**Pricing:**
- Basic: $9.99/month (500 requests)
- Pro: $49.99/month (5,000 requests)
- Ultra: Custom pricing

---

## 🔧 Adding a New Provider

Want to integrate FlightAware, AviationStack, or another API? Here's how:

### Step 1: Create Provider Class

Create `backend/flight/providers/yourprovider.py`:

```python
import httpx
from .base import FlightProvider, ProviderResponse
from ..models import FlightStatus

class YourProvider(FlightProvider):
    def __init__(self):
        self.api_key = os.getenv("YOUR_API_KEY")
        self.base_url = "https://api.yourprovider.com"
    
    def fetch_status(
        self, 
        airline_code: str, 
        flight_number: str, 
        departure_date: str
    ) -> ProviderResponse:
        # Call your API
        url = f"{self.base_url}/flights/{airline_code}{flight_number}"
        response = httpx.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
        data = response.json()
        
        # Map to ProviderResponse
        return ProviderResponse(
            airline_code=airline_code,
            flight_number=flight_number,
            departure_airport=data.get("origin"),
            arrival_airport=data.get("destination"),
            scheduled_offblock=parse_datetime(data.get("scheduled_departure")),
            estimated_offblock=parse_datetime(data.get("estimated_departure")),
            scheduled_arrival=parse_datetime(data.get("scheduled_arrival")),
            estimated_arrival=parse_datetime(data.get("estimated_arrival")),
            gate_dep=data.get("departure_gate"),
            gate_arr=data.get("arrival_gate"),
            terminal_dep=data.get("departure_terminal"),
            terminal_arr=data.get("arrival_terminal"),
            status=self._map_status(data.get("status")),
            status_reason=data.get("delay_reason"),
        )
    
    def _map_status(self, api_status: str) -> FlightStatus:
        # Map provider statuses to our enum
        mapping = {
            "ON_TIME": FlightStatus.SCHEDULED,
            "BOARDING": FlightStatus.BOARDING,
            "IN_FLIGHT": FlightStatus.ACTIVE,
            # ... etc
        }
        return mapping.get(api_status, FlightStatus.SCHEDULED)
```

### Step 2: Register Provider

Update `backend/flight/providers/__init__.py`:

```python
from .yourprovider import YourProvider

def get_provider(provider_type: str):
    providers = {
        "mock": MockProvider,
        "aerodatabox": AeroDataBoxProvider,
        "yourprovider": YourProvider,  # ADD THIS
    }
    # ... rest of function
```

### Step 3: Add Configuration

Update `backend/common/settings.py`:

```python
# Your provider config
your_api_key: str = Field(default=os.getenv("YOUR_API_KEY", ""))
your_api_url: str = Field(default=os.getenv("YOUR_API_URL", ""))
```

### Step 4: Use It

```bash
export FLIGHT_PROVIDER=yourprovider
export YOUR_API_KEY=your_key_here
./start_server.sh
```

---

## 🧪 Testing Providers

### Test with Mock Provider

```bash
# Start server with mock
export FLIGHT_PROVIDER=mock
./start_server.sh

# Track a flight (will return LANDED status)
curl -X POST http://localhost:8000/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "airline_code": "DL",
    "flight_number": "789",
    "departure_date": "2025-10-11"
  }'
```

### Test with AeroDataBox

```bash
# Start server with real API
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=your_rapidapi_key
./start_server.sh

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

---

## 🔍 Provider Response Schema

All providers must return this normalized schema:

```python
class ProviderResponse:
    airline_code: str                    # Required: IATA code (e.g., "AA")
    flight_number: str                   # Required: Flight number
    departure_airport: Optional[str]     # IATA code (e.g., "JFK")
    arrival_airport: Optional[str]       # IATA code (e.g., "LAX")
    scheduled_offblock: Optional[datetime]  # ISO 8601 UTC
    estimated_offblock: Optional[datetime]  # ISO 8601 UTC
    scheduled_arrival: Optional[datetime]   # ISO 8601 UTC
    estimated_arrival: Optional[datetime]   # ISO 8601 UTC
    gate_dep: Optional[str]              # Departure gate
    gate_arr: Optional[str]              # Arrival gate
    terminal_dep: Optional[str]          # Departure terminal
    terminal_arr: Optional[str]          # Arrival terminal
    status: FlightStatus                 # Enum: SCHEDULED, BOARDING, ACTIVE, etc.
    status_reason: Optional[str]         # Human-readable delay reason
```

---

## 🛡️ Best Practices

### 1. Error Handling

Always handle provider failures gracefully:

```python
def fetch_status(...) -> ProviderResponse:
    try:
        response = httpx.get(url, timeout=6)
        response.raise_for_status()
        return self._parse_response(response.json())
    except httpx.TimeoutException:
        raise Exception("Provider timeout")
    except httpx.HTTPStatusError as e:
        raise Exception(f"Provider returned {e.response.status_code}")
```

### 2. Timeouts

Set reasonable timeouts (6 seconds recommended):

```python
httpx.Client(timeout=6.0)
```

### 3. Rate Limiting

Respect provider rate limits. Consider adding:
- Request queuing
- Exponential backoff on errors
- Circuit breaker pattern

### 4. Caching

Cache responses to reduce API calls:
- 60 seconds for active flights
- 5 minutes for landed flights
- 15 minutes for cancelled flights

### 5. Logging

Log provider calls for debugging:

```python
logger.info(f"Fetching from {provider_name}: {airline_code}{flight_number}")
logger.error(f"Provider error: {error}")
```

---

## 📊 Provider Comparison

| Provider | Cost | Data Quality | Setup | Best For |
|----------|------|--------------|-------|----------|
| **Mock** | Free | Deterministic | None | Demo, testing |
| **AeroDataBox** | $10-50/mo | Excellent | Easy | Production |
| **FlightAware** | $89+/mo | Best | Medium | Enterprise |
| **AviationStack** | $10+/mo | Good | Easy | Startups |
| **OpenSky** | Free | Good | Medium | Research |

---

## 🚀 Production Checklist

Before going live with a real provider:

- [ ] API key secured in environment variables
- [ ] Timeout configured (6 seconds)
- [ ] Error handling tested
- [ ] Rate limits respected
- [ ] Caching enabled
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Fallback behavior defined
- [ ] Cost alerts configured
- [ ] API quota monitoring

---

## 💡 Example: Switching Providers

### Development (Mock)
```bash
export FLIGHT_PROVIDER=mock
```

### Staging (AeroDataBox)
```bash
export FLIGHT_PROVIDER=aerodatabox
export AEROBOX_KEY=$STAGING_AEROBOX_KEY
```

### Production (FlightAware)
```bash
export FLIGHT_PROVIDER=flightaware
export FLIGHTAWARE_API_KEY=$PROD_FLIGHTAWARE_KEY
```

No code changes required—just environment variables!

---

## 📞 Need Help?

- **AeroDataBox Docs:** https://rapidapi.com/aedbx-aedbx/api/aerodatabox
- **Provider Interface:** See `backend/flight/providers/base.py`
- **Example Implementation:** See `backend/flight/providers/aerodatabox.py`


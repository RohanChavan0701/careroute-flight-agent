# Flight Agent - A2A Protocol Implementation

**Agent2Agent (A2A) Protocol compliance for Guardian Buddy Flight Agent**

Official A2A Protocol: https://github.com/a2aproject/A2A

---

## 🎯 What is A2A?

The **Agent2Agent (A2A) Protocol** is an open standard by Google that enables AI agents to communicate and collaborate using **JSON-RPC 2.0 over HTTP(S)**.

### Key Benefits:

- ✅ **Interoperability**: Agents from different companies/frameworks can work together
- ✅ **Discovery**: Agents advertise capabilities via "Agent Cards"
- ✅ **Opacity**: Agents don't expose internal state or tools
- ✅ **Enterprise-Ready**: Built-in auth, security, observability
- ✅ **Standardized**: JSON-RPC 2.0 is a well-established protocol

---

## 🏗️ Architecture

### Before (NATS):
```
Client → NATS → Flight Agent → FlightAware/Groq
```

### After (A2A):
```
Client → HTTP/JSON-RPC 2.0 → Flight Agent → FlightAware/Groq
         ↓
    Agent Card Discovery
```

---

## 📡 Endpoints

### 1. Root Endpoint
```http
GET http://localhost:8001/
```

Returns agent info and available endpoints.

**Response:**
```json
{
  "agent": "Guardian Buddy Flight Agent",
  "protocol": "A2A (Agent2Agent)",
  "version": "1.0.0",
  "endpoints": {
    "agent_card": "/agent.json",
    "rpc": "/a2a"
  }
}
```

### 2. Agent Card (Discovery)
```http
GET http://localhost:8001/agent.json
```

Returns the Agent Card describing capabilities.

**Response:**
```json
{
  "name": "Guardian Buddy Flight Agent",
  "description": "Provides real-time flight status with AI summaries",
  "version": "1.0.0",
  "url": "http://localhost:8001/a2a",
  "skills": [
    {
      "name": "get_flight_status",
      "description": "Get current flight status with conversational summary",
      "input_schema": {
        "type": "object",
        "properties": {
          "flight_num": {
            "type": "string",
            "description": "Flight designator (e.g., AA100)"
          },
          "departure_date": {
            "type": "string",
            "description": "Departure date (YYYY-MM-DD)"
          },
          "locale": {
            "type": "string",
            "description": "Locale for formatting",
            "default": "en-US"
          }
        },
        "required": ["flight_num", "departure_date"]
      },
      "output_schema": { ... }
    }
  ],
  "metadata": {
    "provider": "FlightAware AeroAPI v4",
    "ai_model": "Groq llama-3.1-8b-instant"
  }
}
```

### 3. JSON-RPC Endpoint
```http
POST http://localhost:8001/a2a
Content-Type: application/json
```

Handles skill invocations via JSON-RPC 2.0.

---

## 🔧 JSON-RPC 2.0 Format

### Request Structure

```json
{
  "jsonrpc": "2.0",
  "method": "skill_name",
  "params": { ... },
  "id": "unique-request-id"
}
```

### Success Response

```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": "unique-request-id"
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": { ... }
  },
  "id": "unique-request-id"
}
```

---

## 📋 Skills

### get_flight_status

Get real-time flight status with AI-powered summary.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_flight_status",
  "params": {
    "flight_num": "AA100",
    "departure_date": "2025-10-12",
    "locale": "en-US"
  },
  "id": "req-123"
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "raw": {
      "airline": "American Airlines",
      "flight_number": "AA100",
      "origin_iata": "JFK",
      "origin_city": "New York",
      "origin_tz": "America/New_York",
      "destination_iata": "LAX",
      "destination_city": "Los Angeles",
      "destination_tz": "America/Los_Angeles",
      "scheduled_departure_local": "2025-10-12T14:00",
      "estimated_departure_local": "2025-10-12T14:10",
      "scheduled_arrival_local": "2025-10-12T17:30",
      "estimated_arrival_local": "2025-10-12T17:40",
      "gate": "B12",
      "terminal": "8",
      "status": "IN_AIR",
      "delay_minutes": 10
    },
    "script": {
      "text": "Flight AA100 is in the air. Expected arrival at 5:40 PM.",
      "ssml": "<speak>Flight AA100 is in the air. Expected arrival at <say-as interpret-as=\"time\">5:40 PM</say-as>.</speak>",
      "style": "conversational",
      "locale": "en-US"
    },
    "hash": "a1b2c3d4e5f6g7h8",
    "generated_at": "2025-10-11T14:30:00Z",
    "schema_version": "flight.status.v1"
  },
  "id": "req-123"
}
```

---

## ⚠️ Error Codes

| Code | Name | Description |
|------|------|-------------|
| `-32700` | Parse Error | Invalid JSON |
| `-32600` | Invalid Request | Invalid JSON-RPC structure |
| `-32601` | Method Not Found | Skill doesn't exist |
| `-32602` | Invalid Params | Parameter validation failed |
| `-32603` | Internal Error | Server error |
| `-32000` | Provider Error | FlightAware API error |
| `-32001` | Summarizer Error | Groq LLM error |

**Example Error:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid parameters",
    "data": {
      "validation_errors": [
        {
          "loc": ["departure_date"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  },
  "id": "req-123"
}
```

---

## 🚀 Quick Start

### 1. Set Environment Variables

```bash
export PROVIDER=flightaware
export FA_API_KEY=your_flightaware_key
export GROQ_API_KEY=your_groq_key
export A2A_PORT=8001
```

### 2. Start the Agent

```bash
./scripts/run_a2a_flight_agent.sh
```

You should see:
```
✅ Setup complete!
📡 Starting A2A Flight Agent...
   Protocol: A2A (Agent2Agent) JSON-RPC 2.0
   Port: 8001
   Agent Card: http://localhost:8001/agent.json
   JSON-RPC: http://localhost:8001/a2a
```

### 3. Test with Python

```python
import httpx
import json
from uuid import uuid4

# Get Agent Card
card = httpx.get("http://localhost:8001/agent.json").json()
print("Agent:", card["name"])

# Invoke skill
request = {
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
        "flight_num": "AA100",
        "departure_date": "2025-10-12",
        "locale": "en-US"
    },
    "id": str(uuid4())
}

response = httpx.post("http://localhost:8001/a2a", json=request).json()
print("Status:", response["result"]["raw"]["status"])
print("Summary:", response["result"]["script"]["text"])
```

### 4. Test with Test Client

```bash
cd flight_agent
python test_a2a_client.py http://localhost:8001 AA100 2025-10-12
```

### 5. Test with curl

```bash
# Get Agent Card
curl http://localhost:8001/agent.json | jq

# Invoke skill
curl -X POST http://localhost:8001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA100",
      "departure_date": "2025-10-12",
      "locale": "en-US"
    },
    "id": "test-1"
  }' | jq
```

---

## 🔄 Integration Examples

### From Another A2A Agent (Python)

```python
import httpx

class FlightStatusIntegration:
    """Integrate with Flight Agent via A2A."""
    
    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.rpc_url = f"{agent_url}/a2a"
    
    async def get_flight_status(self, flight_num: str, date: str):
        """Call flight agent skill."""
        request = {
            "jsonrpc": "2.0",
            "method": "get_flight_status",
            "params": {
                "flight_num": flight_num,
                "departure_date": date
            },
            "id": str(uuid4())
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.rpc_url, json=request)
            result = response.json()
            
            if "error" in result:
                raise Exception(result["error"]["message"])
            
            return result["result"]

# Usage
agent = FlightStatusIntegration("http://localhost:8001")
status = await agent.get_flight_status("AA100", "2025-10-12")
print(status["script"]["text"])
```

### From Node.js

```javascript
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

async function getFlightStatus(flightNum, date) {
  const request = {
    jsonrpc: '2.0',
    method: 'get_flight_status',
    params: {
      flight_num: flightNum,
      departure_date: date,
      locale: 'en-US'
    },
    id: uuidv4()
  };
  
  const response = await axios.post('http://localhost:8001/a2a', request);
  
  if (response.data.error) {
    throw new Error(response.data.error.message);
  }
  
  return response.data.result;
}

// Usage
getFlightStatus('AA100', '2025-10-12')
  .then(result => console.log(result.script.text));
```

---

## 📊 Comparison: NATS vs A2A

| Feature | NATS | A2A |
|---------|------|-----|
| Protocol | NATS messaging | HTTP + JSON-RPC 2.0 |
| Discovery | Manual | Agent Card |
| Format | Custom JSON | Standard JSON-RPC |
| Transport | TCP | HTTP(S) |
| Auth | NATS auth | HTTP auth (headers) |
| Interop | NATS clients only | Any HTTP client |
| Standard | Proprietary | Open (A2A) |
| Best For | Internal microservices | Agent collaboration |

---

## 🎯 A2A Compliance Checklist

✅ **Protocol**
- [x] JSON-RPC 2.0 format
- [x] HTTP(S) transport
- [x] POST /a2a endpoint

✅ **Agent Card**
- [x] GET /agent.json endpoint
- [x] Name, description, version
- [x] Skills with input/output schemas
- [x] Metadata

✅ **Skills**
- [x] get_flight_status skill
- [x] Pydantic validation
- [x] Structured input/output

✅ **Error Handling**
- [x] Standard JSON-RPC error codes
- [x] Detailed error messages
- [x] Error data payload

✅ **Features**
- [x] Synchronous request/response
- [x] Health check endpoint
- [ ] Streaming (SSE) - future
- [ ] Async push notifications - future

---

## 🔐 Security Considerations

### Current Implementation
- Agent runs on localhost (8001)
- No authentication (dev only)
- HTTP (not HTTPS)

### Production Recommendations
1. **HTTPS**: Use TLS certificates
2. **Authentication**: Add API key or OAuth2
3. **Rate Limiting**: Implement per-client limits
4. **CORS**: Configure allowed origins
5. **Firewall**: Restrict access to trusted IPs
6. **Monitoring**: Log all requests

---

## 📚 Resources

- **A2A Protocol**: https://github.com/a2aproject/A2A
- **A2A Documentation**: https://a2a-protocol.org/
- **JSON-RPC 2.0 Spec**: https://www.jsonrpc.org/specification
- **FlightAware AeroAPI**: https://www.flightaware.com/commercial/aeroapi/
- **Groq**: https://groq.com/

---

## 🎉 Summary

Your Flight Agent now:

- ✅ Implements **A2A Protocol** (Agent2Agent)
- ✅ Uses **JSON-RPC 2.0** over HTTP
- ✅ Provides **Agent Card** for discovery
- ✅ Exposes **get_flight_status** skill
- ✅ Maintains all existing functionality
- ✅ Is **interoperable** with other A2A agents

**Perfect for multi-agent collaboration! 🤝**

---

## 📂 Files

- `flight_agent/a2a_server.py` - A2A HTTP server
- `flight_agent/test_a2a_client.py` - Test client
- `scripts/run_a2a_flight_agent.sh` - Startup script
- `A2A_PROTOCOL_GUIDE.md` - This guide

---

**Next Steps:**
1. Install A2A SDK: `pip install a2a-sdk`
2. Explore A2A examples
3. Connect with other A2A agents
4. Build multi-agent workflows!


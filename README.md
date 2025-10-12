# Guardian Buddy Flight Agent 🛡️✈️

**Real-time Flight Tracking AI Agent for Medical Tourism**  
VT CodeFest 2025 Submission

---

## 🎯 What It Does

Guardian Buddy is an AI-powered flight tracking agent that helps medical tourists and their families stay informed during their journey. It provides real-time flight status with AI-generated conversational summaries.

**Key Features:**
- ✅ Real-time flight tracking (FlightAware AeroAPI)
- ✅ AI-powered natural language summaries (Groq LLM)
- ✅ Voice-ready SSML output for text-to-speech
- ✅ A2A Protocol (JSON-RPC 2.0) for agent interoperability
- ✅ Docker containerized and production-ready
- ✅ Deployed on AWS EC2

---

## 🚀 Live Demo

**Endpoint:** `http://54.158.27.0:8001`

### Quick Test

```bash
# Health check
curl http://54.158.27.0:8001/health

# Get agent capabilities
curl http://54.158.27.0:8001/agent.json

# Get flight status
curl -X POST http://54.158.27.0:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "DL2990",
      "departure_date": "2025-10-11"
    },
    "id": "demo"
  }'
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "flight_data": {
      "airline": "DAL",
      "flight_number": "DAL2990",
      "origin_iata": "MSY",
      "destination_iata": "DTW",
      "status": "LANDED",
      "gate": "C4",
      "terminal": "M"
    },
    "script": {
      "text": "Flight DAL2990 from MSY to DTW has landed at gate C4.",
      "ssml": "<speak>Flight DAL2990 from MSY to DTW has landed at gate C4.</speak>"
    }
  }
}
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Orchestrator  │ (Medical Tourism Platform)
│   (JSON-RPC)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flight Agent   │ ◄── A2A Protocol (JSON-RPC 2.0)
│  (Docker/EC2)   │
└────────┬────────┘
         │
         ├──► FlightAware AeroAPI (Real-time data)
         └──► Groq LLM (AI summaries)
```

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, Pydantic
- **APIs:** FlightAware AeroAPI v4, Groq LLM
- **Protocol:** A2A (Agent2Agent) with JSON-RPC 2.0
- **Deployment:** Docker, AWS EC2
- **Monitoring:** Health checks, structured logging

---

## 📡 API Specification

### A2A Protocol Endpoint

**POST** `/a2a`

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_flight_status",
  "params": {
    "flight_num": "DL2990",
    "departure_date": "2025-10-11",
    "locale": "en-US"
  },
  "id": "request-123"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "flight_data": {
      "airline": "DAL",
      "flight_number": "DAL2990",
      "origin_iata": "MSY",
      "origin_city": "New Orleans",
      "destination_iata": "DTW",
      "destination_city": "Detroit",
      "scheduled_departure_local": "2025-10-11T12:40",
      "estimated_departure_local": "2025-10-11T12:46",
      "scheduled_arrival_local": "2025-10-11T15:09",
      "estimated_arrival_local": "2025-10-11T15:23",
      "gate": "C4",
      "terminal": "M",
      "status": "LANDED",
      "delay_minutes": 14
    },
    "script": {
      "text": "Flight DAL2990 from MSY to DTW has landed at gate C4.",
      "ssml": "<speak>Flight DAL2990 from MSY to DTW has landed at gate C4. Departure was at <say-as interpret-as=\"time\">12:46</say-as> and arrival was at <say-as interpret-as=\"time\">15:23</say-as>.</speak>",
      "style": "conversational",
      "locale": "en-US"
    },
    "hash": "c98604221952dd7b",
    "generated_at": "2025-10-11T23:45:24.600681Z",
    "schema_version": "flight.status.v1"
  },
  "id": "request-123"
}
```

### Agent Card

**GET** `/agent.json`

Returns A2A agent capabilities and metadata.

### Health Check

**GET** `/health`

Returns service health status.

---

## 🔌 A2A Protocol Integration

Guardian Buddy implements the [A2A Protocol](https://github.com/a2aproject/A2A) for agent interoperability.

**Agent Card:**
- Name: Guardian Buddy Flight Agent
- Skills: `get_flight_status`
- Protocol: JSON-RPC 2.0 over HTTP
- Discovery: `/agent.json`

**Why A2A?**
- Standard protocol for AI agent communication
- Easy integration with other agents
- Discoverable capabilities
- Interoperable across platforms

---

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- Docker (optional)

### Quick Start

```bash
# Clone repository
git clone https://github.com/rohanpc0701/Codefest_Flightapi.git
cd Codefest_Flightapi

# Set up environment
cd flight_agent
cp env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run agent
python -m simple_a2a_server
```

### Docker Deployment

```bash
# Build image
docker build -t flight-agent .

# Run container
docker run -p 8001:8001 \
  -e FA_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  flight-agent
```

See `DOCKER_GUIDE.md` for complete Docker documentation.

---

## 📊 Key Features

### 1. Real-Time Flight Data
- FlightAware AeroAPI v4 integration
- Live status updates
- Gate and terminal information
- Delay tracking
- Timezone-aware scheduling

### 2. AI-Powered Summaries
- Natural language flight status
- Conversational tone
- SSML for voice synthesis
- Locale-specific formatting

### 3. Production-Ready
- Docker containerized
- Health monitoring
- Structured logging
- Error handling with retry logic
- Timezone handling (pytz)

### 4. A2A Protocol Compliant
- JSON-RPC 2.0
- Agent discovery
- Standard error codes
- Skill-based architecture

---

## 🔐 Security & Privacy

- ✅ API keys stored in environment variables
- ✅ No sensitive data in logs
- ✅ HTTPS-ready (Nginx configuration available)
- ✅ Input validation with Pydantic
- ✅ Rate limiting support
- ✅ HIPAA-aware design (no PHI in responses)

---

## 📚 Documentation

- **`DOCKER_GUIDE.md`** - Complete Docker setup
- **`EC2_DOCKER_DEPLOYMENT.md`** - AWS deployment guide
- **`A2A_PROTOCOL_GUIDE.md`** - A2A implementation details
- **`PRODUCTION_ENHANCEMENTS.md`** - Monitoring, HTTPS, caching
- **`FLIGHTAWARE_QUICKREF.md`** - FlightAware API reference

---

## 🎯 Use Cases

### Medical Tourism
- Track patient arrival flights
- Notify family of delays
- Coordinate airport pickups
- Monitor connecting flights

### Travel Coordination
- Multi-leg journey tracking
- Real-time status updates
- Voice notifications
- Family communication

### Emergency Response
- Track medical evacuation flights
- Monitor ambulance flight status
- Coordinate ground transport

---

## 🏆 Why Guardian Buddy?

### Problem
Medical tourists face uncertainty during travel:
- Flight delays impact medical appointments
- Families need real-time updates
- Language barriers complicate communication
- Multiple stakeholders need coordination

### Solution
AI agent that:
- Tracks flights automatically
- Generates human-friendly updates
- Speaks multiple languages (locale support)
- Integrates with other AI agents (A2A)

### Impact
- ✅ Reduced anxiety for patients
- ✅ Better coordination for medical facilities
- ✅ Improved family communication
- ✅ Faster emergency response

---

## 📈 Future Enhancements

- [ ] Multi-flight tracking
- [ ] Proactive notifications
- [ ] Hotel booking integration
- [ ] Hospital appointment coordination
- [ ] SMS/WhatsApp notifications
- [ ] Mobile app integration
- [ ] Multi-language support

See `WHATS_NEXT.md` for detailed roadmap.

---

## 💰 Cost-Effective

**Current Deployment:**
- AWS EC2 Free Tier: $0/month (12 months)
- FlightAware API: Free tier available
- Groq LLM: Free tier available
- **Total: $0/month** ✅

**After Free Tier:**
- EC2 t2.micro: $8.50/month
- APIs: $10-20/month
- **Total: ~$20/month**

---

## 🔧 Technical Highlights

### Clean Architecture
- Provider-agnostic design
- Separation of concerns
- Type-safe with Pydantic
- Async/await throughout

### Error Handling
- Exponential backoff retry
- Graceful degradation
- Detailed error messages
- Fallback responses

### Performance
- Async HTTP requests
- Efficient data parsing
- Minimal dependencies
- Fast response times (<500ms)

---

## 👥 Team

Built for VT CodeFest 2025

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **Live Demo:** http://54.158.27.0:8001
- **GitHub:** https://github.com/rohanpc0701/Codefest_Flightapi
- **A2A Protocol:** https://github.com/a2aproject/A2A
- **FlightAware API:** https://www.flightaware.com/commercial/aeroapi/

---

**Built with ❤️ for medical travelers and their families**

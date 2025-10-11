# Docker Guide for Guardian Buddy Flight Agent

This guide explains how to containerize and run the Guardian Buddy Flight Agent using Docker.

## 🐳 Quick Start

### 1. Build the Docker Image

```bash
# Build the image
./scripts/docker-build.sh

# Or manually
docker build -t guardian-buddy-flight-agent:latest .
```

### 2. Run with Docker Compose (Recommended)

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
nano .env

# Start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Run with Docker Run

```bash
# Run the container
docker run -d \
  --name flight-agent \
  -p 8001:8001 \
  -e FA_API_KEY=your_flightaware_key \
  -e GROQ_API_KEY=your_groq_key \
  guardian-buddy-flight-agent:latest

# Check status
docker ps

# View logs
docker logs flight-agent
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROVIDER` | Flight data provider | `flightaware` | No |
| `FA_API_KEY` | FlightAware API key | - | Yes |
| `FA_BASE` | FlightAware API base URL | `https://aeroapi.flightaware.com/aeroapi` | No |
| `FA_TIMEOUT_SEC` | FlightAware timeout | `6` | No |
| `GROQ_API_KEY` | Groq LLM API key | - | Yes |
| `GROQ_MODEL` | Groq model | `llama-3.1-8b-instant` | No |
| `GROQ_TIMEOUT_SEC` | Groq timeout | `10` | No |
| `A2A_PORT` | A2A protocol port | `8001` | No |

### Environment File

Create a `.env` file with your API keys:

```bash
# Copy template
cp env.example .env

# Edit with your keys
PROVIDER=flightaware
FA_API_KEY=your_flightaware_api_key_here
GROQ_API_KEY=your_groq_api_key_here
A2A_PORT=8001
```

## 🏥 Health Checks

The container includes built-in health checks:

```bash
# Check container health
docker ps

# Manual health check
curl http://localhost:8001/health

# Expected response
{
  "status": "healthy",
  "provider": "flightaware",
  "description": "Core flight tracking agent",
  "timestamp": "2025-10-11T17:41:45.808319Z"
}
```

## 📊 Testing the Service

### 1. Health Check

```bash
curl http://localhost:8001/health
```

### 2. Agent Card

```bash
curl http://localhost:8001/agent.json
```

### 3. Flight Status Request

```bash
curl -X POST http://localhost:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "DL2990",
      "departure_date": "2025-10-11",
      "locale": "en-US"
    },
    "id": "test"
  }'
```

## 🔍 Monitoring and Logs

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker Run
docker logs -f flight-agent
```

### Container Status

```bash
# Docker Compose
docker-compose ps

# Docker Run
docker ps
```

### Resource Usage

```bash
# Container stats
docker stats flight-agent
```

## 🛠️ Development

### Build for Development

```bash
# Build with development dependencies
docker build -t guardian-buddy-flight-agent:dev .

# Run with volume mount for development
docker run -d \
  --name flight-agent-dev \
  -p 8001:8001 \
  -v $(pwd)/flight_agent:/app/flight_agent \
  -e FA_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  guardian-buddy-flight-agent:dev
```

### Debug Container

```bash
# Access container shell
docker exec -it flight-agent bash

# Check Python environment
docker exec -it flight-agent python -c "import sys; print(sys.path)"

# Test imports
docker exec -it flight-agent python -c "from flight_agent import config; print(config.config.PROVIDER)"
```

## 🚀 Production Deployment

### Docker Compose for Production

```yaml
version: '3.8'

services:
  flight-agent:
    build: .
    container_name: guardian-buddy-flight-agent
    ports:
      - "8001:8001"
    environment:
      - PROVIDER=flightaware
      - FA_API_KEY=${FA_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - flight-agent-network

networks:
  flight-agent-network:
    driver: bridge
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flight-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flight-agent
  template:
    metadata:
      labels:
        app: flight-agent
    spec:
      containers:
      - name: flight-agent
        image: guardian-buddy-flight-agent:latest
        ports:
        - containerPort: 8001
        env:
        - name: FA_API_KEY
          valueFrom:
            secretKeyRef:
              name: flight-agent-secrets
              key: fa-api-key
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: flight-agent-secrets
              key: groq-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: flight-agent-service
spec:
  selector:
    app: flight-agent
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
```

## 🔒 Security Considerations

### 1. API Key Management

- Use Docker secrets or Kubernetes secrets
- Never commit API keys to version control
- Rotate keys regularly

### 2. Container Security

- Run as non-root user (already configured)
- Use minimal base image (python:3.11-slim)
- Regular security updates

### 3. Network Security

- Use internal networks for service communication
- Implement proper firewall rules
- Use HTTPS in production

## 📋 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker logs flight-agent
   
   # Check environment variables
   docker exec flight-agent env
   ```

2. **Health check failing**
   ```bash
   # Manual health check
   docker exec flight-agent curl -f http://localhost:8001/health
   
   # Check if service is running
   docker exec flight-agent ps aux
   ```

3. **API key issues**
   ```bash
   # Verify environment variables
   docker exec flight-agent env | grep -E "(FA_API_KEY|GROQ_API_KEY)"
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   services:
     flight-agent:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: '0.5'
   ```

2. **Caching**
   - Use Docker layer caching
   - Implement application-level caching
   - Use Redis for distributed caching

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FlightAware AeroAPI Documentation](https://flightaware.com/commercial/aeroapi/)
- [Groq API Documentation](https://console.groq.com/docs)

## 🎯 Next Steps

1. **Set up CI/CD pipeline** for automated builds
2. **Implement monitoring** with Prometheus/Grafana
3. **Add logging aggregation** with ELK stack
4. **Set up alerting** for service failures
5. **Implement auto-scaling** based on load

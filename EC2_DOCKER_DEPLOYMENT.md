# Guardian Buddy Flight Agent - Docker on EC2 Deployment

## 🎯 Overview

This guide shows how to deploy the **Dockerized Flight Agent** to your existing EC2 instance (`54.158.27.0`). This approach is cleaner, more portable, and easier to update than the manual Python deployment.

**Benefits of Docker on EC2:**
- 🐳 Containerized environment (no dependency conflicts)
- 🔄 Easy updates (just pull and restart)
- 📦 Consistent across environments
- 🛡️ Better isolation and security
- 🚀 Simpler deployment process

---

## 📋 Prerequisites

- AWS EC2 instance already running (Ubuntu 22.04)
- SSH access to EC2 (`flight-agent-key.pem`)
- Security Group with port 8001 open
- FlightAware and Groq API keys

---

## 🚀 Step-by-Step Deployment

### Step 1: Connect to EC2 Instance

```bash
ssh -i flight-agent-key.pem ubuntu@54.158.27.0
```

---

### Step 2: Install Docker on EC2

#### 2.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2.2 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group (no sudo needed)
sudo usermod -aG docker ubuntu

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2.3 Install Docker Compose
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

#### 2.4 Log out and back in
```bash
exit
ssh -i flight-agent-key.pem ubuntu@54.158.27.0
```

#### 2.5 Verify Docker Works (No Sudo)
```bash
docker --version
docker ps
```

---

### Step 3: Deploy Flight Agent Code

#### 3.1 Create Application Directory
```bash
sudo mkdir -p /opt/flight-agent-docker
sudo chown ubuntu:ubuntu /opt/flight-agent-docker
cd /opt/flight-agent-docker
```

#### 3.2 Clone Repository
```bash
git clone https://github.com/rohanpc0701/Codefest_Flightapi.git .
```

Or use SCP from your local machine:
```bash
# From local machine
cd /Users/rohanchavan/Desktop/Codefest
scp -i flight-agent-key.pem -r Dockerfile docker-compose.yml flight_agent/ env.example ubuntu@54.158.27.0:/opt/flight-agent-docker/
```

---

### Step 4: Configure Environment Variables

#### 4.1 Create `.env` File
```bash
cd /opt/flight-agent-docker
cp env.example .env
nano .env
```

#### 4.2 Edit `.env` with Your API Keys
```bash
# Provider Configuration
PROVIDER=flightaware

# FlightAware AeroAPI
FA_API_KEY=your_flightaware_api_key_here
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6

# Groq LLM
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT_SEC=10

# Server
A2A_PORT=8001
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`

---

### Step 5: Build and Run Docker Container

#### 5.1 Build Docker Image
```bash
cd /opt/flight-agent-docker
docker build -t guardian-buddy-flight-agent:latest .
```

This will:
- Install Python 3.11 and dependencies
- Copy your flight_agent code
- Set up the container

#### 5.2 Run with Docker Compose (Recommended)
```bash
docker-compose up -d
```

Or run directly with Docker:
```bash
docker run -d \
  --name flight-agent \
  -p 8001:8001 \
  --env-file .env \
  --restart unless-stopped \
  guardian-buddy-flight-agent:latest
```

#### 5.3 Verify Container is Running
```bash
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE                              COMMAND                  STATUS         PORTS
abc123def456   guardian-buddy-flight-agent:latest "python -m flight_ag…"   Up 5 seconds   0.0.0.0:8001->8001/tcp
```

---

### Step 6: Test the Deployment

#### 6.1 Check Container Logs
```bash
docker logs flight-agent-docker -f
```

Expected output:
```
2025-10-11 20:00:00,000 [INFO] __main__: Starting Simplified Flight Agent on port 8001
2025-10-11 20:00:00,000 [INFO] __main__: Provider: flightaware
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

Press `Ctrl+C` to exit logs.

#### 6.2 Test Health Endpoint (from EC2)
```bash
curl http://localhost:8001/health
```

Expected:
```json
{"status": "ok"}
```

#### 6.3 Test Agent Card
```bash
curl http://localhost:8001/agent.json
```

#### 6.4 Test Flight Status
```bash
curl -X POST http://localhost:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "DL2990",
      "departure_date": "2025-10-11"
    },
    "id": "test"
  }'
```

---

### Step 7: Test External Access

From your **local machine**:

```bash
# Health check
curl http://54.158.27.0:8001/health

# Agent card
curl http://54.158.27.0:8001/agent.json

# Flight status
curl -X POST http://54.158.27.0:8001/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "DL2990",
      "departure_date": "2025-10-11"
    },
    "id": "test"
  }'
```

---

## 🔧 Docker Management Commands

### View Running Containers
```bash
docker ps
```

### View All Containers (including stopped)
```bash
docker ps -a
```

### View Container Logs
```bash
# Follow logs in real-time
docker logs flight-agent-docker -f

# View last 50 lines
docker logs flight-agent-docker --tail 50

# View logs with timestamps
docker logs flight-agent-docker -t
```

### Stop Container
```bash
docker stop flight-agent-docker
```

### Start Container
```bash
docker start flight-agent-docker
```

### Restart Container
```bash
docker restart flight-agent-docker
```

### Remove Container
```bash
docker stop flight-agent-docker
docker rm flight-agent-docker
```

### Rebuild and Restart (after code changes)
```bash
cd /opt/flight-agent-docker
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔄 Updating the Flight Agent

### Method 1: Using Docker Compose (Recommended)
```bash
cd /opt/flight-agent-docker

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify
docker logs flight-agent-docker -f
```

### Method 2: Using Docker Commands
```bash
cd /opt/flight-agent-docker

# Pull latest code
git pull origin main

# Stop and remove old container
docker stop flight-agent-docker
docker rm flight-agent-docker

# Rebuild image
docker build -t guardian-buddy-flight-agent:latest .

# Run new container
docker run -d \
  --name flight-agent-docker \
  -p 8001:8001 \
  --env-file .env \
  --restart unless-stopped \
  guardian-buddy-flight-agent:latest

# Verify
docker logs flight-agent-docker -f
```

---

## 🐛 Troubleshooting

### Issue 1: Container Immediately Exits

**Check logs:**
```bash
docker logs flight-agent-docker
```

**Common causes:**
- Missing or invalid API keys in `.env`
- Port 8001 already in use
- Import errors in Python code

**Solution:**
```bash
# Check if port is in use
sudo netstat -tlnp | grep 8001

# Kill process if needed
sudo kill -9 <PID>

# Verify .env file
cat .env

# Restart container
docker restart flight-agent-docker
```

---

### Issue 2: Cannot Build Docker Image

**Error:** `Cannot connect to Docker daemon`

**Solution:**
```bash
# Check Docker service
sudo systemctl status docker

# Start Docker if stopped
sudo systemctl start docker

# Verify user is in docker group
groups ubuntu

# If not, re-login
exit
ssh -i flight-agent-key.pem ubuntu@54.158.27.0
```

---

### Issue 3: External Access Fails

**Symptoms:** `curl` times out from local machine

**Solution:**
1. **Verify container is running:**
   ```bash
   docker ps
   curl http://localhost:8001/health
   ```

2. **Check Security Group:**
   - AWS Console → EC2 → Security Groups
   - Verify port 8001 is open to `0.0.0.0/0`

3. **Check container port mapping:**
   ```bash
   docker port flight-agent-docker
   ```
   Should show: `8001/tcp -> 0.0.0.0:8001`

---

### Issue 4: Out of Memory

**Symptoms:** Container crashes, Docker build fails

**Solution:**
```bash
# Check memory usage
free -h

# Check Docker stats
docker stats flight-agent-docker

# Clean up unused Docker resources
docker system prune -a

# Restart container with memory limit
docker stop flight-agent-docker
docker rm flight-agent-docker
docker run -d \
  --name flight-agent-docker \
  -p 8001:8001 \
  --env-file .env \
  --memory="512m" \
  --restart unless-stopped \
  guardian-buddy-flight-agent:latest
```

---

### Issue 5: API Key Not Working Inside Container

**Verify environment variables:**
```bash
# Check .env file
cat /opt/flight-agent-docker/.env

# Check container environment
docker exec flight-agent-docker env | grep FA_API_KEY
docker exec flight-agent-docker env | grep GROQ_API_KEY
```

---

## 📊 Monitoring

### Container Resource Usage
```bash
# Real-time stats
docker stats flight-agent-docker

# Detailed inspect
docker inspect flight-agent-docker
```

### Application Logs
```bash
# Follow logs
docker logs flight-agent-docker -f

# Search logs for errors
docker logs flight-agent-docker 2>&1 | grep ERROR

# Count requests
docker logs flight-agent-docker 2>&1 | grep "Request:" | wc -l
```

### Health Monitoring Script
Create a simple health check script:

```bash
nano /opt/flight-agent-docker/health-check.sh
```

```bash
#!/bin/bash
RESPONSE=$(curl -s http://localhost:8001/health)
if [[ $RESPONSE == *"ok"* ]]; then
  echo "✅ Flight Agent is healthy"
  exit 0
else
  echo "❌ Flight Agent is down!"
  docker logs flight-agent-docker --tail 20
  exit 1
fi
```

```bash
chmod +x /opt/flight-agent-docker/health-check.sh
./health-check.sh
```

---

## 🔒 Security Best Practices

### 1. Secure .env File
```bash
# Restrict permissions
chmod 600 /opt/flight-agent-docker/.env

# Verify
ls -la /opt/flight-agent-docker/.env
```

### 2. Run as Non-Root User
The Dockerfile already creates a non-root user `flightagent`:
```dockerfile
RUN useradd --create-home --shell /bin/bash flightagent
USER flightagent
```

### 3. Limit Container Resources
```bash
docker run -d \
  --name flight-agent-docker \
  -p 8001:8001 \
  --env-file .env \
  --memory="512m" \
  --cpus="0.5" \
  --restart unless-stopped \
  guardian-buddy-flight-agent:latest
```

### 4. Enable Docker Content Trust
```bash
export DOCKER_CONTENT_TRUST=1
```

---

## 🔄 Docker Compose Configuration

Your `docker-compose.yml` is already set up. Here's what it does:

```yaml
version: '3.8'

services:
  flight-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flight-agent-docker
    ports:
      - "8001:8001"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
```

**Features:**
- ✅ Auto-restart on failure
- ✅ Health checks every 30s
- ✅ Environment variables from `.env`
- ✅ Port mapping to host

---

## 🆚 Docker vs Manual Deployment Comparison

| Feature | Docker Deployment | Manual Deployment |
|---------|-------------------|-------------------|
| Setup Time | 5 minutes | 15 minutes |
| Dependencies | Isolated in container | System-wide |
| Updates | `docker-compose up -d` | Git pull + supervisor restart |
| Rollback | Change image tag | Git revert + restart |
| Portability | Run anywhere | EC2 specific |
| Resource Usage | ~150 MB RAM | ~100 MB RAM |
| Isolation | Full containerization | Virtual environment |
| Debugging | `docker logs` | `/var/log/flight-agent.log` |

---

## 💰 Cost Impact

Docker on EC2 Free Tier:
- **Same cost as manual deployment** (no additional charges)
- Slightly higher memory usage (~50 MB more)
- Still well within t2.micro limits (1 GB RAM)

---

## 📚 Quick Reference Card

### Essential Commands
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker logs flight-agent-docker -f

# Restart
docker restart flight-agent-docker

# Update
cd /opt/flight-agent-docker && git pull && docker-compose up -d --build

# Health check
curl http://localhost:8001/health

# Container stats
docker stats flight-agent-docker
```

### File Locations
```bash
Application:   /opt/flight-agent-docker/
Dockerfile:    /opt/flight-agent-docker/Dockerfile
Compose File:  /opt/flight-agent-docker/docker-compose.yml
Environment:   /opt/flight-agent-docker/.env
Flight Agent:  /opt/flight-agent-docker/flight_agent/
```

### Endpoints
```bash
Health:      http://54.158.27.0:8001/health
Agent Card:  http://54.158.27.0:8001/agent.json
Flight API:  http://54.158.27.0:8001/a2a (POST)
```

---

## 🎓 Migration from Manual Deployment

If you already have the manual Python deployment running:

### Step 1: Stop Supervisor Service
```bash
sudo supervisorctl stop flight-agent
sudo supervisorctl remove flight-agent
```

### Step 2: Free Up Port 8001
```bash
sudo netstat -tlnp | grep 8001
sudo kill -9 <PID_if_any>
```

### Step 3: Follow Docker Deployment Steps Above
Start from **Step 2: Install Docker on EC2**

### Step 4: Verify Docker Deployment Works
```bash
curl http://localhost:8001/health
```

### Step 5: Remove Old Supervisor Config (Optional)
```bash
sudo rm /etc/supervisor/conf.d/flight-agent.conf
sudo supervisorctl reread
sudo supervisorctl update
```

---

## 🚀 Next Steps

1. ✅ **Set up automated health monitoring** using AWS CloudWatch
2. ✅ **Configure log rotation** for Docker logs
3. ✅ **Set up CI/CD** with GitHub Actions for auto-deployment
4. ✅ **Add HTTPS** with Let's Encrypt and Nginx reverse proxy
5. ✅ **Implement Redis caching** for API responses

---

## 📞 Support

- **GitHub**: https://github.com/rohanpc0701/Codefest_Flightapi
- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/

---

**Deployment Date**: October 11, 2025  
**Instance IP**: 54.158.27.0:8001  
**Status**: 🐳 Ready for Docker deployment


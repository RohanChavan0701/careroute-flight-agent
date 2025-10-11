# Guardian Buddy Flight Agent - AWS EC2 Deployment Guide

## 🎯 Overview

This guide walks you through deploying the Guardian Buddy Flight Agent to AWS EC2 Free Tier. Based on our successful deployment, this service provides real-time flight tracking with AI-powered summaries using the A2A Protocol (JSON-RPC 2.0).

**Live Instance**: `http://54.158.27.0:8001`

---

## 📋 Prerequisites

### AWS Account Setup
- AWS Account with EC2 Free Tier eligibility
- Basic familiarity with AWS Console
- SSH client installed on your local machine

### Required API Keys
- **FlightAware AeroAPI Key**: [Get one here](https://flightaware.com/commercial/aeroapi/)
- **Groq API Key**: [Get one here](https://console.groq.com/)

### Local Requirements
- Git installed
- SSH key pair for EC2 access

---

## 🚀 Step-by-Step Deployment

### Step 1: Launch EC2 Instance

#### 1.1 Navigate to EC2 Dashboard
1. Log into AWS Console
2. Search for "EC2" in the services search bar
3. Click "Launch Instance"

#### 1.2 Configure Instance
```yaml
Name: flight-agent-team
AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
Instance Type: t2.micro (1 vCPU, 1 GB RAM)
Key Pair: Create new key pair or use existing
  - Name: flight-agent-key
  - Type: RSA
  - Format: .pem
  - Download and save securely
```

#### 1.3 Configure Storage
```yaml
Storage: 8 GB gp3 (Free tier eligible)
```

#### 1.4 Configure Security Group
**CRITICAL**: You need to manually add port 8001 after instance creation.

Initial security group (instance creation):
```yaml
Name: flight-agent-sg
Rules:
  - Type: SSH
    Protocol: TCP
    Port: 22
    Source: 0.0.0.0/0 (or your IP for better security)
  
  - Type: HTTP
    Protocol: TCP
    Port: 80
    Source: 0.0.0.0/0
```

**After instance is running**, add this rule in AWS Console:
1. Go to EC2 → Instances → Select your instance
2. Click Security tab → Click security group link
3. Edit inbound rules → Add rule:
   ```yaml
   Type: Custom TCP
   Port: 8001
   Source: 0.0.0.0/0
   Description: Flight Agent API
   ```

#### 1.5 Launch Instance
- Review settings
- Click "Launch Instance"
- **Note the Public IPv4 Address** (e.g., `54.158.27.0`)

---

### Step 2: Connect to EC2 Instance

#### 2.1 Set Key Permissions
```bash
chmod 400 flight-agent-key.pem
```

#### 2.2 SSH into Instance
```bash
ssh -i flight-agent-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Example:
```bash
ssh -i flight-agent-key.pem ubuntu@54.158.27.0
```

---

### Step 3: Prepare EC2 Environment

#### 3.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### 3.2 Install Python 3.11
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

#### 3.3 Install System Dependencies
```bash
sudo apt install -y supervisor nginx curl git
```

---

### Step 4: Deploy Flight Agent Code

#### 4.1 Create Application Directory
```bash
sudo mkdir -p /opt/flight-agent
sudo chown ubuntu:ubuntu /opt/flight-agent
cd /opt/flight-agent
```

#### 4.2 Transfer Code to EC2

**Option A: Using Git (Recommended)**
```bash
cd /opt/flight-agent
git clone https://github.com/rohanpc0701/Codefest_Flightapi.git .
```

**Option B: Using SCP from Local Machine**
```bash
# From your local machine
cd /path/to/Codefest
scp -i flight-agent-key.pem -r flight_agent ubuntu@YOUR_EC2_PUBLIC_IP:/opt/flight-agent/
```

#### 4.3 Install Python Dependencies
```bash
cd /opt/flight-agent/flight_agent
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 5: Configure Environment Variables

#### 5.1 Create Environment File
```bash
cd /opt/flight-agent/flight_agent
nano .env
```

#### 5.2 Add Configuration
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

### Step 6: Configure Supervisor (Process Manager)

#### 6.1 Create Supervisor Config
```bash
sudo nano /etc/supervisor/conf.d/flight-agent.conf
```

#### 6.2 Add Configuration
```ini
[program:flight-agent]
command=/opt/flight-agent/flight_agent/venv/bin/python3.11 -m flight_agent.simple_a2a_server
directory=/opt/flight-agent/flight_agent
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/flight-agent.log
environment=PROVIDER=flightaware,FA_API_KEY=your_flightaware_api_key_here,GROQ_API_KEY=your_groq_api_key_here,A2A_PORT=8001,PYTHONPATH=/opt/flight-agent/flight_agent
```

**Note**: Replace API keys with your actual keys.

#### 6.3 Start Service
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flight-agent
```

#### 6.4 Verify Service is Running
```bash
sudo supervisorctl status flight-agent
```

Expected output:
```
flight-agent                     RUNNING   pid 12345, uptime 0:00:05
```

---

### Step 7: Test the Deployment

#### 7.1 Test Health Endpoint
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status": "ok"}
```

#### 7.2 Test Agent Card
```bash
curl http://localhost:8001/agent.json
```

#### 7.3 Test Flight Status API
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

### Step 8: External Access Configuration

#### 8.1 Verify Security Group Rule for Port 8001
This is **CRITICAL** and is the most common issue.

1. Go to AWS Console → EC2 → Instances
2. Select your instance
3. Click "Security" tab
4. Click on the security group link
5. Click "Edit inbound rules"
6. Verify this rule exists:
   ```yaml
   Type: Custom TCP
   Port: 8001
   Source: 0.0.0.0/0
   ```
7. If not, click "Add rule" and add it
8. Click "Save rules"

#### 8.2 Test External Access
From your **local machine**:

```bash
# Health check
curl http://YOUR_EC2_PUBLIC_IP:8001/health

# Agent card
curl http://YOUR_EC2_PUBLIC_IP:8001/agent.json

# Flight status
curl -X POST http://YOUR_EC2_PUBLIC_IP:8001/a2a \
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

## 🔧 Management Commands

### View Logs
```bash
# Application logs
sudo tail -f /var/log/flight-agent.log

# Supervisor logs
sudo tail -f /var/log/supervisor/supervisord.log
```

### Service Management
```bash
# Check status
sudo supervisorctl status flight-agent

# Restart service
sudo supervisorctl restart flight-agent

# Stop service
sudo supervisorctl stop flight-agent

# Start service
sudo supervisorctl start flight-agent
```

### Update Application Code
```bash
# SSH into EC2
ssh -i flight-agent-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Pull latest code
cd /opt/flight-agent
git pull origin main

# Restart service
sudo supervisorctl restart flight-agent
```

---

## 👥 Team Access Setup

### Share SSH Key with Team Members

#### 1. Distribute the Key File
Share `flight-agent-key.pem` with team members securely (e.g., via encrypted email, secure file sharing)

#### 2. Team Member Setup
```bash
# Set permissions
chmod 400 flight-agent-key.pem

# Connect to EC2
ssh -i flight-agent-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### API Access (No Authentication Required)
All team members can access the API directly:
- **Health**: `http://YOUR_EC2_PUBLIC_IP:8001/health`
- **Agent Card**: `http://YOUR_EC2_PUBLIC_IP:8001/agent.json`
- **Flight API**: `http://YOUR_EC2_PUBLIC_IP:8001/a2a` (POST)

---

## 🐛 Troubleshooting

### Issue 1: Service Won't Start
**Symptoms**: `sudo supervisorctl status` shows `FATAL` or `EXITED`

**Solutions**:
```bash
# Check logs
sudo tail -50 /var/log/flight-agent.log

# Check for import errors
cd /opt/flight-agent/flight_agent
source venv/bin/activate
python3.11 -c "import flight_agent; print('OK')"

# Verify PYTHONPATH
echo $PYTHONPATH

# Restart with logs
sudo supervisorctl restart flight-agent
sudo tail -f /var/log/flight-agent.log
```

### Issue 2: Cannot Connect from Outside
**Symptoms**: `curl` from local machine times out or fails

**Solutions**:
1. **Check Security Group Rule**:
   - AWS Console → EC2 → Security Groups
   - Verify port 8001 is open to `0.0.0.0/0`
   
2. **Check if service is running**:
   ```bash
   sudo supervisorctl status flight-agent
   sudo netstat -tlnp | grep 8001
   ```

3. **Test from EC2 instance itself**:
   ```bash
   curl http://localhost:8001/health
   ```

### Issue 3: Import Errors (Module Not Found)
**Symptoms**: `ModuleNotFoundError: No module named 'flight_agent'`

**Solutions**:
```bash
# Update Supervisor config with PYTHONPATH
sudo nano /etc/supervisor/conf.d/flight-agent.conf

# Ensure this line has PYTHONPATH
environment=PROVIDER=flightaware,...,PYTHONPATH=/opt/flight-agent/flight_agent

# Reload and restart
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart flight-agent
```

### Issue 4: API Key Errors
**Symptoms**: 401 Unauthorized from FlightAware API

**Solutions**:
```bash
# Verify API key is set
cd /opt/flight-agent/flight_agent
source venv/bin/activate
python3.11 -c "from flight_config import config; print(config.FA_API_KEY[:10])"

# Test API key directly
curl -X GET 'https://aeroapi.flightaware.com/aeroapi/flights/AA100?ident_type=designator&start=2025-10-11&end=2025-10-12&max_pages=1' \
  -H 'x-apikey: YOUR_FA_API_KEY'
```

### Issue 5: Port Already in Use
**Symptoms**: `Address already in use` error

**Solutions**:
```bash
# Find process using port 8001
sudo netstat -tlnp | grep 8001
sudo lsof -i :8001

# Kill the process
sudo kill -9 <PID>

# Restart service
sudo supervisorctl restart flight-agent
```

---

## 📊 Monitoring & Performance

### Check Service Health
```bash
# CPU and Memory usage
top -u ubuntu

# Disk usage
df -h

# Network connections
sudo netstat -an | grep 8001

# Recent logs
sudo tail -50 /var/log/flight-agent.log | grep ERROR
```

### API Request Monitoring
```bash
# Watch requests in real-time
sudo tail -f /var/log/flight-agent.log | grep "Request:"

# Count requests by flight number
sudo grep "Request:" /var/log/flight-agent.log | wc -l
```

---

## 💰 Cost Breakdown

### EC2 Free Tier (12 months)
- **Instance**: t2.micro (750 hours/month free)
- **Storage**: 8 GB gp3 (30 GB free)
- **Data Transfer**: 100 GB outbound free per month
- **Estimated Cost**: **$0/month** (within free tier)

### After Free Tier Expires
- **EC2 t2.micro**: ~$8.50/month
- **Storage (8 GB)**: ~$0.80/month
- **Data Transfer**: ~$0.09/GB (after 100 GB)
- **Total**: ~$9-12/month (depending on traffic)

---

## 🔐 Security Best Practices

### 1. SSH Key Management
- Never share the `.pem` file publicly
- Use encrypted channels for team distribution
- Consider using AWS Systems Manager Session Manager instead of SSH

### 2. API Key Security
- Store API keys in environment variables only
- Never commit `.env` files to git
- Rotate keys periodically

### 3. Network Security
- Consider restricting SSH access to specific IP ranges
- Use AWS Security Groups as a firewall
- Enable VPC Flow Logs for monitoring

### 4. Service Security
- Keep Ubuntu and Python packages updated
- Monitor logs for suspicious activity
- Set up CloudWatch alarms for unusual traffic

---

## 📚 Quick Reference

### Service Endpoints
```bash
Health:      http://YOUR_EC2_IP:8001/health
Agent Card:  http://YOUR_EC2_IP:8001/agent.json
Flight API:  http://YOUR_EC2_IP:8001/a2a (POST)
```

### Management Commands
```bash
# Service control
sudo supervisorctl {status|start|stop|restart} flight-agent

# View logs
sudo tail -f /var/log/flight-agent.log

# Update code
cd /opt/flight-agent && git pull && sudo supervisorctl restart flight-agent
```

### Common File Locations
```bash
Application:       /opt/flight-agent/flight_agent/
Environment:       /opt/flight-agent/flight_agent/.env
Supervisor Config: /etc/supervisor/conf.d/flight-agent.conf
Application Logs:  /var/log/flight-agent.log
Supervisor Logs:   /var/log/supervisor/supervisord.log
```

---

## 🎓 Lessons Learned from Our Deployment

### 1. Security Group Configuration is Critical
The most common issue is forgetting to add port 8001 to the security group. **Always verify this first** if external access fails.

### 2. PYTHONPATH is Essential
Due to the module structure, `PYTHONPATH=/opt/flight-agent/flight_agent` must be set in the Supervisor environment variables.

### 3. Use Absolute Imports
Changed from relative imports (`from .config import config`) to absolute imports (`from flight_config import config`) to avoid import issues.

### 4. Test Locally First
Always test `curl http://localhost:8001/health` from the EC2 instance before testing external access.

### 5. Monitor Logs During Deployment
Keep `sudo tail -f /var/log/flight-agent.log` running during initial deployment to catch errors quickly.

---

## 🚀 Next Steps

1. **Set up monitoring**: Configure CloudWatch alarms
2. **Enable HTTPS**: Use Let's Encrypt with Nginx
3. **Add caching**: Implement Redis for API response caching
4. **Scale horizontally**: Add Application Load Balancer for multiple instances
5. **CI/CD**: Set up GitHub Actions for automated deployments

---

## 📞 Support & Resources

- **GitHub Repository**: https://github.com/rohanpc0701/Codefest_Flightapi
- **A2A Protocol**: https://github.com/a2aproject/A2A
- **FlightAware AeroAPI**: https://flightaware.com/commercial/aeroapi/
- **Groq API**: https://console.groq.com/

---

**Deployment Date**: October 11, 2025  
**Instance IP**: 54.158.27.0:8001  
**Status**: ✅ Live and operational


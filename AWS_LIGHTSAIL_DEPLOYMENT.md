# AWS Lightsail Deployment Guide - Guardian Buddy Flight Agent

## 🚀 Deploy to AWS Lightsail

This guide will help you deploy your A2A Flight Agent to AWS Lightsail for production use.

## 📋 Prerequisites

- AWS Account
- AWS CLI installed (optional but recommended)
- SSH key pair for Lightsail
- Your FlightAware API key (you'll need to obtain one from FlightAware)

## 🎯 Step-by-Step Deployment

### Step 1: Create Lightsail Instance

1. **Log into AWS Console**
   - Go to: https://lightsail.aws.amazon.com/

2. **Create Instance**
   - Click "Create instance"
   - **Region**: Choose closest to your users (e.g., us-east-1)
   - **Platform**: Linux/Unix
   - **Blueprint**: OS Only → Ubuntu 22.04 LTS
   - **Instance Plan**: 
     - **Recommended**: $10/month (2 GB RAM, 1 vCPU, 60 GB SSD)
     - **Minimum**: $5/month (1 GB RAM, 1 vCPU, 40 GB SSD)
   - **Instance Name**: `guardian-buddy-flight-agent`

3. **Configure Networking**
   - In instance details, go to "Networking" tab
   - Add firewall rule:
     - **Application**: Custom
     - **Protocol**: TCP
     - **Port**: 8001
     - **Source**: Anywhere (0.0.0.0/0) or restrict to your IP
   - Port 22 (SSH) should already be open

4. **Create and Download SSH Key**
   - AWS will provide an SSH key or you can use existing
   - Download and save it (e.g., `guardian-buddy-key.pem`)

### Step 2: Connect to Your Instance

```bash
# Set permissions on SSH key
chmod 400 guardian-buddy-key.pem

# Connect to instance (replace with your instance IP)
ssh -i guardian-buddy-key.pem ubuntu@YOUR_INSTANCE_IP
```

### Step 3: Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Git
sudo apt-get install -y git

# Install nginx (optional, for reverse proxy)
sudo apt-get install -y nginx

# Install supervisor (for process management)
sudo apt-get install -y supervisor
```

### Step 4: Deploy Your Application

```bash
# Create application directory
sudo mkdir -p /opt/guardian-buddy
sudo chown ubuntu:ubuntu /opt/guardian-buddy
cd /opt/guardian-buddy

# Clone your repository (or upload files via SCP)
# Option 1: Clone from GitHub
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Option 2: Upload via SCP (from your local machine)
# scp -i guardian-buddy-key.pem -r /Users/rohanchavan/Desktop/Codefest/flight_agent ubuntu@YOUR_INSTANCE_IP:/opt/guardian-buddy/
```

### Step 5: Setup Python Environment

```bash
cd /opt/guardian-buddy/flight_agent

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Configure Environment

```bash
# Create production .env file
cat > /opt/guardian-buddy/flight_agent/.env << 'EOF'
# Provider Configuration
PROVIDER=flightaware

# FlightAware AeroAPI Configuration
FA_API_KEY=your_flightaware_api_key_here
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6

# Groq LLM Configuration (optional)
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT_SEC=10

# A2A Server Configuration
A2A_PORT=8001
EOF

# Set proper permissions
chmod 600 /opt/guardian-buddy/flight_agent/.env
```

### Step 7: Setup Supervisor (Process Manager)

```bash
# Create supervisor config
sudo tee /etc/supervisor/conf.d/flight-agent.conf > /dev/null << 'EOF'
[program:flight-agent]
command=/opt/guardian-buddy/flight_agent/venv/bin/python -m a2a_server
directory=/opt/guardian-buddy
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/flight-agent/error.log
stdout_logfile=/var/log/flight-agent/access.log
environment=PROVIDER="flightaware",FA_API_KEY="your_flightaware_api_key_here",A2A_PORT="8001"

[program:flight-agent-worker]
command=/opt/guardian-buddy/flight_agent/venv/bin/python -m a2a_server
directory=/opt/guardian-buddy
user=ubuntu
process_name=%(program_name)s_%(process_num)02d
numprocs=1
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/flight-agent/worker-error.log
stdout_logfile=/var/log/flight-agent/worker-access.log
environment=PROVIDER="flightaware",FA_API_KEY="your_flightaware_api_key_here",A2A_PORT="8001"
EOF

# Create log directory
sudo mkdir -p /var/log/flight-agent
sudo chown ubuntu:ubuntu /var/log/flight-agent

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flight-agent
```

### Step 8: Setup Nginx Reverse Proxy (Optional but Recommended)

```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/flight-agent > /dev/null << 'EOF'
server {
    listen 80;
    server_name YOUR_INSTANCE_IP;  # Replace with your IP or domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8001/health;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/flight-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 9: Setup SSL/HTTPS (Optional but Recommended for Production)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate (requires a domain name)
# Replace YOUR_DOMAIN with your actual domain
sudo certbot --nginx -d YOUR_DOMAIN --non-interactive --agree-tos -m YOUR_EMAIL

# Auto-renewal is automatically configured by certbot
```

### Step 10: Verify Deployment

```bash
# Check supervisor status
sudo supervisorctl status flight-agent

# Check nginx status
sudo systemctl status nginx

# Check logs
sudo tail -f /var/log/flight-agent/access.log

# Test health endpoint
curl http://localhost:8001/health

# Test from outside (replace with your instance IP)
curl http://YOUR_INSTANCE_IP/health
```

## 🧪 Testing Your Deployment

### From Your Local Machine

```bash
# Health check
curl http://YOUR_INSTANCE_IP/health | jq

# Agent Card
curl http://YOUR_INSTANCE_IP/agent.json | jq

# Test flight status
curl -X POST http://YOUR_INSTANCE_IP/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA123",
      "departure_date": "2025-10-12"
    },
    "id": "test-1"
  }' | jq
```

## 📊 Monitoring & Maintenance

### View Logs

```bash
# Application logs
sudo tail -f /var/log/flight-agent/access.log
sudo tail -f /var/log/flight-agent/error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u supervisor -f
```

### Restart Services

```bash
# Restart flight agent
sudo supervisorctl restart flight-agent

# Restart nginx
sudo systemctl restart nginx

# Restart all
sudo supervisorctl restart all
```

### Update Application

```bash
# Pull latest code
cd /opt/guardian-buddy
git pull origin main

# Reinstall dependencies (if needed)
source flight_agent/venv/bin/activate
pip install -r flight_agent/requirements.txt

# Restart service
sudo supervisorctl restart flight-agent
```

## 💰 Cost Estimation

### Lightsail Instance
- **$5/month**: 1 GB RAM, 1 vCPU (minimum)
- **$10/month**: 2 GB RAM, 1 vCPU (recommended)
- **$20/month**: 4 GB RAM, 2 vCPU (production)

### FlightAware AeroAPI
- **$89/month**: Basic plan (10,000 queries)
- **$199/month**: Plus plan (25,000 queries)

### Data Transfer
- First 1 TB/month: Free with Lightsail
- Additional: $0.09/GB

**Total Monthly Cost (Recommended)**: $99 ($10 Lightsail + $89 FlightAware)

## 🔒 Security Best Practices

1. **Firewall Rules**
   ```bash
   # Only allow necessary ports
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **SSH Key Only** (Disable password authentication)
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

3. **Automatic Security Updates**
   ```bash
   sudo apt-get install -y unattended-upgrades
   sudo dpkg-reconfigure -plow unattended-upgrades
   ```

4. **Fail2Ban** (Prevent brute force)
   ```bash
   sudo apt-get install -y fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo supervisorctl tail -f flight-agent stderr

# Check if port is in use
sudo netstat -tulpn | grep 8001

# Manually test
cd /opt/guardian-buddy
source flight_agent/venv/bin/activate
python -m a2a_server
```

### Can't Connect from Outside
```bash
# Check firewall
sudo ufw status

# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check Lightsail firewall rules in AWS console
```

### High Memory Usage
```bash
# Monitor resources
htop

# Reduce workers in supervisor config
sudo nano /etc/supervisor/conf.d/flight-agent.conf
# Change numprocs to 1
```

## 📱 Quick Deploy Script

Create this script on your Lightsail instance for easy deployment:

```bash
#!/bin/bash
# deploy.sh - Quick deployment script

set -e

echo "🚀 Deploying Guardian Buddy Flight Agent..."

# Pull latest code
cd /opt/guardian-buddy
git pull origin main

# Activate venv
source flight_agent/venv/bin/activate

# Install dependencies
pip install -r flight_agent/requirements.txt

# Restart service
sudo supervisorctl restart flight-agent

# Wait for service to start
sleep 3

# Test health
curl -s http://localhost:8001/health | jq

echo "✅ Deployment complete!"
```

## 🌐 Custom Domain Setup (Optional)

1. **Register Domain** (e.g., from Route 53, Namecheap, etc.)

2. **Create A Record**
   - Point your domain to Lightsail instance IP
   - Example: `api.guardianbuddy.com` → `YOUR_INSTANCE_IP`

3. **Update Nginx Config**
   ```bash
   sudo nano /etc/nginx/sites-available/flight-agent
   # Change server_name to your domain
   ```

4. **Get SSL Certificate**
   ```bash
   sudo certbot --nginx -d api.guardianbuddy.com
   ```

## 📚 Additional Resources

- **AWS Lightsail Docs**: https://docs.aws.amazon.com/lightsail/
- **Supervisor Docs**: http://supervisord.org/
- **Nginx Docs**: https://nginx.org/en/docs/
- **FlightAware API**: https://www.flightaware.com/commercial/aeroapi/

## ✅ Deployment Checklist

- [ ] Lightsail instance created ($10/month recommended)
- [ ] Firewall rules configured (ports 22, 80, 443, 8001)
- [ ] SSH key downloaded and working
- [ ] Dependencies installed (Python 3.11, Git, Nginx, Supervisor)
- [ ] Application code deployed
- [ ] Environment variables configured (.env file)
- [ ] Supervisor configured and running
- [ ] Nginx configured (optional but recommended)
- [ ] SSL/HTTPS configured (optional but recommended)
- [ ] Health endpoint tested
- [ ] Flight status API tested
- [ ] Monitoring/logs verified
- [ ] Documentation updated with production URL

---

**Your Guardian Buddy Flight Agent will be accessible at:**
- HTTP: `http://YOUR_INSTANCE_IP:8001` or `http://YOUR_INSTANCE_IP` (with nginx)
- HTTPS: `https://YOUR_DOMAIN` (if SSL configured)

**Good luck with your deployment! 🎉**


# AWS EC2 Free Tier Deployment - Flight Agent

## 🆓 Free Tier Details
- **Instance**: t2.micro (1 vCPU, 1 GB RAM)
- **Hours**: 750 hours/month (24/7 for ~31 days)
- **Storage**: 30 GB EBS storage
- **Duration**: 12 months from AWS account creation
- **Cost**: $0/month (within free tier limits)

## 🚀 Quick Deploy Steps

### Step 1: Launch EC2 Instance
1. Go to AWS Console → EC2
2. Click "Launch Instance"
3. Configure:
   - **Name**: `flight-agent-free`
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type**: t2.micro (Free tier eligible)
   - **Key Pair**: Create new or use existing
   - **Security Group**: 
     - SSH (22) from your IP
     - HTTP (80) from anywhere
     - Custom TCP (8001) from anywhere
   - **Storage**: 30 GB (Free tier limit)

### Step 2: Connect and Deploy
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install other dependencies
sudo apt install -y curl nginx supervisor

# Create application directory
sudo mkdir -p /opt/flight-agent
sudo chown ubuntu:ubuntu /opt/flight-agent
cd /opt/flight-agent

# Upload your code (from local machine)
# scp -i your-key.pem -r flight_agent ubuntu@YOUR_EC2_IP:/opt/flight-agent/
```

### Step 3: Setup Application
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r flight_agent/requirements.txt

# Create environment file
cat > .env << EOF
PROVIDER=flightaware
FA_API_KEY=your_flightaware_api_key_here
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT_SEC=10
A2A_PORT=8001
EOF

# Test the application
python -m flight_agent.simple_a2a_server
```

### Step 4: Configure Supervisor
```bash
# Create supervisor config
sudo tee /etc/supervisor/conf.d/flight-agent.conf > /dev/null << EOF
[program:flight-agent]
command=/opt/flight-agent/venv/bin/python -m flight_agent.simple_a2a_server
directory=/opt/flight-agent
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/flight-agent.log
environment=PROVIDER=flightaware,FA_API_KEY=your_flightaware_api_key_here,GROQ_API_KEY=your_groq_api_key_here,A2A_PORT=8001
EOF

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flight-agent
```

### Step 5: Configure Nginx
```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/flight-agent > /dev/null << EOF
server {
    listen 80;
    server_name YOUR_EC2_IP;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/flight-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🧪 Test Your Deployment
```bash
# Test health endpoint
curl http://YOUR_EC2_IP/health

# Test flight status
curl -X POST http://YOUR_EC2_IP/a2a \
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

## 💰 Cost Breakdown
- **EC2 t2.micro**: $0/month (Free tier)
- **EBS 30GB**: $0/month (Free tier)
- **Data Transfer**: 1GB/month free
- **Total**: $0/month for 12 months

## ⚠️ Free Tier Limits
- **Instance Hours**: 750/month (enough for 24/7)
- **Storage**: 30GB (sufficient for app)
- **Data Transfer**: 1GB/month outbound
- **Duration**: 12 months from account creation

## 🔧 Management Commands
```bash
# Check service status
sudo supervisorctl status flight-agent

# View logs
sudo tail -f /var/log/flight-agent.log

# Restart service
sudo supervisorctl restart flight-agent

# Update code
cd /opt/flight-agent
# Upload new files
sudo supervisorctl restart flight-agent
```

## 🎯 Benefits
- ✅ Completely free for 12 months
- ✅ Full control over the server
- ✅ Easy to scale later
- ✅ Familiar AWS environment
- ✅ Perfect for development/testing

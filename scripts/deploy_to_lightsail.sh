#!/bin/bash
# deploy_to_lightsail.sh
# Automated deployment script for AWS Lightsail

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}║        🚀 Guardian Buddy - AWS Lightsail Deployment              ║${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running on Lightsail instance
if [ ! -f /etc/update-motd.d/70-available-updates ]; then
    echo -e "${YELLOW}⚠️  This script is designed to run ON the Lightsail instance.${NC}"
    echo -e "${YELLOW}   Please SSH into your instance first:${NC}"
    echo ""
    echo "   ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP"
    echo ""
    echo -e "${YELLOW}   Then upload and run this script on the instance.${NC}"
    echo ""
    exit 1
fi

# Configuration
APP_DIR="/opt/guardian-buddy"
VENV_DIR="$APP_DIR/flight_agent/venv"
FA_API_KEY="your_flightaware_api_key_here"

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 1: Update System${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sudo apt-get update
sudo apt-get upgrade -y

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 2: Install Dependencies${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Install Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
else
    echo "✅ Python 3.11 already installed"
fi

# Install other dependencies
sudo apt-get install -y git nginx supervisor

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 3: Create Application Directory${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sudo mkdir -p $APP_DIR
sudo chown ubuntu:ubuntu $APP_DIR

echo "✅ Created $APP_DIR"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 4: Deploy Application Files${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo "ℹ️  Upload your code using one of these methods:"
echo ""
echo "Method 1 - SCP (from your local machine):"
echo "  scp -i your-key.pem -r /Users/rohanchavan/Desktop/Codefest/flight_agent ubuntu@YOUR_IP:$APP_DIR/"
echo ""
echo "Method 2 - Git clone:"
echo "  cd $APP_DIR"
echo "  git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
echo ""
read -p "Have you uploaded the code? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please upload code first, then run this script again."
    exit 1
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 5: Setup Python Environment${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd $APP_DIR/flight_agent

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    python3.11 -m venv venv
    echo "✅ Created virtual environment"
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Installed dependencies"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 6: Configure Environment${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cat > $APP_DIR/flight_agent/.env << EOF
# Provider Configuration
PROVIDER=flightaware

# FlightAware AeroAPI Configuration
FA_API_KEY=$FA_API_KEY
FA_BASE=https://aeroapi.flightaware.com/aeroapi
FA_TIMEOUT_SEC=6

# Groq LLM Configuration
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TIMEOUT_SEC=10

# A2A Server Configuration
A2A_PORT=8001
EOF

chmod 600 $APP_DIR/flight_agent/.env
echo "✅ Created .env file"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 7: Setup Supervisor${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sudo tee /etc/supervisor/conf.d/flight-agent.conf > /dev/null << EOF
[program:flight-agent]
command=$VENV_DIR/bin/python -m a2a_server
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/flight-agent/error.log
stdout_logfile=/var/log/flight-agent/access.log
environment=PROVIDER="flightaware",FA_API_KEY="$FA_API_KEY",A2A_PORT="8001"
EOF

# Create log directory
sudo mkdir -p /var/log/flight-agent
sudo chown ubuntu:ubuntu /var/log/flight-agent

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flight-agent

echo "✅ Supervisor configured and started"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 8: Setup Nginx${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

sudo tee /etc/nginx/sites-available/flight-agent > /dev/null << EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8001/health;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/flight-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Nginx configured and started"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Step 9: Verify Deployment${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sleep 3

# Test health endpoint
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ Service is healthy"
else
    echo "❌ Service health check failed"
    sudo supervisorctl status flight-agent
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}║        ✅ DEPLOYMENT COMPLETE!                                     ║${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Your Guardian Buddy Flight Agent is now running!${NC}"
echo ""
echo "🌐 Public URL: http://$PUBLIC_IP"
echo ""
echo "📊 Test endpoints:"
echo "   Health: curl http://$PUBLIC_IP/health"
echo "   Agent Card: curl http://$PUBLIC_IP/agent.json"
echo ""
echo "📝 View logs:"
echo "   sudo tail -f /var/log/flight-agent/access.log"
echo "   sudo supervisorctl status flight-agent"
echo ""
echo "🔄 Manage service:"
echo "   sudo supervisorctl restart flight-agent"
echo "   sudo supervisorctl stop flight-agent"
echo "   sudo supervisorctl start flight-agent"
echo ""
echo -e "${GREEN}🎉 Ready for production!${NC}"


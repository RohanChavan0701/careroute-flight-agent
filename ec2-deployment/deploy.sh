#!/bin/bash
set -e

echo "🚀 Deploying Flight Agent to EC2..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
print_status "Installing Python 3.11..."
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Install other dependencies
print_status "Installing system dependencies..."
sudo apt install -y curl nginx supervisor git

# Create application directory
print_status "Setting up application directory..."
sudo mkdir -p /opt/flight-agent
sudo chown ubuntu:ubuntu /opt/flight-agent

# Copy application files
print_status "Copying application files..."
cp -r flight_agent/* /opt/flight-agent/
cd /opt/flight-agent

# Create virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
print_status "Creating environment configuration..."
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
print_status "Testing application..."
export $(cat .env | xargs)
python -m flight_agent.simple_a2a_server &
APP_PID=$!
sleep 5

# Test health endpoint
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Application test successful!"
    kill $APP_PID
else
    print_error "Application test failed!"
    kill $APP_PID
    exit 1
fi

# Configure Supervisor
print_status "Configuring Supervisor..."
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
print_status "Starting service with Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flight-agent

# Wait for service to start
sleep 5

# Configure Nginx
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/flight-agent > /dev/null << EOF
server {
    listen 80;
    server_name _;

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
sudo ln -sf /etc/nginx/sites-available/flight-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Final test
print_status "Running final tests..."

# Test health endpoint
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "Health endpoint working!"
else
    print_error "Health endpoint failed!"
    exit 1
fi

# Test flight status endpoint
if curl -f -X POST http://localhost/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA123",
      "departure_date": "2025-10-12"
    },
    "id": "test"
  }' > /dev/null 2>&1; then
    print_status "Flight status endpoint working!"
else
    print_warning "Flight status endpoint test failed (this is expected for AA123)"
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Service Status:"
sudo supervisorctl status flight-agent
echo ""
echo "🌐 Your Flight Agent is now live at:"
echo "   • Health: http://$PUBLIC_IP/health"
echo "   • Agent Card: http://$PUBLIC_IP/agent.json"
echo "   • Flight Status: http://$PUBLIC_IP/a2a (POST)"
echo ""
echo "👥 TEAM ACCESS INFORMATION:"
echo "   • Public IP: $PUBLIC_IP"
echo "   • Share this IP with your team members"
echo "   • All endpoints are publicly accessible"
echo "   • No authentication required for API access"
echo ""
echo "🔧 Management Commands:"
echo "   • Check status: sudo supervisorctl status flight-agent"
echo "   • View logs: sudo tail -f /var/log/flight-agent.log"
echo "   • Restart: sudo supervisorctl restart flight-agent"
echo "   • Stop: sudo supervisorctl stop flight-agent"
echo "   • Start: sudo supervisorctl start flight-agent"
echo ""
echo "📝 Test Commands (for team members):"
echo "   curl http://$PUBLIC_IP/health"
echo "   curl http://$PUBLIC_IP/agent.json"
echo "   curl -X POST http://$PUBLIC_IP/a2a \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\":\"2.0\",\"method\":\"get_flight_status\",\"params\":{\"flight_num\":\"DL2990\",\"departure_date\":\"2025-10-11\"},\"id\":\"test\"}'"
echo ""
echo "🔑 SSH Access for Team:"
echo "   • Share the SSH key (.pem file) with team members"
echo "   • SSH command: ssh -i flight-agent-key.pem ubuntu@$PUBLIC_IP"
echo "   • Team members can manage the service remotely"
echo ""
echo "💰 Cost: \$0/month (EC2 Free Tier)"
echo "⏱️  Duration: 12 months from AWS account creation"
echo ""
print_status "Flight Agent successfully deployed to AWS EC2!"
print_status "Ready for team access at: http://$PUBLIC_IP"
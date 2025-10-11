#!/bin/bash
# HTTPS Setup with Nginx and Let's Encrypt for Flight Agent
# This script configures Nginx as a reverse proxy with SSL/TLS

set -e

echo "🔒 Setting up HTTPS with Nginx and Let's Encrypt..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if domain name is provided
if [ -z "$1" ]; then
    print_error "Domain name required!"
    echo ""
    echo "Usage: $0 <your-domain.com>"
    echo ""
    echo "Example: $0 flight-agent.example.com"
    echo ""
    echo "⚠️  Make sure your domain's A record points to: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
    echo ""
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@${DOMAIN}"}

print_info "Domain: $DOMAIN"
print_info "Email: $EMAIL"
echo ""

# Install Nginx
print_info "Installing Nginx..."
sudo apt-get update -qq
sudo apt-get install -y nginx
print_status "Nginx installed"

# Install Certbot
print_info "Installing Certbot..."
sudo apt-get install -y certbot python3-certbot-nginx
print_status "Certbot installed"

# Stop Nginx to free port 80
sudo systemctl stop nginx

# Create Nginx configuration
print_info "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/flight-agent > /dev/null << NGINX_EOF
# Flight Agent - HTTP (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Flight Agent - HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

    # SSL certificates (will be created by Certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # SSL configuration (Mozilla Modern)
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS (optional, uncomment after testing)
    # add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/flight-agent-access.log;
    error_log /var/log/nginx/flight-agent-error.log;

    # Proxy settings
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        
        # Proxy headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://localhost:8001/health;
        access_log off;
    }

    # Rate limiting (optional)
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    location /a2a {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8001/a2a;
    }
}
NGINX_EOF
print_status "Nginx configuration created"

# Enable the site
sudo ln -sf /etc/nginx/sites-available/flight-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_info "Testing Nginx configuration..."
if sudo nginx -t; then
    print_status "Nginx configuration valid"
else
    print_error "Nginx configuration invalid!"
    exit 1
fi

# Create webroot for certbot
sudo mkdir -p /var/www/certbot

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
print_status "Nginx started"

# Obtain SSL certificate
print_info "Obtaining SSL certificate from Let's Encrypt..."
echo ""
print_info "This may take a minute..."
echo ""

sudo certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    --domain ${DOMAIN} \
    --non-interactive || {
        print_error "Failed to obtain SSL certificate!"
        echo ""
        echo "Common issues:"
        echo "  1. Domain doesn't point to this server's IP"
        echo "  2. Port 80 is blocked by firewall"
        echo "  3. Domain validation failed"
        echo ""
        echo "Check DNS: dig ${DOMAIN}"
        echo "Expected IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
        exit 1
    }

print_status "SSL certificate obtained!"

# Reload Nginx with SSL
sudo systemctl reload nginx
print_status "Nginx reloaded with SSL"

# Set up auto-renewal
print_info "Setting up certificate auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
print_status "Auto-renewal configured"

# Create renewal hook
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null << 'HOOK_EOF'
#!/bin/bash
systemctl reload nginx
HOOK_EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
print_status "Renewal hook created"

# Test auto-renewal (dry run)
print_info "Testing certificate renewal..."
sudo certbot renew --dry-run || print_error "Renewal test failed (not critical)"

# Update Security Group reminder
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_status "HTTPS Setup Complete! 🔒"
echo ""
echo "🎯 Your Flight Agent is now available at:"
echo "   • HTTPS: https://${DOMAIN}"
echo "   • HTTP: http://${DOMAIN} (redirects to HTTPS)"
echo ""
echo "📋 Endpoints:"
echo "   • Health: https://${DOMAIN}/health"
echo "   • Agent Card: https://${DOMAIN}/agent.json"
echo "   • Flight API: https://${DOMAIN}/a2a"
echo ""
echo "🔒 SSL Certificate:"
echo "   • Issuer: Let's Encrypt"
echo "   • Valid: 90 days"
echo "   • Auto-renewal: Enabled (runs twice daily)"
echo ""
echo "⚠️  IMPORTANT: Update AWS Security Group"
echo "   Add inbound rule for HTTPS:"
echo "   • Type: HTTPS"
echo "   • Protocol: TCP"
echo "   • Port: 443"
echo "   • Source: 0.0.0.0/0"
echo ""
echo "🔧 Management Commands:"
echo "   • Check status: sudo systemctl status nginx"
echo "   • Reload config: sudo nginx -s reload"
echo "   • View logs: sudo tail -f /var/log/nginx/flight-agent-access.log"
echo "   • Test renewal: sudo certbot renew --dry-run"
echo "   • Renew now: sudo certbot renew"
echo ""
echo "🧪 Test your setup:"
echo "   curl https://${DOMAIN}/health"
echo "   curl -X POST https://${DOMAIN}/a2a \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\":\"2.0\",\"method\":\"get_flight_status\",\"params\":{\"flight_num\":\"DL2990\",\"departure_date\":\"2025-10-11\"},\"id\":\"test\"}'"
echo ""
print_status "Ready for secure production traffic! 🚀"


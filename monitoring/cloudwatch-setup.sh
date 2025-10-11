#!/bin/bash
# CloudWatch Monitoring Setup for Flight Agent Docker Container
# This script sets up CloudWatch monitoring for the EC2 instance and Docker container

set -e

echo "📊 Setting up CloudWatch Monitoring..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Install CloudWatch Agent
print_info "Installing CloudWatch Agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb
print_status "CloudWatch Agent installed"

# Create CloudWatch config
print_info "Creating CloudWatch configuration..."
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/config.json > /dev/null << 'EOF'
{
  "metrics": {
    "namespace": "FlightAgent",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          },
          {
            "name": "cpu_usage_active",
            "rename": "CPU_ACTIVE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/flight-agent-docker.log",
            "log_group_name": "/aws/ec2/flight-agent",
            "log_stream_name": "{instance_id}/docker-logs",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF
print_status "CloudWatch configuration created"

# Create log file
print_info "Setting up Docker log forwarding..."
sudo touch /var/log/flight-agent-docker.log
sudo chmod 666 /var/log/flight-agent-docker.log

# Add Docker log forwarding to docker-compose
cd /opt/flight-agent-docker
if ! grep -q "logging:" docker-compose.yml; then
    print_info "Adding logging configuration to docker-compose.yml..."
    # Backup original
    cp docker-compose.yml docker-compose.yml.backup
    
    # Add logging configuration
    cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  flight-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: guardian-buddy-flight-agent
    ports:
      - "8001:8001"
    env_file:
      - .env
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "flight-agent"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

COMPOSE_EOF
    print_status "Docker Compose logging configured"
fi

# Create health check script
print_info "Creating health check script..."
sudo tee /opt/flight-agent-docker/healthcheck.sh > /dev/null << 'HEALTH_EOF'
#!/bin/bash
# Health check script for Flight Agent

LOG_FILE="/var/log/flight-agent-docker.log"

# Check if container is running
if ! docker ps | grep -q guardian-buddy-flight-agent; then
    echo "$(date): ERROR - Container is not running" >> $LOG_FILE
    exit 1
fi

# Check health endpoint
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)

if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    echo "$(date): OK - Health check passed (HTTP $HEALTH_RESPONSE)" >> $LOG_FILE
    exit 0
else
    echo "$(date): ERROR - Health check failed (HTTP $HEALTH_RESPONSE)" >> $LOG_FILE
    exit 1
fi
HEALTH_EOF

sudo chmod +x /opt/flight-agent-docker/healthcheck.sh
print_status "Health check script created"

# Create cron job for health checks (every 5 minutes)
print_info "Setting up automated health checks..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/flight-agent-docker/healthcheck.sh") | crontab -
print_status "Health checks scheduled"

# Create metric collection script
print_info "Creating metric collection script..."
sudo tee /opt/flight-agent-docker/collect-metrics.sh > /dev/null << 'METRICS_EOF'
#!/bin/bash
# Collect and send custom metrics to CloudWatch

NAMESPACE="FlightAgent"
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)

# Get container stats
CONTAINER_STATS=$(docker stats guardian-buddy-flight-agent --no-stream --format "{{.CPUPerc}},{{.MemPerc}}")
CPU_USAGE=$(echo $CONTAINER_STATS | cut -d',' -f1 | tr -d '%')
MEM_USAGE=$(echo $CONTAINER_STATS | cut -d',' -f2 | tr -d '%')

# Send to CloudWatch
aws cloudwatch put-metric-data \
    --namespace $NAMESPACE \
    --metric-name ContainerCPU \
    --value $CPU_USAGE \
    --unit Percent \
    --dimensions Instance=$INSTANCE_ID

aws cloudwatch put-metric-data \
    --namespace $NAMESPACE \
    --metric-name ContainerMemory \
    --value $MEM_USAGE \
    --unit Percent \
    --dimensions Instance=$INSTANCE_ID

# Count requests in last 5 minutes
REQUEST_COUNT=$(docker logs guardian-buddy-flight-agent --since 5m 2>&1 | grep -c "Request:")

aws cloudwatch put-metric-data \
    --namespace $NAMESPACE \
    --metric-name RequestCount \
    --value $REQUEST_COUNT \
    --unit Count \
    --dimensions Instance=$INSTANCE_ID

echo "$(date): Metrics sent - CPU: ${CPU_USAGE}%, Memory: ${MEM_USAGE}%, Requests: ${REQUEST_COUNT}"
METRICS_EOF

sudo chmod +x /opt/flight-agent-docker/collect-metrics.sh
print_status "Metric collection script created"

# Schedule metric collection (every 5 minutes)
print_info "Scheduling metric collection..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/flight-agent-docker/collect-metrics.sh >> /var/log/flight-agent-metrics.log 2>&1") | crontab -
print_status "Metric collection scheduled"

# Create CloudWatch dashboard JSON
print_info "Creating CloudWatch Dashboard configuration..."
cat > /opt/flight-agent-docker/cloudwatch-dashboard.json << 'DASHBOARD_EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["FlightAgent", "ContainerCPU"],
          [".", "ContainerMemory"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Container Resources",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["FlightAgent", "RequestCount", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Requests (5 min)"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/ec2/flight-agent'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
        "region": "us-east-1",
        "title": "Recent Errors"
      }
    }
  ]
}
DASHBOARD_EOF
print_status "Dashboard configuration created"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_status "CloudWatch Monitoring Setup Complete!"
echo ""
echo "📊 What was configured:"
echo "   • CloudWatch Agent installed and configured"
echo "   • Docker logs forwarding to CloudWatch"
echo "   • Automated health checks (every 5 minutes)"
echo "   • Custom metrics collection (CPU, Memory, Requests)"
echo "   • Cron jobs for monitoring"
echo ""
echo "🎯 Next Steps:"
echo "   1. Install AWS CLI if not already installed:"
echo "      curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
echo "      unzip awscliv2.zip && sudo ./aws/install"
echo ""
echo "   2. Configure AWS credentials:"
echo "      aws configure"
echo ""
echo "   3. Start CloudWatch Agent:"
echo "      sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \\"
echo "        -a fetch-config \\"
echo "        -m ec2 \\"
echo "        -s \\"
echo "        -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json"
echo ""
echo "   4. Create CloudWatch Dashboard (optional):"
echo "      aws cloudwatch put-dashboard \\"
echo "        --dashboard-name FlightAgentMonitoring \\"
echo "        --dashboard-body file:///opt/flight-agent-docker/cloudwatch-dashboard.json"
echo ""
echo "   5. Set up CloudWatch Alarms:"
echo "      aws cloudwatch put-metric-alarm \\"
echo "        --alarm-name flight-agent-high-cpu \\"
echo "        --alarm-description 'Alert when CPU exceeds 80%' \\"
echo "        --metric-name ContainerCPU \\"
echo "        --namespace FlightAgent \\"
echo "        --statistic Average \\"
echo "        --period 300 \\"
echo "        --threshold 80 \\"
echo "        --comparison-operator GreaterThanThreshold \\"
echo "        --evaluation-periods 2"
echo ""
echo "📋 Log Files:"
echo "   • Health checks: /var/log/flight-agent-docker.log"
echo "   • Metrics: /var/log/flight-agent-metrics.log"
echo "   • Docker logs: docker logs guardian-buddy-flight-agent"
echo ""
echo "🔍 Monitor your agent:"
echo "   • Health check: /opt/flight-agent-docker/healthcheck.sh"
echo "   • View logs: tail -f /var/log/flight-agent-docker.log"
echo "   • Container stats: docker stats guardian-buddy-flight-agent"
echo ""
print_status "Ready for monitoring! 🎉"


# Fly.io Deployment - Flight Agent

## 🆓 Free Tier Details
- **VMs**: 3 shared-CPU VMs
- **RAM**: 256MB per VM
- **Storage**: 3GB persistent volume
- **Data Transfer**: 160GB/month
- **Duration**: Always free
- **Cost**: $0/month (within limits)

## 🚀 Quick Deploy Steps

### Step 1: Install Fly CLI
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Add to PATH
export PATH="$HOME/.fly/bin:$PATH"

# Login to Fly.io
fly auth login
```

### Step 2: Create Fly App
```bash
# Initialize Fly app
fly launch --no-deploy

# This creates fly.toml configuration
```

### Step 3: Configure fly.toml
```toml
# fly.toml
app = "flight-agent"
primary_region = "iad"

[build]

[env]
  PROVIDER = "flightaware"
  FA_API_KEY = "your_flightaware_api_key_here"
  GROQ_API_KEY = "your_groq_api_key_here"
  A2A_PORT = "8001"

[http_service]
  internal_port = 8001
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### Step 4: Deploy to Fly.io
```bash
# Deploy the application
fly deploy

# Check deployment status
fly status

# View logs
fly logs
```

### Step 5: Configure Custom Domain (Optional)
```bash
# Add custom domain
fly certs add your-domain.com

# Check certificate status
fly certs show your-domain.com
```

## 🧪 Test Your Deployment
```bash
# Get app URL
fly info

# Test health endpoint
curl https://flight-agent.fly.dev/health

# Test flight status
curl -X POST https://flight-agent.fly.dev/a2a \
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
- **Fly.io**: $0/month (Free tier)
- **Data Transfer**: 160GB/month free
- **Storage**: 3GB free
- **Total**: $0/month (within limits)

## ⚠️ Free Tier Limits
- **VMs**: 3 shared-CPU VMs
- **RAM**: 256MB per VM
- **Storage**: 3GB persistent
- **Data Transfer**: 160GB/month
- **Duration**: Always free within limits

## 🔧 Management Commands
```bash
# Check app status
fly status

# View logs
fly logs

# Scale app
fly scale count 1

# Update app
fly deploy

# SSH into app
fly ssh console

# View app info
fly info

# Delete app
fly apps destroy flight-agent
```

## 🎯 Benefits
- ✅ Global edge deployment
- ✅ Auto-scaling
- ✅ HTTPS by default
- ✅ Docker-native
- ✅ No server management
- ✅ Generous free tier
- ✅ Fast deployment

## 📊 Usage Estimation
- **Light usage**: ~100 requests/day = Well within free tier
- **Medium usage**: ~500 requests/day = Within free tier
- **Heavy usage**: 1000+ requests/day = May exceed free tier

## 🔄 CI/CD Pipeline (Optional)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Fly.io
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Fly CLI
        uses: superfly/flyctl-actions/setup-flyctl@master
      - name: Deploy to Fly
        run: fly deploy
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

## 🌍 Global Deployment
```bash
# Deploy to multiple regions
fly regions add nrt  # Tokyo
fly regions add lhr  # London
fly regions add syd  # Sydney

# Check regions
fly regions list
```

## 🔒 Security Features
- ✅ Automatic HTTPS
- ✅ DDoS protection
- ✅ Firewall rules
- ✅ Private networking
- ✅ Secrets management

## 📈 Scaling Options
```bash
# Scale horizontally
fly scale count 3

# Scale vertically (paid)
fly scale memory 512
fly scale cpu 2

# Auto-scaling
fly autoscale set min=1 max=5
```

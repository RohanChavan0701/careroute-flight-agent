# AWS Lightsail Quick Start - 5 Minute Deploy

## 🚀 Deploy in 5 Steps

### Step 1: Create Lightsail Instance (2 minutes)

1. Go to: https://lightsail.aws.amazon.com/
2. Click **"Create instance"**
3. Select:
   - **Region**: us-east-1 (or closest to you)
   - **Platform**: Linux/Unix
   - **Blueprint**: Ubuntu 22.04 LTS
   - **Plan**: $10/month (2 GB RAM)
4. **Name**: `guardian-buddy`
5. Click **"Create instance"**
6. Download SSH key → Save as `guardian-key.pem`

### Step 2: Configure Firewall (30 seconds)

1. Click on your instance
2. Go to **"Networking"** tab
3. Click **"Add rule"** under IPv4 Firewall:
   - **Application**: Custom
   - **Protocol**: TCP
   - **Port**: 8001
4. Click **"Create"**

### Step 3: Upload Code (1 minute)

```bash
# From your local machine
cd /Users/rohanchavan/Desktop/Codefest

# Set key permissions
chmod 400 guardian-key.pem

# Upload flight_agent
scp -i guardian-key.pem -r flight_agent ubuntu@YOUR_IP:/tmp/

# Upload deployment script
scp -i guardian-key.pem scripts/deploy_to_lightsail.sh ubuntu@YOUR_IP:~/
```

Replace `YOUR_IP` with your instance's IP (shown in Lightsail console).

### Step 4: Run Deployment Script (2 minutes)

```bash
# SSH into your instance
ssh -i guardian-key.pem ubuntu@YOUR_IP

# Move files
sudo mkdir -p /opt/guardian-buddy
sudo chown ubuntu:ubuntu /opt/guardian-buddy
mv /tmp/flight_agent /opt/guardian-buddy/

# Run deployment
chmod +x ~/deploy_to_lightsail.sh
./deploy_to_lightsail.sh
```

The script will:
- Install Python 3.11
- Setup virtual environment
- Install dependencies
- Configure Supervisor & Nginx
- Start your service

### Step 5: Test It! (30 seconds)

```bash
# On your instance or local machine
curl http://YOUR_IP/health

# Test flight status
curl -X POST http://YOUR_IP/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "AA123",
      "departure_date": "2025-10-12"
    },
    "id": "test"
  }' | jq
```

## ✅ Done!

Your Guardian Buddy Flight Agent is live at: `http://YOUR_IP`

## 🔧 Common Commands

```bash
# View logs
sudo tail -f /var/log/flight-agent/access.log

# Restart service
sudo supervisorctl restart flight-agent

# Check status
sudo supervisorctl status flight-agent

# Test health
curl http://YOUR_IP/health
```

## 💰 Monthly Cost

- Lightsail: $10/month (2 GB RAM)
- FlightAware API: $89/month (10,000 queries)
- **Total**: $99/month

## 📚 Full Documentation

See `AWS_LIGHTSAIL_DEPLOYMENT.md` for complete guide with:
- SSL/HTTPS setup
- Custom domain configuration
- Security hardening
- Monitoring setup
- Troubleshooting

## 🆘 Troubleshooting

**Service won't start?**
```bash
sudo supervisorctl tail -f flight-agent stderr
```

**Can't connect?**
- Check Lightsail firewall (port 8001 open?)
- Check security group
- Try: `curl http://localhost:8001/health` from instance

**Need to update code?**
```bash
cd /opt/guardian-buddy
git pull  # or upload new files via scp
sudo supervisorctl restart flight-agent
```

---

**Your API Endpoints:**
- Health: `http://YOUR_IP/health`
- Agent Card: `http://YOUR_IP/agent.json`  
- Flight Status: `http://YOUR_IP/a2a` (POST)

Good luck! 🎉


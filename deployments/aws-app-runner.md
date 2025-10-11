# AWS App Runner Deployment - Flight Agent

## 🆓 Free Tier Details
- **vCPU Seconds**: 2,000/month (Free tier)
- **GB-Hours**: 10/month (Free tier)
- **Requests**: Included in compute time
- **Duration**: Always free within limits
- **Cost**: $0/month (within free tier)

## 🚀 Quick Deploy Steps

### Step 1: Prepare Docker Image
```bash
# Build and push to ECR (or use Docker Hub)
aws ecr create-repository --repository-name flight-agent
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t flight-agent .
docker tag flight-agent:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/flight-agent:latest

# Push to ECR
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/flight-agent:latest
```

### Step 2: Create App Runner Service
1. Go to AWS Console → App Runner
2. Click "Create service"
3. Configure:
   - **Source**: Container registry
   - **Provider**: Amazon ECR
   - **Image URI**: `YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/flight-agent:latest`
   - **Deployment trigger**: Manual

### Step 3: Configure Service Settings
```yaml
# Service Configuration
Service name: flight-agent
Virtual CPU: 0.25 vCPU (Free tier)
Memory: 0.5 GB (Free tier)
Port: 8001
Environment variables:
  PROVIDER: flightaware
  FA_API_KEY: your_flightaware_api_key_here
  GROQ_API_KEY: your_groq_api_key_here
  A2A_PORT: 8001
```

### Step 4: Configure Auto Scaling
```yaml
# Auto Scaling (Free tier limits)
Min size: 1
Max size: 1
Target CPU: 70%
Target memory: 80%
```

### Step 5: Create App Runner Service
```bash
# Using AWS CLI
aws apprunner create-service \
  --service-name flight-agent \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/flight-agent:latest",
      "ImageConfiguration": {
        "Port": "8001",
        "RuntimeEnvironmentVariables": {
          "PROVIDER": "flightaware",
          "FA_API_KEY": "your_flightaware_api_key_here",
          "GROQ_API_KEY": "your_groq_api_key_here",
          "A2A_PORT": "8001"
        }
      },
      "ImageRepositoryType": "ECR"
    }
  }' \
  --instance-configuration '{
    "Cpu": "0.25 vCPU",
    "Memory": "0.5 GB"
  }' \
  --auto-scaling-configuration-arn arn:aws:apprunner:us-east-1:YOUR_ACCOUNT:autoscalingconfiguration/DefaultConfiguration/1/00000000000000000000000000000001
```

## 🧪 Test Your Deployment
```bash
# Get service URL
aws apprunner describe-service --service-arn YOUR_SERVICE_ARN

# Test health endpoint
curl https://YOUR_APP_RUNNER_URL/health

# Test flight status
curl -X POST https://YOUR_APP_RUNNER_URL/a2a \
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
- **App Runner**: $0/month (Free tier)
- **ECR Storage**: 500MB free
- **Data Transfer**: Included
- **Total**: $0/month (within limits)

## ⚠️ Free Tier Limits
- **vCPU Seconds**: 2,000/month
- **GB-Hours**: 10/month
- **Requests**: Included in compute
- **Duration**: Always free within limits

## 🔧 Management Commands
```bash
# Check service status
aws apprunner describe-service --service-arn YOUR_SERVICE_ARN

# View logs
aws logs describe-log-groups --log-group-name-prefix /aws/apprunner/flight-agent

# Update service
aws apprunner start-deployment --service-arn YOUR_SERVICE_ARN

# Pause service (saves costs)
aws apprunner pause-service --service-arn YOUR_SERVICE_ARN
```

## 🎯 Benefits
- ✅ Serverless container platform
- ✅ Auto-scaling
- ✅ HTTPS by default
- ✅ No server management
- ✅ Pay only for usage
- ✅ Always free within limits

## 📊 Usage Estimation
- **Light usage**: ~100 requests/day = Well within free tier
- **Medium usage**: ~500 requests/day = May exceed free tier
- **Heavy usage**: 1000+ requests/day = Will exceed free tier

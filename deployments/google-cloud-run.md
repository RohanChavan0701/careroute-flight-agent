# Google Cloud Run Deployment - Flight Agent

## 🆓 Free Tier Details
- **Requests**: 2 million/month (Free tier)
- **Memory**: 360,000 GB-seconds/month
- **CPU**: 180,000 vCPU-seconds/month
- **Duration**: Always free within limits
- **Cost**: $0/month (within free tier)

## 🚀 Quick Deploy Steps

### Step 1: Setup Google Cloud
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Build and Push Docker Image
```bash
# Build Docker image
docker build -t flight-agent .

# Tag for Google Container Registry
docker tag flight-agent gcr.io/YOUR_PROJECT_ID/flight-agent:latest

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/flight-agent:latest
```

### Step 3: Deploy to Cloud Run
```bash
# Deploy with environment variables
gcloud run deploy flight-agent \
  --image gcr.io/YOUR_PROJECT_ID/flight-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8001 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "PROVIDER=flightaware" \
  --set-env-vars "FA_API_KEY=your_flightaware_api_key_here" \
  --set-env-vars "GROQ_API_KEY=your_groq_api_key_here" \
  --set-env-vars "A2A_PORT=8001"
```

### Step 4: Configure Custom Domain (Optional)
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service flight-agent \
  --domain your-domain.com \
  --region us-central1
```

## 🧪 Test Your Deployment
```bash
# Get service URL
gcloud run services describe flight-agent --region us-central1 --format 'value(status.url)'

# Test health endpoint
curl https://YOUR_CLOUD_RUN_URL/health

# Test flight status
curl -X POST https://YOUR_CLOUD_RUN_URL/a2a \
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
- **Cloud Run**: $0/month (Free tier)
- **Container Registry**: 500MB free
- **Data Transfer**: Included
- **Total**: $0/month (within limits)

## ⚠️ Free Tier Limits
- **Requests**: 2M/month
- **Memory**: 360,000 GB-seconds/month
- **CPU**: 180,000 vCPU-seconds/month
- **Duration**: Always free within limits

## 🔧 Management Commands
```bash
# Check service status
gcloud run services describe flight-agent --region us-central1

# View logs
gcloud logs read --service flight-agent --limit 50

# Update service
gcloud run deploy flight-agent --image gcr.io/YOUR_PROJECT_ID/flight-agent:latest

# Scale service
gcloud run services update flight-agent --min-instances 1 --region us-central1

# Delete service
gcloud run services delete flight-agent --region us-central1
```

## 🎯 Benefits
- ✅ Serverless containers
- ✅ Auto-scaling to zero
- ✅ HTTPS by default
- ✅ Global CDN
- ✅ No server management
- ✅ Generous free tier
- ✅ Pay only for usage

## 📊 Usage Estimation
- **Light usage**: ~100 requests/day = Well within free tier
- **Medium usage**: ~1000 requests/day = Within free tier
- **Heavy usage**: 5000+ requests/day = May exceed free tier

## 🔄 CI/CD Pipeline (Optional)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Google Cloud CLI
        uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      - name: Build and Push
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/flight-agent:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/flight-agent:${{ github.sha }}
      - name: Deploy
        run: |
          gcloud run deploy flight-agent \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/flight-agent:${{ github.sha }} \
            --region us-central1
```

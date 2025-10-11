# AWS Lambda Serverless Deployment - Flight Agent

## 🆓 Free Tier Details
- **Requests**: 1 million/month (Free tier)
- **Compute**: 400,000 GB-seconds/month
- **Duration**: Always free within limits
- **Cost**: $0/month (within free tier)

## ⚠️ Important Note
This requires modifying the flight agent to work with Lambda's serverless model. The current FastAPI app needs to be adapted.

## 🚀 Quick Deploy Steps

### Step 1: Modify for Lambda
```python
# lambda_handler.py
import json
import asyncio
from flight_agent.simple_a2a_server import SimpleFlightAgent

# Initialize agent outside handler for reuse
agent = SimpleFlightAgent()

def lambda_handler(event, context):
    """Lambda handler for flight agent."""
    
    # Handle different HTTP methods
    method = event.get('httpMethod', 'POST')
    path = event.get('path', '/')
    
    if method == 'GET':
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'healthy',
                    'provider': 'flightaware',
                    'description': 'Core flight tracking agent',
                    'timestamp': '2025-10-11T18:00:00Z'
                })
            }
        elif path == '/agent.json':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(agent.agent_card)
            }
    
    elif method == 'POST' and path == '/a2a':
        # Handle JSON-RPC request
        try:
            body = json.loads(event.get('body', '{}'))
            
            # Run async handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                agent.handle_json_rpc(body)
            )
            loop.close()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': str(e)
                })
            }
    
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Not found'})
    }
```

### Step 2: Create Lambda Package
```bash
# Create deployment package
mkdir lambda-package
cd lambda-package

# Copy flight agent code
cp -r ../flight_agent .

# Install dependencies
pip install -r flight_agent/requirements.txt -t .

# Create lambda handler
cat > lambda_function.py << 'EOF'
# Paste the lambda_handler.py content here
EOF

# Create deployment zip
zip -r flight-agent-lambda.zip .
```

### Step 3: Deploy with AWS CLI
```bash
# Create Lambda function
aws lambda create-function \
  --function-name flight-agent \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://flight-agent-lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables='{
    "PROVIDER":"flightaware",
    "FA_API_KEY":"your_flightaware_api_key_here",
    "GROQ_API_KEY":"your_groq_api_key_here"
  }'
```

### Step 4: Create API Gateway
```bash
# Create REST API
aws apigateway create-rest-api \
  --name flight-agent-api \
  --description "Flight Agent API"

# Get API ID
API_ID=$(aws apigateway get-rest-apis --query 'items[?name==`flight-agent-api`].id' --output text)

# Create resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?path==`/`].id' --output text) \
  --path-part "a2a"

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?pathPart==`a2a`].id' --output text) \
  --http-method POST \
  --authorization-type NONE

# Set up Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $(aws apigateway get-resources --rest-api-id $API_ID --query 'items[?pathPart==`a2a`].id' --output text) \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:flight-agent/invocations

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

## 🧪 Test Your Deployment
```bash
# Get API Gateway URL
API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"

# Test health endpoint
curl $API_URL/health

# Test flight status
curl -X POST $API_URL/a2a \
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
- **Lambda**: $0/month (Free tier)
- **API Gateway**: $0/month (Free tier)
- **Data Transfer**: Included
- **Total**: $0/month (within limits)

## ⚠️ Free Tier Limits
- **Requests**: 1M/month
- **Compute**: 400,000 GB-seconds/month
- **Duration**: Always free within limits

## 🔧 Management Commands
```bash
# Check function status
aws lambda get-function --function-name flight-agent

# View logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/flight-agent

# Update function
aws lambda update-function-code \
  --function-name flight-agent \
  --zip-file fileb://flight-agent-lambda.zip

# Test function
aws lambda invoke \
  --function-name flight-agent \
  --payload '{"httpMethod":"GET","path":"/health"}' \
  response.json
```

## 🎯 Benefits
- ✅ True serverless
- ✅ Auto-scaling
- ✅ Pay per request
- ✅ No server management
- ✅ Built-in monitoring
- ✅ Generous free tier

## 📊 Usage Estimation
- **Light usage**: ~100 requests/day = Well within free tier
- **Medium usage**: ~1000 requests/day = Within free tier
- **Heavy usage**: 5000+ requests/day = May exceed free tier

## ⚠️ Limitations
- ❌ Cold start latency
- ❌ 15-minute execution limit
- ❌ Memory constraints
- ❌ No persistent connections
- ❌ Complex async handling

## 🔄 CI/CD Pipeline (Optional)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Lambda
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup AWS CLI
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Deploy to Lambda
        run: |
          zip -r flight-agent-lambda.zip flight_agent/ lambda_function.py
          aws lambda update-function-code \
            --function-name flight-agent \
            --zip-file fileb://flight-agent-lambda.zip
```

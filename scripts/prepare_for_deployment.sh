#!/bin/bash
# prepare_for_deployment.sh
# Prepare your local code for AWS Lightsail deployment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}║        📦 Preparing for AWS Lightsail Deployment                 ║${NC}"
echo -e "${GREEN}║                                                                   ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_DIR="/Users/rohanchavan/Desktop/Codefest"
cd "$PROJECT_DIR"

echo -e "${YELLOW}Step 1: Creating deployment package...${NC}"

# Create deployment directory
mkdir -p deploy_package
cd deploy_package

# Copy necessary files
echo "  Copying flight_agent..."
cp -r ../flight_agent .

# Remove unnecessary files
echo "  Cleaning up..."
rm -rf flight_agent/__pycache__
rm -rf flight_agent/.pytest_cache
rm -f flight_agent/.env  # Will be created on server
find flight_agent -name "*.pyc" -delete
find flight_agent -name ".DS_Store" -delete

# Create deployment README
cat > README_DEPLOY.md << 'EOF'
# Guardian Buddy Flight Agent - Deployment Package

## Quick Deploy to Lightsail

1. Upload this folder to your Lightsail instance:
   ```bash
   scp -i your-key.pem -r flight_agent ubuntu@YOUR_IP:/opt/guardian-buddy/
   ```

2. SSH into your instance:
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_IP
   ```

3. Run the deployment script:
   ```bash
   cd /opt/guardian-buddy
   chmod +x scripts/deploy_to_lightsail.sh
   ./scripts/deploy_to_lightsail.sh
   ```

## Manual Deploy

See: ../AWS_LIGHTSAIL_DEPLOYMENT.md
EOF

echo ""
echo -e "${GREEN}✅ Deployment package created!${NC}"
echo ""
echo "📦 Location: $PROJECT_DIR/deploy_package/"
echo ""

echo -e "${YELLOW}Step 2: Checking requirements...${NC}"

if [ -f flight_agent/requirements.txt ]; then
    echo "✅ requirements.txt found"
    cat flight_agent/requirements.txt
else
    echo "❌ requirements.txt not found!"
fi

echo ""
echo -e "${YELLOW}Step 3: Verifying essential files...${NC}"

REQUIRED_FILES=(
    "flight_agent/a2a_server.py"
    "flight_agent/provider.py"
    "flight_agent/mock_provider.py"
    "flight_agent/summarizer.py"
    "flight_agent/schemas.py"
    "flight_agent/config.py"
    "flight_agent/requirements.txt"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING!"
        ALL_GOOD=false
    fi
done

if [ "$ALL_GOOD" = true ]; then
    echo ""
    echo -e "${GREEN}✅ All required files present${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Some files are missing. Deployment may fail.${NC}"
    exit 1
fi

cd ..

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1️⃣  Create Lightsail Instance:"
echo "   • Go to: https://lightsail.aws.amazon.com/"
echo "   • Create Ubuntu 22.04 instance (\$10/month recommended)"
echo "   • Download SSH key"
echo "   • Open ports: 22, 80, 8001"
echo ""
echo "2️⃣  Upload deployment package:"
echo "   scp -i your-key.pem -r deploy_package/flight_agent ubuntu@YOUR_IP:/opt/guardian-buddy/"
echo ""
echo "3️⃣  Upload deployment script:"
echo "   scp -i your-key.pem scripts/deploy_to_lightsail.sh ubuntu@YOUR_IP:~/"
echo ""
echo "4️⃣  SSH and deploy:"
echo "   ssh -i your-key.pem ubuntu@YOUR_IP"
echo "   chmod +x ~/deploy_to_lightsail.sh"
echo "   ./deploy_to_lightsail.sh"
echo ""
echo "📚 Full guide: AWS_LIGHTSAIL_DEPLOYMENT.md"
echo ""
echo -e "${GREEN}🎉 Preparation complete!${NC}"


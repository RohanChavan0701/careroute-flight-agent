#!/bin/bash

# Docker build script for Guardian Buddy Flight Agent

set -e

echo "🐳 Building Guardian Buddy Flight Agent Docker Image"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the image
echo "📦 Building Docker image..."
docker build -t guardian-buddy-flight-agent:latest .

echo ""
echo "✅ Docker image built successfully!"
echo ""
echo "📋 Image details:"
docker images guardian-buddy-flight-agent:latest

echo ""
echo "🚀 To run the container:"
echo "   docker run -p 8001:8001 \\"
echo "     -e FA_API_KEY=your_key \\"
echo "     -e GROQ_API_KEY=your_key \\"
echo "     guardian-buddy-flight-agent:latest"
echo ""
echo "🐳 Or use docker-compose:"
echo "   cp env.example .env"
echo "   # Edit .env with your API keys"
echo "   docker-compose up -d"
echo ""
echo "🏥 Health check:"
echo "   curl http://localhost:8001/health"
echo ""
echo "📊 Agent card:"
echo "   curl http://localhost:8001/agent.json"

#!/bin/bash
set -e

echo "🛡️  Guardian Buddy - Starting Backend Server..."
echo ""

# Change to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo "❌ Virtual environment not found. Running setup..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Setup complete!"
    echo ""
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚙️  Creating .env file..."
    cat > backend/.env << 'EOF'
API_KEY=dev-key
ENV=development
LOG_LEVEL=INFO
PROVIDER_CACHE_TTL_SECONDS=60
PROVIDER_RATE_LIMIT_PER_KEY_PER_MINUTE=10
CORS_ALLOW_ORIGINS=*
EOF
    echo "✅ .env created with default values"
    echo ""
fi

# Activate virtual environment
source backend/.venv/bin/activate

# Start server
echo "🚀 Starting server on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo "🔑 API Key: dev-key"
echo ""
echo "Press Ctrl+C to stop..."
echo ""

PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH uvicorn backend.main:app --reload --port 8000


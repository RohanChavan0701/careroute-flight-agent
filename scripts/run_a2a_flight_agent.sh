#!/bin/bash
# Run flight-agent with A2A Protocol (JSON-RPC 2.0 over HTTP)

set -e

cd "$(dirname "$0")/.."

echo "🔧 Setting up A2A flight-agent..."

# Create venv if needed
if [ ! -d "flight_agent/.venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv flight_agent/.venv
fi

# Activate venv
source flight_agent/.venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r flight_agent/requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📡 Starting A2A Flight Agent..."
echo "   Protocol: A2A (Agent2Agent) JSON-RPC 2.0"
echo "   Port: ${A2A_PORT:-8001}"
echo "   Provider: ${PROVIDER:-flightaware}"
echo "   Agent Card: http://localhost:${A2A_PORT:-8001}/agent.json"
echo "   JSON-RPC: http://localhost:${A2A_PORT:-8001}/a2a"
echo ""

# Run the A2A server
python -m flight_agent.a2a_server


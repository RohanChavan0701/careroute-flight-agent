#!/bin/bash
# Run flight-agent microservice

set -e

cd "$(dirname "$0")/.."

echo "🔧 Setting up flight-agent..."

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
echo "📡 Starting flight-agent..."
echo "   NATS subject: guardian.flight.get_status.v1"
echo "   Provider: ${PROVIDER:-flightaware}"
echo ""

# Run the agent
python -m flight_agent


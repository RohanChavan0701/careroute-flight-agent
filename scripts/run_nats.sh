#!/bin/bash
# Start NATS server with JetStream

echo "🚀 Starting NATS server..."
echo "   Ports: 4222 (client), 8222 (monitoring)"
echo ""

docker run --rm -p 4222:4222 -p 8222:8222 nats:latest -js -m 8222


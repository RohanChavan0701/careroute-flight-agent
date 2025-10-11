#!/bin/bash
set -e

echo "🧪 Guardian Buddy - Provider Test Suite"
echo "========================================="
echo ""

API_KEY="dev-key"
BASE="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Mock Provider${NC}"
echo "----------------------"

# Test health
echo -n "1. Health check... "
HEALTH=$(curl -s $BASE/healthz | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
if [ "$HEALTH" = "ok" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test track flight
echo -n "2. Track flight DL789 (should be LANDED)... "
RESPONSE=$(curl -s -X POST $BASE/v1/flights/track \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"airline_code":"DL","flight_number":"789","departure_date":"2025-10-11"}')

STATUS=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
PROVIDER=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['last_provider'])")

if [ "$STATUS" = "LANDED" ] && [ "$PROVIDER" = "MockProvider" ]; then
    echo -e "${GREEN}✓${NC} (status=$STATUS, provider=$PROVIDER)"
else
    echo -e "${RED}✗${NC} (status=$STATUS, provider=$PROVIDER)"
    exit 1
fi

# Test get flight
echo -n "3. Get flight DL-789-2025-10-11... "
GET_RESPONSE=$(curl -s $BASE/v1/flights/DL-789-2025-10-11 -H "x-api-key: $API_KEY")
GET_STATUS=$(echo $GET_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

if [ "$GET_STATUS" = "LANDED" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test events
echo -n "4. Get flight events... "
EVENTS=$(curl -s $BASE/v1/flights/DL-789-2025-10-11/events -H "x-api-key: $API_KEY")
EVENT_COUNT=$(echo $EVENTS | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

if [ "$EVENT_COUNT" -ge "1" ]; then
    echo -e "${GREEN}✓${NC} ($EVENT_COUNT events)"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test LLM tool endpoint
echo -n "5. LLM tool endpoint... "
TOOL_RESPONSE=$(curl -s -X POST $BASE/v1/tools/get_flight_status \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"flight_id":"DL-789-2025-10-11"}')

TOOL_TEXT=$(echo $TOOL_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['status_text'])")

if [[ "$TOOL_TEXT" == *"landed"* ]] || [[ "$TOOL_TEXT" == *"LANDED"* ]]; then
    echo -e "${GREEN}✓${NC}"
    echo "   Status text: $TOOL_TEXT"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test different flight statuses
echo ""
echo "6. Testing deterministic statuses:"
for flight in "100:SCHEDULED" "456:BOARDING" "202:ACTIVE" "303:DELAYED" "789:LANDED"; do
    IFS=':' read -r num expected <<< "$flight"
    RESP=$(curl -s -X POST $BASE/v1/flights/track \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -d "{\"airline_code\":\"TEST\",\"flight_number\":\"$num\",\"departure_date\":\"2025-10-11\"}")
    
    ACTUAL=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    
    if [ "$ACTUAL" = "$expected" ]; then
        echo -e "   TEST$num → $expected ${GREEN}✓${NC}"
    else
        echo -e "   TEST$num → expected $expected, got $ACTUAL ${RED}✗${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Provider Info:"
echo "  Type: MockProvider"
echo "  Cache: 60s per flight"
echo "  Rate Limit: 10 req/min per flight"
echo ""
echo "To test AeroDataBox provider:"
echo "  export FLIGHT_PROVIDER=aerodatabox"
echo "  export AEROBOX_KEY=your_rapidapi_key"
echo "  ./start_server.sh"
echo "  ./test_providers.sh"


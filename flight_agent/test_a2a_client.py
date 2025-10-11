"""Test client for A2A Protocol flight-agent."""

import json
import sys
from uuid import uuid4

import httpx


def test_get_agent_card(base_url: str):
    """Test Agent Card retrieval."""
    print("📋 Testing Agent Card (GET /agent.json)...")
    
    response = httpx.get(f"{base_url}/agent.json")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        card = response.json()
        print("\nAgent Card:")
        print(json.dumps(card, indent=2))
        return card
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_get_flight_status(base_url: str, flight_num: str, date: str, locale: str = "en-US"):
    """Test get_flight_status skill via JSON-RPC 2.0."""
    print(f"\n✈️  Testing get_flight_status (POST /a2a)...")
    print(f"Flight: {flight_num}, Date: {date}, Locale: {locale}")
    
    # Build JSON-RPC 2.0 request
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "get_flight_status",
        "params": {
            "flight_num": flight_num,
            "departure_date": date,
            "locale": locale
        },
        "id": str(uuid4())
    }
    
    print("\n📤 Request:")
    print(json.dumps(rpc_request, indent=2))
    
    response = httpx.post(
        f"{base_url}/a2a",
        json=rpc_request,
        timeout=30.0
    )
    
    print(f"\n📥 Response (Status {response.status_code}):")
    
    try:
        result = response.json()
        print(json.dumps(result, indent=2))
        
        # Check for error
        if "error" in result and result["error"]:
            print(f"\n❌ JSON-RPC Error:")
            print(f"   Code: {result['error']['code']}")
            print(f"   Message: {result['error']['message']}")
            if "data" in result["error"]:
                print(f"   Data: {result['error']['data']}")
            return None
        
        # Extract result
        if "result" in result and result["result"]:
            data = result["result"]
            
            print(f"\n✅ Success!")
            print(f"\n📊 Flight Data:")
            print(f"   Airline: {data['raw']['airline']}")
            print(f"   Flight: {data['raw']['flight_number']}")
            print(f"   Route: {data['raw']['origin_iata']} → {data['raw']['destination_iata']}")
            print(f"   Status: {data['raw']['status']}")
            if data['raw'].get('delay_minutes'):
                print(f"   Delay: {data['raw']['delay_minutes']} minutes")
            if data['raw'].get('gate'):
                print(f"   Gate: {data['raw']['gate']}")
            
            print(f"\n💬 AI Summary:")
            print(f"   Text: {data['script']['text']}")
            print(f"\n🔊 SSML:")
            print(f"   {data['script']['ssml']}")
            
            print(f"\n🔑 Metadata:")
            print(f"   Hash: {data['hash']}")
            print(f"   Generated: {data['generated_at']}")
            print(f"   Schema: {data['schema_version']}")
            
            return data
        
        return None
        
    except Exception as e:
        print(f"❌ Error parsing response: {e}")
        print(response.text)
        return None


def test_invalid_method(base_url: str):
    """Test invalid method handling."""
    print(f"\n🧪 Testing invalid method...")
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "invalid_method",
        "params": {},
        "id": str(uuid4())
    }
    
    response = httpx.post(f"{base_url}/a2a", json=rpc_request)
    result = response.json()
    
    if result.get("error") and result["error"]["code"] == -32601:
        print("✅ Correctly returned METHOD_NOT_FOUND error")
        print(f"   Message: {result['error']['message']}")
    else:
        print("❌ Unexpected response for invalid method")


def test_invalid_params(base_url: str):
    """Test invalid params handling."""
    print(f"\n🧪 Testing invalid params...")
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "get_flight_status",
        "params": {
            "flight_num": "AA100"
            # Missing required 'departure_date'
        },
        "id": str(uuid4())
    }
    
    response = httpx.post(f"{base_url}/a2a", json=rpc_request)
    result = response.json()
    
    if result.get("error") and result["error"]["code"] == -32602:
        print("✅ Correctly returned INVALID_PARAMS error")
        print(f"   Message: {result['error']['message']}")
    else:
        print("❌ Unexpected response for invalid params")


if __name__ == "__main__":
    base_url = "http://localhost:8001"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║        A2A PROTOCOL - FLIGHT AGENT TEST CLIENT                    ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"\nBase URL: {base_url}")
    print("=" * 60)
    
    # Test 1: Agent Card
    test_get_agent_card(base_url)
    
    # Test 2: Get Flight Status (use command line args or defaults)
    flight_num = sys.argv[2] if len(sys.argv) > 2 else "AA100"
    date = sys.argv[3] if len(sys.argv) > 3 else "2025-10-12"
    locale = sys.argv[4] if len(sys.argv) > 4 else "en-US"
    
    test_get_flight_status(base_url, flight_num, date, locale)
    
    # Test 3: Error handling
    test_invalid_method(base_url)
    test_invalid_params(base_url)
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")


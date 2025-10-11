"""Quick test client for flight-agent NATS service."""

import asyncio
import json
import sys

import nats


async def test_flight_status(flight_num: str, date: str, locale: str = "en-US"):
    """Send a test request to flight-agent."""
    
    print(f"Connecting to NATS...")
    nc = await nats.connect("nats://localhost:4222")
    print(f"Connected!")
    
    request = {
        "flight_num": flight_num,
        "departure_date": date,
        "locale": locale,
        "user_id": "test_user"
    }
    
    print(f"\nSending request:")
    print(json.dumps(request, indent=2))
    
    print(f"\nWaiting for response (15s timeout)...")
    
    try:
        response = await nc.request(
            "guardian.flight.get_status.v1",
            json.dumps(request).encode(),
            timeout=15
        )
        
        result = json.loads(response.data.decode())
        
        print(f"\n{'='*60}")
        print(f"RESPONSE:")
        print(f"{'='*60}")
        print(json.dumps(result, indent=2))
        
        if result.get("ok"):
            data = result["data"]
            print(f"\n{'='*60}")
            print(f"SUMMARY:")
            print(f"{'='*60}")
            print(f"Text: {data['script']['text']}")
            print(f"SSML: {data['script']['ssml']}")
            print(f"Status: {data['raw']['status']}")
            print(f"Hash: {data['hash']}")
        else:
            print(f"\n❌ Error: {result.get('error')}")
            
    except asyncio.TimeoutError:
        print(f"\n❌ Request timed out after 15 seconds")
        print(f"   Is flight-agent running?")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await nc.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_client.py <flight_num> <date> [locale]")
        print("Example: python test_client.py AA100 2025-10-12 en-US")
        sys.exit(1)
    
    flight_num = sys.argv[1]
    date = sys.argv[2]
    locale = sys.argv[3] if len(sys.argv) > 3 else "en-US"
    
    asyncio.run(test_flight_status(flight_num, date, locale))


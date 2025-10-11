#!/usr/bin/env python3
"""Quick test script to verify FlightAware API key works."""

import httpx
from datetime import datetime, timedelta

# Your API key
FA_API_KEY = "codefest2025"
FA_BASE = "https://aeroapi.flightaware.com/aeroapi"

def test_flightaware_api():
    """Test FlightAware AeroAPI with a real flight."""
    
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║        🧪 TESTING FLIGHTAWARE AEROAPI CONNECTION                 ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"API Key: {FA_API_KEY}")
    print(f"Base URL: {FA_BASE}")
    print()
    
    # Test with a common flight (American Airlines 100)
    flight_num = "AA100"
    
    # Use today's date
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"Testing flight: {flight_num}")
    print(f"Date range: {start_date} to {end_date}")
    print()
    print("Making API request...")
    print("─" * 70)
    
    url = f"{FA_BASE}/flights/{flight_num}"
    params = {
        "ident_type": "designator",
        "start": start_date,
        "end": end_date,
        "max_pages": 1
    }
    headers = {
        "x-apikey": FA_API_KEY  # Note: lowercase 'x-apikey' as per AeroAPI v4
    }
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            flights = data.get("flights", [])
            
            print(f"✅ SUCCESS! Found {len(flights)} flight(s)")
            print()
            
            if flights:
                flight = flights[0]
                print("📊 Flight Details:")
                print(f"   Ident: {flight.get('ident', 'N/A')}")
                print(f"   Operator: {flight.get('operator', 'N/A')}")
                
                origin = flight.get('origin', {})
                destination = flight.get('destination', {})
                
                print(f"   Route: {origin.get('code_iata', 'N/A')} → {destination.get('code_iata', 'N/A')}")
                print(f"   Origin: {origin.get('city', 'N/A')}")
                print(f"   Destination: {destination.get('city', 'N/A')}")
                
                if flight.get('scheduled_out'):
                    print(f"   Scheduled Out: {flight.get('scheduled_out')}")
                if flight.get('estimated_out'):
                    print(f"   Estimated Out: {flight.get('estimated_out')}")
                    
                print()
                print("🎉 Your FlightAware API key is working!")
                print()
                print("You can now use:")
                print("   • Backend REST API (port 8000)")
                print("   • Flight-Agent A2A (port 8001)")
                return True
            else:
                print("ℹ️  No flights found for today.")
                print("   This is normal if the flight doesn't operate today.")
                print("   Try a different date or flight number.")
                return True
                
        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED")
            print()
            print("Error: Invalid API key")
            print()
            print("Please check:")
            print("   1. Your API key is correct: codefesthokies")
            print("   2. Your FlightAware account is active")
            print("   3. You have sufficient API credits")
            return False
            
        elif response.status_code == 429:
            print("⚠️  RATE LIMIT EXCEEDED")
            print()
            print("You've hit the rate limit. Please wait a moment.")
            return False
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print()
            print("Response:")
            print(response.text[:500])
            return False
            
    except httpx.TimeoutException:
        print("❌ TIMEOUT")
        print()
        print("The request timed out. Please check your internet connection.")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("An unexpected error occurred.")
        return False


if __name__ == "__main__":
    success = test_flightaware_api()
    print()
    print("─" * 70)
    if success:
        print()
        print("✅ Setup complete! Your FlightAware integration is ready.")
        print()
        print("Next steps:")
        print("   1. Start A2A agent: ./scripts/run_a2a_flight_agent.sh")
        print("   2. Test with: cd flight_agent && python test_a2a_client.py")
    else:
        print()
        print("❌ Please fix the issues above and try again.")
    print()


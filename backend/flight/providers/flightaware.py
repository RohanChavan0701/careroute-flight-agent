"""FlightAware AeroAPI v4 provider.

Docs: https://www.flightaware.com/commercial/aeroapi/
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import httpx

from ..models import FlightStatus
from .base import FlightProvider, ProviderResponse
from ...common.logging_config import get_logger

logger = get_logger(__name__)

# Configuration from environment
FA_API_KEY = os.getenv("FA_API_KEY", "")
FA_BASE = os.getenv("FA_BASE", "https://aeroapi.flightaware.com/aeroapi")
FA_TIMEOUT_SEC = float(os.getenv("FA_TIMEOUT_SEC", "6"))


class FlightAwareProvider(FlightProvider):
    """Provider using FlightAware AeroAPI v4.
    
    Implements GET /flights/{ident} with date bounds and designator type.
    Requires API key from: https://www.flightaware.com/commercial/aeroapi/
    """
    
    def __init__(self):
        if not FA_API_KEY:
            raise RuntimeError("FA_API_KEY environment variable is required")
        
        self.base_url = FA_BASE
        self.headers = {
            "x-apikey": FA_API_KEY,
        }
        self.timeout = FA_TIMEOUT_SEC

    def fetch_status(
        self, 
        airline_code: str, 
        flight_number: str, 
        departure_date: str
    ) -> ProviderResponse:
        """Fetch flight status from FlightAware AeroAPI v4.
        
        Args:
            airline_code: IATA airline code (e.g., "AA")
            flight_number: Flight number without airline code
            departure_date: ISO date string YYYY-MM-DD
            
        Returns:
            ProviderResponse with normalized flight data
        """
        # FlightAware uses flight designator (e.g., "AA100")
        flight_ident = f"{airline_code}{flight_number}"
        
        # Parse date and create bounds (start=date, end=date+1)
        try:
            date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
            start_date = date_obj.strftime("%Y-%m-%d")
            end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError as e:
            raise RuntimeError(f"Invalid date format: {departure_date}. Expected YYYY-MM-DD")
        
        url = f"{self.base_url}/flights/{flight_ident}"
        
        # Query params per spec
        params = {
            "ident_type": "designator",
            "start": start_date,
            "end": end_date,
            "max_pages": 1
        }
        
        logger.info(f"Fetching from FlightAware: {flight_ident} on {departure_date}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.error(f"FlightAware timeout for {flight_ident}")
            raise RuntimeError(f"Provider timeout for {flight_ident}")
        except httpx.HTTPStatusError as e:
            logger.error(f"FlightAware HTTP {e.response.status_code} for {flight_ident}")
            raise RuntimeError(f"Provider returned {e.response.status_code}")
        except Exception as e:
            logger.error(f"FlightAware error: {e}")
            raise RuntimeError(f"Provider error: {str(e)}")

        # Extract flights array
        flights = data.get("flights", [])
        if not flights:
            raise RuntimeError(f"No flights found for {flight_ident} on {departure_date}")

        # Use first flight matching our date
        flight_data = flights[0]
        return self._map_to_response(airline_code, flight_number, flight_data)

    def _map_to_response(
        self, 
        airline_code: str, 
        flight_number: str, 
        data: Dict[str, Any]
    ) -> ProviderResponse:
        """Map FlightAware AeroAPI v4 response to ProviderResponse.
        
        Maps per specification:
        - airline -> operator/operator_iata
        - origin/destination -> code_iata, city|name, timezone
        - times -> scheduled_out|off, estimated_out|off, scheduled_in|on, estimated_in|on
        - gate/terminal -> gate_origin/destination, terminal_origin/destination
        - delays -> departure_delay, arrival_delay
        """
        
        # Extract operator (airline)
        operator = data.get("operator") or data.get("operator_iata") or airline_code
        ident = data.get("ident", "")
        
        # Extract origin
        origin = data.get("origin", {}) or {}
        origin_iata = origin.get("code_iata") or origin.get("code")
        origin_city = origin.get("city") or origin.get("name") or ""
        origin_tz = origin.get("timezone", "")
        
        # Extract destination
        destination = data.get("destination", {}) or {}
        dest_iata = destination.get("code_iata") or destination.get("code")
        dest_city = destination.get("city") or destination.get("name") or ""
        dest_tz = destination.get("timezone", "")
        
        # Extract times (local YYYY-MM-DDTHH:MM format)
        # Scheduled departure: scheduled_out or scheduled_off
        sched_dep = self._parse_local_time(data.get("scheduled_out") or data.get("scheduled_off"))
        # Estimated departure: estimated_out or estimated_off
        est_dep = self._parse_local_time(data.get("estimated_out") or data.get("estimated_off"))
        
        # Scheduled arrival: scheduled_in or scheduled_on
        sched_arr = self._parse_local_time(data.get("scheduled_in") or data.get("scheduled_on"))
        # Estimated arrival: estimated_in or estimated_on
        est_arr = self._parse_local_time(data.get("estimated_in") or data.get("estimated_on"))
        
        # Gate and terminal
        gate_dep = data.get("gate_origin")
        gate_arr = data.get("gate_destination")
        terminal_dep = data.get("terminal_origin")
        terminal_arr = data.get("terminal_destination")
        
        # Status mapping
        status = self._map_status(data.get("status"))
        
        # Delay information (in minutes)
        delay_min = data.get("departure_delay") or data.get("arrival_delay")
        status_reason = None
        if delay_min and delay_min > 0:
            status_reason = f"Delayed {delay_min} minutes"
        
        return ProviderResponse(
            airline_code=operator,
            flight_number=ident or flight_number,
            departure_airport=origin_iata,
            arrival_airport=dest_iata,
            scheduled_offblock=sched_dep,
            estimated_offblock=est_dep or sched_dep,
            scheduled_arrival=sched_arr,
            estimated_arrival=est_arr or sched_arr,
            gate_dep=gate_dep,
            gate_arr=gate_arr,
            terminal_dep=terminal_dep,
            terminal_arr=terminal_arr,
            status=status,
            status_reason=status_reason,
        )

    def _parse_local_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse local time string to datetime object.
        
        Expected format: YYYY-MM-DDTHH:MM or ISO 8601 with timezone
        """
        if not time_str:
            return None
        try:
            # Remove timezone suffix if present for local time
            if time_str.endswith('Z'):
                time_str = time_str[:-1] + '+00:00'
            
            # Try ISO 8601 parse
            return datetime.fromisoformat(time_str)
        except Exception as e:
            logger.warning(f"Failed to parse time '{time_str}': {e}")
            return None

    def _map_status(self, status_str: Optional[str]) -> FlightStatus:
        """Map FlightAware status to our FlightStatus enum.
        
        Maps: ON_TIME, DELAYED, BOARDING, IN_AIR, LANDED, CANCELLED, UNKNOWN
        """
        if not status_str:
            return FlightStatus.SCHEDULED
        
        status_upper = status_str.upper()
        
        status_map = {
            "ON_TIME": FlightStatus.SCHEDULED,
            "SCHEDULED": FlightStatus.SCHEDULED,
            "DELAYED": FlightStatus.DELAYED,
            "BOARDING": FlightStatus.BOARDING,
            "IN_AIR": FlightStatus.ACTIVE,
            "ACTIVE": FlightStatus.ACTIVE,
            "EN_ROUTE": FlightStatus.ACTIVE,
            "LANDED": FlightStatus.LANDED,
            "ARRIVED": FlightStatus.LANDED,
            "CANCELLED": FlightStatus.CANCELLED,
            "CANCELED": FlightStatus.CANCELLED,
            "DIVERTED": FlightStatus.DIVERTED,
            "UNKNOWN": FlightStatus.SCHEDULED,
        }
        
        return status_map.get(status_upper, FlightStatus.SCHEDULED)


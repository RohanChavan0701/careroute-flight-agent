"""AeroDataBox provider via RapidAPI.

Docs: https://rapidapi.com/aedbx-aedbx/api/aerodatabox
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from ..models import FlightStatus
from .base import FlightProvider, ProviderResponse
from ...common.logging_config import get_logger

logger = get_logger(__name__)

# Configuration from environment
AEROBOX_BASE = os.getenv("AEROBOX_BASE", "https://aerodatabox.p.rapidapi.com")
AEROBOX_KEY = os.getenv("AEROBOX_KEY", "")
AEROBOX_HOST = os.getenv("AEROBOX_HOST", "aerodatabox.p.rapidapi.com")
AEROBOX_TIMEOUT = float(os.getenv("AEROBOX_TIMEOUT_SEC", "6"))


class AeroDataBoxProvider(FlightProvider):
    """Provider using AeroDataBox API via RapidAPI."""
    
    def __init__(self):
        if not AEROBOX_KEY:
            raise RuntimeError("AEROBOX_KEY environment variable is required for AeroDataBox provider")
        
        self.base_url = AEROBOX_BASE
        self.headers = {
            "x-rapidapi-key": AEROBOX_KEY,
            "x-rapidapi-host": AEROBOX_HOST,
        }
        self.timeout = AEROBOX_TIMEOUT

    def fetch_status(
        self, 
        airline_code: str, 
        flight_number: str, 
        departure_date: str
    ) -> ProviderResponse:
        """Fetch flight status from AeroDataBox API.
        
        Uses the /flights/number/{flightNumber}/{date} endpoint.
        """
        flight_designator = f"{airline_code}{flight_number}"
        url = f"{self.base_url}/flights/number/{flight_designator}/{departure_date}"
        
        logger.info(f"Fetching from AeroDataBox: {flight_designator} on {departure_date}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            logger.error(f"AeroDataBox timeout: {e}")
            raise Exception(f"Provider timeout for {flight_designator}")
        except httpx.HTTPStatusError as e:
            logger.error(f"AeroDataBox HTTP error: {e.response.status_code}")
            raise Exception(f"Provider returned {e.response.status_code}")
        except Exception as e:
            logger.error(f"AeroDataBox error: {e}")
            raise Exception(f"Provider error: {str(e)}")

        # Parse response
        flights = self._extract_flights(data)
        if not flights:
            raise Exception(f"No flights found for {flight_designator} on {departure_date}")

        # Use first matching flight
        flight_data = flights[0]
        return self._map_to_response(airline_code, flight_number, flight_data)

    def _extract_flights(self, data: Any) -> list:
        """Extract flight list from API response."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Try different possible keys
            return (
                data.get("departures", []) or 
                data.get("arrivals", []) or 
                data.get("flights", []) or
                []
            )
        return []

    def _map_to_response(
        self, 
        airline_code: str, 
        flight_number: str, 
        data: Dict[str, Any]
    ) -> ProviderResponse:
        """Map AeroDataBox response to normalized ProviderResponse."""
        dep = data.get("departure", {}) or {}
        arr = data.get("arrival", {}) or {}

        # Extract airport codes
        dep_airport = self._extract_airport(dep)
        arr_airport = self._extract_airport(arr)

        # Extract times
        sched_dep = self._parse_time(dep.get("scheduledTimeLocal") or dep.get("scheduledTime"))
        est_dep = self._parse_time(dep.get("estimatedTimeLocal") or dep.get("estimatedTime"))
        sched_arr = self._parse_time(arr.get("scheduledTimeLocal") or arr.get("scheduledTime"))
        est_arr = self._parse_time(arr.get("estimatedTimeLocal") or arr.get("estimatedTime"))

        # Extract gate/terminal
        gate_dep = dep.get("gate")
        gate_arr = arr.get("gate")
        terminal_dep = dep.get("terminal")
        terminal_arr = arr.get("terminal")

        # Map status
        status_str = (data.get("status") or "").upper()
        status = self._map_status(status_str)

        # Status reason (delay info)
        status_reason = None
        delay = dep.get("delay") or data.get("delays")
        if delay:
            if isinstance(delay, dict):
                delay_min = delay.get("departure") or delay.get("arrival")
                if delay_min:
                    status_reason = f"Delayed {delay_min} minutes"
            elif isinstance(delay, (int, float)):
                status_reason = f"Delayed {delay} minutes"

        return ProviderResponse(
            airline_code=airline_code,
            flight_number=flight_number,
            departure_airport=dep_airport,
            arrival_airport=arr_airport,
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

    def _extract_airport(self, location: Dict[str, Any]) -> Optional[str]:
        """Extract airport IATA code from location object."""
        airport = location.get("airport", {}) or {}
        return airport.get("iata") or airport.get("icao")

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object."""
        if not time_str:
            return None
        try:
            # Handle various formats
            time_str = time_str.replace(" ", "T")
            if "T" in time_str and len(time_str) >= 16:
                return datetime.fromisoformat(time_str[:19])
            return None
        except Exception as e:
            logger.warning(f"Failed to parse time '{time_str}': {e}")
            return None

    def _map_status(self, status_str: str) -> FlightStatus:
        """Map AeroDataBox status to our FlightStatus enum."""
        status_map = {
            "SCHEDULED": FlightStatus.SCHEDULED,
            "BOARDING": FlightStatus.BOARDING,
            "DEPARTED": FlightStatus.ACTIVE,
            "EN_ROUTE": FlightStatus.ACTIVE,
            "ACTIVE": FlightStatus.ACTIVE,
            "DELAYED": FlightStatus.DELAYED,
            "LANDED": FlightStatus.LANDED,
            "ARRIVED": FlightStatus.LANDED,
            "CANCELLED": FlightStatus.CANCELLED,
            "CANCELED": FlightStatus.CANCELLED,
            "DIVERTED": FlightStatus.DIVERTED,
        }
        return status_map.get(status_str, FlightStatus.SCHEDULED)


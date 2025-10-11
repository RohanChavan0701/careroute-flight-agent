"""FlightAware provider with retry logic."""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict

import httpx

from .config import config
from .schemas import FlightRaw


class ProviderError(Exception):
    """Provider-related errors."""
    pass


class FlightAwareProvider:
    """FlightAware AeroAPI v4 provider with exponential backoff retry."""
    
    def __init__(self):
        if not config.FA_API_KEY:
            raise ValueError("FA_API_KEY is required")
        
        self.base_url = config.FA_BASE
        self.headers = {"x-apikey": config.FA_API_KEY}
        self.timeout = config.FA_TIMEOUT_SEC
    
    async def fetch_status(self, flight_num: str, departure_date: str) -> FlightRaw:
        """Fetch flight status with retry logic.
        
        Args:
            flight_num: Flight designator (e.g., "AA100")
            departure_date: ISO date YYYY-MM-DD
            
        Returns:
            FlightRaw normalized data
            
        Raises:
            ProviderError: On failure after retries
        """
        # Parse date and create bounds
        try:
            date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
            start_date = date_obj.strftime("%Y-%m-%d")
            end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError as e:
            raise ProviderError(f"Invalid date format: {departure_date}")
        
        url = f"{self.base_url}/flights/{flight_num}"
        params = {
            "ident_type": "designator",
            "start": start_date,
            "end": end_date,
            "max_pages": 1
        }
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    data = response.json()
                
                flights = data.get("flights", [])
                if not flights:
                    raise ProviderError(f"No flights found for {flight_num} on {departure_date}")
                
                return self._map_to_flight_raw(flights[0])
                
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                # Retry on timeout or 5xx errors
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code < 500:
                    # Don't retry 4xx errors
                    raise ProviderError(f"Provider returned {e.response.status_code}")
                
                # Exponential backoff
                if attempt < config.RETRY_ATTEMPTS - 1:
                    backoff_ms = config.RETRY_BACKOFF_MS[attempt]
                    await asyncio.sleep(backoff_ms / 1000)
            except Exception as e:
                raise ProviderError(f"Provider error: {str(e)}")
        
        # All retries failed
        raise ProviderError(f"Provider timeout/error after {config.RETRY_ATTEMPTS} attempts")
    
    def _map_to_flight_raw(self, data: Dict[str, Any]) -> FlightRaw:
        """Map FlightAware response to FlightRaw schema."""
        
        # Extract fields
        operator = data.get("operator") or data.get("operator_iata") or ""
        ident = data.get("ident", "")
        
        origin = data.get("origin", {}) or {}
        destination = data.get("destination", {}) or {}
        
        origin_iata = origin.get("code_iata") or origin.get("code") or ""
        origin_city = origin.get("city") or origin.get("name") or ""
        origin_tz = origin.get("timezone", "")
        
        dest_iata = destination.get("code_iata") or destination.get("code") or ""
        dest_city = destination.get("city") or destination.get("name") or ""
        dest_tz = destination.get("timezone", "")
        
        # Times (prefer out/in over off/on for user-facing times)
        sched_dep = self._parse_time(data.get("scheduled_out") or data.get("scheduled_off"), origin_tz)
        est_dep = self._parse_time(data.get("estimated_out") or data.get("estimated_off"), origin_tz)
        sched_arr = self._parse_time(data.get("scheduled_in") or data.get("scheduled_on"), dest_tz)
        est_arr = self._parse_time(data.get("estimated_in") or data.get("estimated_on"), dest_tz)
        
        # Gate and terminal
        gate = data.get("gate_origin") or data.get("gate_destination")
        terminal = data.get("terminal_origin") or data.get("terminal_destination")
        
        # Status and delay
        status = self._map_status(data.get("status", ""))
        delay_min = data.get("departure_delay") or data.get("arrival_delay")
        
        return FlightRaw(
            airline=operator,
            flight_number=ident,
            origin_iata=origin_iata,
            origin_city=origin_city,
            origin_tz=origin_tz,
            destination_iata=dest_iata,
            destination_city=dest_city,
            destination_tz=dest_tz,
            scheduled_departure_local=sched_dep,
            estimated_departure_local=est_dep,
            scheduled_arrival_local=sched_arr,
            estimated_arrival_local=est_arr,
            gate=gate,
            terminal=terminal,
            status=status,
            delay_minutes=delay_min
        )
    
    def _parse_time(self, time_str: str | None, airport_tz: str | None = None) -> str | None:
        """Parse ISO time to YYYY-MM-DDTHH:MM format in local timezone."""
        if not time_str:
            return None
        try:
            # FlightAware returns UTC times, convert to local airport timezone
            if time_str.endswith('Z'):
                time_str = time_str[:-1] + '+00:00'
            
            dt_utc = datetime.fromisoformat(time_str)
            
            # Convert to local timezone if provided
            if airport_tz:
                try:
                    import pytz
                    local_tz = pytz.timezone(airport_tz)
                    dt_local = dt_utc.astimezone(local_tz)
                    return dt_local.strftime("%Y-%m-%dT%H:%M")
                except ImportError:
                    # Fallback: assume EDT (UTC-4) for US airports
                    if 'America' in airport_tz:
                        dt_local = dt_utc.replace(tzinfo=None) - timedelta(hours=4)
                        return dt_local.strftime("%Y-%m-%dT%H:%M")
            
            # Default: return UTC time
            return dt_utc.strftime("%Y-%m-%dT%H:%M")
        except Exception:
            return None
    
    def _map_status(self, status_str: str) -> str:
        """Map FlightAware status to our standard statuses."""
        if not status_str:
            return "UNKNOWN"
            
        # Normalize status string - remove spaces, slashes, and convert to uppercase
        normalized = status_str.upper().replace(" ", "").replace("/", "").replace("-", "")
        
        # Check for specific patterns
        if "ENROUTE" in normalized or "INROUTE" in normalized:
            return "IN_AIR"
        elif "ONROUTE" in normalized:
            return "IN_AIR"
        elif "DELAYED" in normalized:
            return "DELAYED"
        elif "ONTIME" in normalized:
            return "ON_TIME"
        elif "SCHEDULED" in normalized:
            return "ON_TIME"
        elif "BOARDING" in normalized:
            return "BOARDING"
        elif "LANDED" in normalized or "ARRIVED" in normalized:
            return "LANDED"
        elif "CANCELLED" in normalized or "CANCELED" in normalized:
            return "CANCELLED"
        elif "DIVERTED" in normalized:
            return "DIVERTED"
        elif "ACTIVE" in normalized:
            return "IN_AIR"
        else:
            return "UNKNOWN"


def compute_hash(raw: FlightRaw) -> str:
    """Compute deterministic hash of FlightRaw for caching."""
    # Serialize to JSON with sorted keys
    json_str = raw.model_dump_json(exclude_none=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


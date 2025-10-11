"""Mock flight provider for testing and demos."""

import time
from datetime import datetime, timezone
from typing import Dict, Tuple

from ..models import FlightStatus
from .base import FlightProvider, ProviderResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._tokens: Dict[str, Tuple[int, float]] = {}

    def allow(self, key: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        tokens, ts = self._tokens.get(key, (self.max_per_minute, now))
        
        # Refill tokens each minute
        if now - ts >= 60:
            tokens = self.max_per_minute
            ts = now
            
        if tokens <= 0:
            self._tokens[key] = (tokens, ts)
            return False
            
        tokens -= 1
        self._tokens[key] = (tokens, ts)
        return True


class MockProvider(FlightProvider):
    """Mock provider returning deterministic statuses based on flight number.
    
    Uses flight number modulo 5 to determine status:
    - 0: SCHEDULED
    - 1: BOARDING
    - 2: ACTIVE
    - 3: DELAYED
    - 4: LANDED
    
    Includes 60s caching and simple rate limiting.
    """
    
    def __init__(self, cache_ttl: int = 60, rate_limit: int = 10):
        self._cache: Dict[str, Tuple[ProviderResponse, float]] = {}
        self._limiter = RateLimiter(rate_limit)
        self._cache_ttl = cache_ttl

    def _cache_key(self, airline_code: str, flight_number: str, departure_date: str) -> str:
        return f"{airline_code}:{flight_number}:{departure_date}"

    def fetch_status(
        self, 
        airline_code: str, 
        flight_number: str, 
        departure_date: str
    ) -> ProviderResponse:
        """Fetch mock flight status with deterministic behavior."""
        cache_key = self._cache_key(airline_code, flight_number, departure_date)

        # Check cache first
        if cache_key in self._cache:
            cached_resp, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_resp

        # Rate limit check
        if not self._limiter.allow(cache_key):
            # Try to serve from stale cache
            if cache_key in self._cache:
                cached_resp, _ = self._cache[cache_key]
                return cached_resp
            # Fallback to SCHEDULED
            return ProviderResponse(
                airline_code=airline_code,
                flight_number=flight_number,
                status=FlightStatus.SCHEDULED
            )

        # Generate deterministic status
        try:
            mod = int(''.join([c for c in flight_number if c.isdigit()]) or 0) % 5
        except Exception:
            mod = 0

        status_map = {
            0: FlightStatus.SCHEDULED,
            1: FlightStatus.BOARDING,
            2: FlightStatus.ACTIVE,
            3: FlightStatus.DELAYED,
            4: FlightStatus.LANDED,
        }
        status = status_map.get(mod, FlightStatus.SCHEDULED)

        resp = ProviderResponse(
            airline_code=airline_code,
            flight_number=flight_number,
            status=status,
        )

        # Cache result
        self._cache[cache_key] = (resp, time.time())
        return resp


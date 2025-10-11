from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from pydantic import BaseModel

from ..common.logging_config import get_logger
from ..common.settings import settings
from .models import Flight, FlightStatus

logger = get_logger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderResponse(BaseModel):
    airline_code: str
    flight_number: str
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    scheduled_offblock: Optional[datetime] = None
    estimated_offblock: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    gate_dep: Optional[str] = None
    gate_arr: Optional[str] = None
    terminal_dep: Optional[str] = None
    terminal_arr: Optional[str] = None
    status: FlightStatus = FlightStatus.SCHEDULED
    status_reason: Optional[str] = None


@dataclass
class _CacheEntry:
    value: ProviderResponse
    expires_at: float


class RateLimiter:
    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._tokens: Dict[str, Tuple[int, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        tokens, ts = self._tokens.get(key, (self.max_per_minute, now))
        # refill each minute
        if now - ts >= 60:
            tokens = self.max_per_minute
            ts = now
        if tokens <= 0:
            self._tokens[key] = (tokens, ts)
            return False
        tokens -= 1
        self._tokens[key] = (tokens, ts)
        return True


class ProviderClient:
    """Deterministic provider shim.

    - 60s in-memory cache keyed by (airline, number, date)
    - Simple per-key rate limiting
    - Placeholder logic returns a stable pseudo-status without external calls
    """

    def __init__(self) -> None:
        self._cache: Dict[str, _CacheEntry] = {}
        self._limiter = RateLimiter(settings.provider_rate_limit_per_key_per_minute)

    def _cache_key(self, airline_code: str, flight_number: str, departure_date: str) -> str:
        return f"{airline_code}:{flight_number}:{departure_date}"

    def fetch_status(self, airline_code: str, flight_number: str, departure_date: str) -> ProviderResponse:
        cache_key = self._cache_key(airline_code, flight_number, departure_date)

        # Rate limit per flight key
        if not self._limiter.allow(cache_key):
            # Serve from cache if available
            cached = self._cache.get(cache_key)
            if cached and cached.expires_at > time.time():
                return cached.value
            # If no cache, degrade gracefully with SCHEDULED
            logger.warning("provider rate-limited; returning fallback for %s", cache_key)
            return ProviderResponse(airline_code=airline_code, flight_number=flight_number)

        # Cache check
        cached = self._cache.get(cache_key)
        if cached and cached.expires_at > time.time():
            return cached.value

        # Simulated deterministic response based on flight number modulo
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

        ttl = settings.provider_cache_ttl_seconds
        self._cache[cache_key] = _CacheEntry(value=resp, expires_at=time.time() + ttl)
        return resp

    def to_flight(self, flight_id: str, current: Optional[Flight], provider: ProviderResponse) -> Flight:
        now = utc_now()
        if current:
            return Flight(
                id=current.id,
                airline_code=provider.airline_code or current.airline_code,
                flight_number=provider.flight_number or current.flight_number,
                departure_airport=provider.departure_airport or current.departure_airport,
                arrival_airport=provider.arrival_airport or current.arrival_airport,
                scheduled_offblock=provider.scheduled_offblock or current.scheduled_offblock,
                estimated_offblock=provider.estimated_offblock or current.estimated_offblock,
                scheduled_arrival=provider.scheduled_arrival or current.scheduled_arrival,
                estimated_arrival=provider.estimated_arrival or current.estimated_arrival,
                gate_dep=provider.gate_dep or current.gate_dep,
                gate_arr=provider.gate_arr or current.gate_arr,
                terminal_dep=provider.terminal_dep or current.terminal_dep,
                terminal_arr=provider.terminal_arr or current.terminal_arr,
                status=provider.status or current.status,
                status_reason=provider.status_reason or current.status_reason,
                last_provider="mock-provider",
                last_updated=now,
            )
        return Flight(
            id=flight_id,
            airline_code=provider.airline_code,
            flight_number=provider.flight_number,
            departure_airport=provider.departure_airport,
            arrival_airport=provider.arrival_airport,
            scheduled_offblock=provider.scheduled_offblock,
            estimated_offblock=provider.estimated_offblock,
            scheduled_arrival=provider.scheduled_arrival,
            estimated_arrival=provider.estimated_arrival,
            gate_dep=provider.gate_dep,
            gate_arr=provider.gate_arr,
            terminal_dep=provider.terminal_dep,
            terminal_arr=provider.terminal_arr,
            status=provider.status,
            status_reason=provider.status_reason,
            last_provider="mock-provider",
            last_updated=now,
        )



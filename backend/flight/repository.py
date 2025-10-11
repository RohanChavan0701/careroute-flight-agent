from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import Flight, Event


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FlightRecord:
    flight: Flight
    events: List[Event] = field(default_factory=list)


class InMemoryFlightRepository:
    def __init__(self) -> None:
        self._flights: Dict[str, FlightRecord] = {}

    # CRUD for flights
    def upsert(self, flight: Flight) -> None:
        if flight.id not in self._flights:
            self._flights[flight.id] = FlightRecord(flight=flight, events=[])
        else:
            self._flights[flight.id].flight = flight

    def get(self, flight_id: str) -> Optional[Flight]:
        rec = self._flights.get(flight_id)
        return rec.flight if rec else None

    def delete(self, flight_id: str) -> bool:
        return self._flights.pop(flight_id, None) is not None

    # Event operations
    def append_event(self, flight_id: str, event: Event) -> None:
        if flight_id not in self._flights:
            raise KeyError("Flight not found for event append")
        self._flights[flight_id].events.append(event)

    def list_events(self, flight_id: str) -> List[Event]:
        rec = self._flights.get(flight_id)
        return list(rec.events) if rec else []



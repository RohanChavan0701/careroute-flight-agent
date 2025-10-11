from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from ..common.audit import write_audit
from ..common.logging_config import get_logger
from .models import Event, EventType, Flight, FlightStatus, ToolStatusResponse, TrackRequest
from .providers.base import FlightProvider
from .repository import InMemoryFlightRepository

logger = get_logger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FlightService:
    repo: InMemoryFlightRepository
    provider: FlightProvider

    def _flight_id(self, airline_code: str, flight_number: str, departure_date: str) -> str:
        return f"{airline_code.upper()}-{flight_number}-{departure_date}"

    def _to_flight(self, flight_id: str, current: Optional[Flight], provider_resp) -> Flight:
        """Convert provider response to Flight model."""
        now = utc_now()
        if current:
            return Flight(
                id=current.id,
                airline_code=provider_resp.airline_code or current.airline_code,
                flight_number=provider_resp.flight_number or current.flight_number,
                departure_airport=provider_resp.departure_airport or current.departure_airport,
                arrival_airport=provider_resp.arrival_airport or current.arrival_airport,
                scheduled_offblock=provider_resp.scheduled_offblock or current.scheduled_offblock,
                estimated_offblock=provider_resp.estimated_offblock or current.estimated_offblock,
                scheduled_arrival=provider_resp.scheduled_arrival or current.scheduled_arrival,
                estimated_arrival=provider_resp.estimated_arrival or current.estimated_arrival,
                gate_dep=provider_resp.gate_dep or current.gate_dep,
                gate_arr=provider_resp.gate_arr or current.gate_arr,
                terminal_dep=provider_resp.terminal_dep or current.terminal_dep,
                terminal_arr=provider_resp.terminal_arr or current.terminal_arr,
                status=provider_resp.status or current.status,
                status_reason=provider_resp.status_reason or current.status_reason,
                last_provider=type(self.provider).__name__,
                last_updated=now,
            )
        return Flight(
            id=flight_id,
            airline_code=provider_resp.airline_code,
            flight_number=provider_resp.flight_number,
            departure_airport=provider_resp.departure_airport,
            arrival_airport=provider_resp.arrival_airport,
            scheduled_offblock=provider_resp.scheduled_offblock,
            estimated_offblock=provider_resp.estimated_offblock,
            scheduled_arrival=provider_resp.scheduled_arrival,
            estimated_arrival=provider_resp.estimated_arrival,
            gate_dep=provider_resp.gate_dep,
            gate_arr=provider_resp.gate_arr,
            terminal_dep=provider_resp.terminal_dep,
            terminal_arr=provider_resp.terminal_arr,
            status=provider_resp.status,
            status_reason=provider_resp.status_reason,
            last_provider=type(self.provider).__name__,
            last_updated=now,
        )

    def track(self, req: TrackRequest) -> Flight:
        flight_id = self._flight_id(req.airline_code, req.flight_number, req.departure_date)
        current = self.repo.get(flight_id)
        provider_resp = self.provider.fetch_status(req.airline_code, req.flight_number, req.departure_date)
        flight = self._to_flight(flight_id, current, provider_resp)
        self.repo.upsert(flight)
        
        # Append events after upsert ensures flight exists
        try:
            if current is None:
                self.repo.append_event(
                    flight_id,
                    Event(t=utc_now(), type=EventType.STATUS_CHANGED, old=None, new=str(flight.status), note="tracking started"),
                )
            else:
                if current.status != flight.status:
                    self.repo.append_event(
                        flight_id,
                        Event(t=utc_now(), type=EventType.STATUS_CHANGED, old=str(current.status), new=str(flight.status)),
                    )
        except Exception as e:
            logger.error(f"Failed to append event for {flight_id}: {e}")
        
        write_audit(actor="system", action="flight.track", target=flight_id, details={"airline": req.airline_code, "number": req.flight_number})
        return flight

    def get(self, flight_id: str) -> Optional[Flight]:
        return self.repo.get(flight_id)

    def delete(self, flight_id: str) -> bool:
        ok = self.repo.delete(flight_id)
        if ok:
            write_audit(actor="system", action="flight.delete", target=flight_id, details={})
        return ok

    def events(self, flight_id: str) -> List[Event]:
        return self.repo.list_events(flight_id)

    def tool_get_status(self, flight_id: str) -> Optional[ToolStatusResponse]:
        current = self.repo.get(flight_id)
        if not current:
            return None

        status_text = self._status_text(current)
        return ToolStatusResponse(
            flight_id=flight_id,
            status_text=status_text,
            status=current.status,
            airline_code=current.airline_code,
            flight_number=current.flight_number,
            departure_airport=current.departure_airport,
            arrival_airport=current.arrival_airport,
            scheduled_offblock=current.scheduled_offblock,
            estimated_offblock=current.estimated_offblock,
            scheduled_arrival=current.scheduled_arrival,
            estimated_arrival=current.estimated_arrival,
            gate_dep=current.gate_dep,
            gate_arr=current.gate_arr,
            terminal_dep=current.terminal_dep,
            terminal_arr=current.terminal_arr,
        )

    def _status_text(self, f: Flight) -> str:
        if f.status == FlightStatus.DELAYED and f.estimated_offblock:
            return f"Flight {f.airline_code}{f.flight_number} delayed. New ETD {f.estimated_offblock.isoformat()}"
        if f.status == FlightStatus.BOARDING:
            return f"Flight {f.airline_code}{f.flight_number} is boarding. Gate {f.gate_dep or 'TBD'}"
        if f.status == FlightStatus.ACTIVE:
            return f"Flight {f.airline_code}{f.flight_number} is en route. ETA {f.estimated_arrival.isoformat() if f.estimated_arrival else 'unknown'}"
        if f.status == FlightStatus.LANDED:
            return f"Flight {f.airline_code}{f.flight_number} has landed."
        if f.status == FlightStatus.CANCELLED:
            return f"Flight {f.airline_code}{f.flight_number} is cancelled."
        if f.status == FlightStatus.DIVERTED:
            return f"Flight {f.airline_code}{f.flight_number} was diverted."
        return f"Flight {f.airline_code}{f.flight_number} scheduled."



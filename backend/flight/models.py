from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FlightStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    BOARDING = "BOARDING"
    ACTIVE = "ACTIVE"
    DELAYED = "DELAYED"
    LANDED = "LANDED"
    CANCELLED = "CANCELLED"
    DIVERTED = "DIVERTED"


class EventType(str, Enum):
    ETD_CHANGED = "ETD_CHANGED"
    GATE_CHANGED = "GATE_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    LANDED = "LANDED"
    ARRIVED = "ARRIVED"
    OFFBLOCK = "OFFBLOCK"
    ONBLOCK = "ONBLOCK"


class Event(BaseModel):
    t: datetime = Field(..., description="Event time in UTC")
    type: EventType
    old: Optional[str] = None
    new: Optional[str] = None
    note: Optional[str] = None


class Flight(BaseModel):
    id: str
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
    last_provider: Optional[str] = None
    last_updated: datetime

    model_config = {"use_enum_values": True}


class TrackRequest(BaseModel):
    airline_code: str
    flight_number: str
    departure_date: str  # ISO date YYYY-MM-DD to disambiguate same-number flights


class ToolStatusResponse(BaseModel):
    flight_id: str
    status_text: str
    status: FlightStatus
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



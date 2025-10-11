"""Data schemas for flight-agent."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FlightRaw(BaseModel):
    """Normalized flight data from provider."""
    
    airline: str
    flight_number: str
    origin_iata: str
    origin_city: str
    origin_tz: str
    destination_iata: str
    destination_city: str
    destination_tz: str
    
    scheduled_departure_local: Optional[str] = None  # YYYY-MM-DDTHH:MM
    estimated_departure_local: Optional[str] = None
    scheduled_arrival_local: Optional[str] = None
    estimated_arrival_local: Optional[str] = None
    
    gate: Optional[str] = None
    terminal: Optional[str] = None
    
    status: str  # ON_TIME, DELAYED, BOARDING, IN_AIR, LANDED, CANCELLED, UNKNOWN
    delay_minutes: Optional[int] = None


class Script(BaseModel):
    """AI-generated summary script."""
    
    text: str = Field(..., max_length=220, description="Plain text summary")
    ssml: str = Field(..., max_length=300, description="SSML markup for TTS")
    style: str = Field(default="conversational", description="TTS style hint")
    locale: str = Field(default="en-US", description="Locale for formatting")


class FlightStatusResponse(BaseModel):
    """Response payload for flight status request."""
    
    ok: bool
    data: Optional["FlightStatusData"] = None
    error: Optional[str] = None


class FlightStatusData(BaseModel):
    """Data payload when ok=true."""
    
    raw: FlightRaw
    script: Script
    hash: str = Field(..., description="Hash of raw data for caching")
    generated_at: datetime
    schema_version: str = Field(default="flight.status.v1")


class FlightStatusRequest(BaseModel):
    """Request payload for flight status."""
    
    flight_num: str = Field(..., description="Flight designator e.g. AA100")
    departure_date: str = Field(..., description="YYYY-MM-DD format")
    locale: str = Field(default="en-US", description="Locale for formatting")
    user_id: Optional[str] = None  # For audit logging


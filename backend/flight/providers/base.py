"""Base provider interface for flight data sources."""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from ..models import FlightStatus


class ProviderResponse(BaseModel):
    """Normalized response from any flight data provider."""
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


class FlightProvider(ABC):
    """Abstract base class for flight data providers."""
    
    @abstractmethod
    def fetch_status(
        self, 
        airline_code: str, 
        flight_number: str, 
        departure_date: str
    ) -> ProviderResponse:
        """Fetch flight status from the provider.
        
        Args:
            airline_code: IATA airline code (e.g., "AA", "UA")
            flight_number: Flight number without airline code
            departure_date: ISO date string YYYY-MM-DD
            
        Returns:
            ProviderResponse with normalized flight data
            
        Raises:
            Exception: If provider call fails or data is invalid
        """
        pass


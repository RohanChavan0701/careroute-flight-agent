"""Mock flight data provider for testing and demos."""

from datetime import datetime
from typing import Dict, Any
from .schemas import FlightRaw


class MockProvider:
    """
    Mock provider that returns deterministic flight data.
    Perfect for demos, testing, and development.
    """

    # Mock flight database
    FLIGHTS: Dict[str, Dict[str, Any]] = {
        "AA100": {
            "airline": "American Airlines",
            "flight_number": "AA100",
            "origin_iata": "JFK",
            "origin_city": "New York",
            "origin_tz": "America/New_York",
            "destination_iata": "LAX",
            "destination_city": "Los Angeles",
            "destination_tz": "America/Los_Angeles",
            "scheduled_departure_local": "14:00",
            "estimated_departure_local": "14:10",
            "scheduled_arrival_local": "17:30",
            "estimated_arrival_local": "17:40",
            "gate": "B12",
            "terminal": "8",
            "status": "IN_AIR",
            "delay_minutes": 10,
        },
        "DL789": {
            "airline": "Delta Air Lines",
            "flight_number": "DL789",
            "origin_iata": "ATL",
            "origin_city": "Atlanta",
            "origin_tz": "America/New_York",
            "destination_iata": "LAX",
            "destination_city": "Los Angeles",
            "destination_tz": "America/Los_Angeles",
            "scheduled_departure_local": "10:00",
            "estimated_departure_local": "10:30",
            "scheduled_arrival_local": "13:00",
            "estimated_arrival_local": "13:30",
            "gate": "A5",
            "terminal": "1",
            "status": "DELAYED",
            "delay_minutes": 30,
        },
        "UA456": {
            "airline": "United Airlines",
            "flight_number": "UA456",
            "origin_iata": "SFO",
            "origin_city": "San Francisco",
            "origin_tz": "America/Los_Angeles",
            "destination_iata": "JFK",
            "destination_city": "New York",
            "destination_tz": "America/New_York",
            "scheduled_departure_local": "08:00",
            "estimated_departure_local": "08:00",
            "scheduled_arrival_local": "16:00",
            "estimated_arrival_local": "16:00",
            "gate": "C15",
            "terminal": "7",
            "status": "SCHEDULED",
            "delay_minutes": None,
        },
        "WN123": {
            "airline": "Southwest Airlines",
            "flight_number": "WN123",
            "origin_iata": "LAS",
            "origin_city": "Las Vegas",
            "origin_tz": "America/Los_Angeles",
            "destination_iata": "DEN",
            "destination_city": "Denver",
            "destination_tz": "America/Denver",
            "scheduled_departure_local": "09:00",
            "estimated_departure_local": "09:00",
            "scheduled_arrival_local": "12:00",
            "estimated_arrival_local": "12:00",
            "gate": "B22",
            "terminal": "3",
            "status": "BOARDING",
            "delay_minutes": None,
        },
        "BA123": {
            "airline": "British Airways",
            "flight_number": "BA123",
            "origin_iata": "LHR",
            "origin_city": "London",
            "origin_tz": "Europe/London",
            "destination_iata": "JFK",
            "destination_city": "New York",
            "destination_tz": "America/New_York",
            "scheduled_departure_local": "10:00",
            "estimated_departure_local": None,
            "scheduled_arrival_local": "13:00",
            "estimated_arrival_local": None,
            "gate": None,
            "terminal": None,
            "status": "CANCELLED",
            "delay_minutes": None,
        },
    }

    async def get_status(self, flight_num: str, departure_date: str) -> FlightRaw:
        """
        Get mock flight status.

        Args:
            flight_num: Flight number (e.g. "AA100")
            departure_date: Departure date (YYYY-MM-DD format)

        Returns:
            FlightRaw object with mock data

        Raises:
            RuntimeError: If flight not found in mock database
        """
        # Normalize flight number (uppercase, remove spaces)
        flight_num = flight_num.upper().replace(" ", "")

        # Look up in mock database
        if flight_num not in self.FLIGHTS:
            raise RuntimeError(
                f"Flight {flight_num} not found in mock database. "
                f"Available flights: {', '.join(self.FLIGHTS.keys())}"
            )

        flight_data = self.FLIGHTS[flight_num].copy()

        # Add date to times
        date_prefix = departure_date
        for time_field in [
            "scheduled_departure_local",
            "estimated_departure_local",
            "scheduled_arrival_local",
            "estimated_arrival_local",
        ]:
            if flight_data.get(time_field):
                flight_data[time_field] = f"{date_prefix}T{flight_data[time_field]}"

        # Create FlightRaw object
        return FlightRaw(**flight_data)


"""Unit tests for flight-agent."""

import pytest
from datetime import datetime

from .provider import FlightAwareProvider
from .summarizer import GroqSummarizer
from .schemas import FlightRaw


class TestProviderMapping:
    """Test provider response mapping."""
    
    def test_map_to_flight_raw(self):
        """Test FlightAware response mapping to FlightRaw."""
        provider = FlightAwareProvider.__new__(FlightAwareProvider)
        
        # Sample FlightAware response
        fa_response = {
            "operator": "American Airlines",
            "operator_iata": "AA",
            "ident": "AA100",
            "origin": {
                "code_iata": "JFK",
                "city": "New York",
                "timezone": "America/New_York"
            },
            "destination": {
                "code_iata": "LAX",
                "city": "Los Angeles",
                "timezone": "America/Los_Angeles"
            },
            "scheduled_out": "2025-10-12T14:00:00Z",
            "estimated_out": "2025-10-12T14:10:00Z",
            "scheduled_in": "2025-10-12T17:30:00Z",
            "estimated_in": "2025-10-12T17:40:00Z",
            "gate_origin": "B12",
            "terminal_origin": "8",
            "status": "IN_AIR",
            "departure_delay": 10
        }
        
        result = provider._map_to_flight_raw(fa_response)
        
        assert result.airline == "American Airlines"
        assert result.flight_number == "AA100"
        assert result.origin_iata == "JFK"
        assert result.destination_iata == "LAX"
        assert result.status == "IN_AIR"
        assert result.delay_minutes == 10
        assert result.gate == "B12"
    
    def test_status_mapping(self):
        """Test status string mapping."""
        provider = FlightAwareProvider.__new__(FlightAwareProvider)
        
        assert provider._map_status("ON_TIME") == "ON_TIME"
        assert provider._map_status("DELAYED") == "DELAYED"
        assert provider._map_status("IN_AIR") == "IN_AIR"
        assert provider._map_status("ACTIVE") == "IN_AIR"
        assert provider._map_status("CANCELLED") == "CANCELLED"
        assert provider._map_status("CANCELED") == "CANCELLED"
        assert provider._map_status("LANDED") == "LANDED"
        assert provider._map_status("UNKNOWN_STATUS") == "UNKNOWN"


class TestSummarizer:
    """Test summarizer fallback logic."""
    
    def test_cancelled_flight_summary(self):
        """Test summary for cancelled flight."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        raw = FlightRaw(
            airline="AA",
            flight_number="AA100",
            origin_iata="JFK",
            origin_city="New York",
            origin_tz="America/New_York",
            destination_iata="LAX",
            destination_city="Los Angeles",
            destination_tz="America/Los_Angeles",
            scheduled_departure_local="2025-10-12T14:00",
            estimated_departure_local=None,
            scheduled_arrival_local="2025-10-12T17:30",
            estimated_arrival_local=None,
            gate=None,
            terminal=None,
            status="CANCELLED",
            delay_minutes=None
        )
        
        script = summarizer._fallback_summary(raw, "en-US")
        
        assert "cancelled" in script.text.lower()
        assert "<emphasis>cancelled</emphasis>" in script.ssml
        assert len(script.text) <= 220
        assert len(script.ssml) <= 300
        assert script.locale == "en-US"
    
    def test_delayed_flight_summary(self):
        """Test summary for delayed flight."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        raw = FlightRaw(
            airline="AA",
            flight_number="AA100",
            origin_iata="JFK",
            origin_city="New York",
            origin_tz="America/New_York",
            destination_iata="LAX",
            destination_city="Los Angeles",
            destination_tz="America/Los_Angeles",
            scheduled_departure_local="2025-10-12T14:00",
            estimated_departure_local="2025-10-12T14:30",
            scheduled_arrival_local="2025-10-12T17:30",
            estimated_arrival_local="2025-10-12T18:00",
            gate="B12",
            terminal="8",
            status="DELAYED",
            delay_minutes=30
        )
        
        script = summarizer._fallback_summary(raw, "en-US")
        
        assert "delayed" in script.text.lower()
        assert "30 minutes" in script.text
        assert "<emphasis>delayed" in script.ssml
        assert "<say-as interpret-as=\"time\">" in script.ssml
        assert len(script.text) <= 220
    
    def test_boarding_flight_summary(self):
        """Test summary for boarding flight."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        raw = FlightRaw(
            airline="AA",
            flight_number="AA100",
            origin_iata="JFK",
            origin_city="New York",
            origin_tz="America/New_York",
            destination_iata="LAX",
            destination_city="Los Angeles",
            destination_tz="America/Los_Angeles",
            scheduled_departure_local="2025-10-12T14:00",
            estimated_departure_local="2025-10-12T14:00",
            scheduled_arrival_local="2025-10-12T17:30",
            estimated_arrival_local="2025-10-12T17:30",
            gate="B12",
            terminal="8",
            status="BOARDING",
            delay_minutes=None
        )
        
        script = summarizer._fallback_summary(raw, "en-US")
        
        assert "boarding" in script.text.lower()
        assert "gate B12" in script.text
        assert "<emphasis>now boarding</emphasis>" in script.ssml
    
    def test_time_formatting_us(self):
        """Test US time formatting (12-hour)."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        assert summarizer._format_time("2025-10-12T14:30", "en-US") == "2:30 PM"
        assert summarizer._format_time("2025-10-12T09:15", "en-US") == "9:15 AM"
        assert summarizer._format_time("2025-10-12T00:00", "en-US") == "12:00 AM"
        assert summarizer._format_time("2025-10-12T12:00", "en-US") == "12:00 PM"
    
    def test_time_formatting_24h(self):
        """Test 24-hour time formatting."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        assert summarizer._format_time("2025-10-12T14:30", "en-GB") == "14:30"
        assert summarizer._format_time("2025-10-12T09:15", "fr-FR") == "09:15"
    
    def test_ssml_rules(self):
        """Test SSML formatting rules."""
        summarizer = GroqSummarizer.__new__(GroqSummarizer)
        
        raw = FlightRaw(
            airline="AA",
            flight_number="AA100",
            origin_iata="JFK",
            origin_city="New York",
            origin_tz="America/New_York",
            destination_iata="LAX",
            destination_city="Los Angeles",
            destination_tz="America/Los_Angeles",
            scheduled_departure_local="2025-10-12T14:00",
            estimated_departure_local="2025-10-12T14:00",
            scheduled_arrival_local="2025-10-12T17:30",
            estimated_arrival_local="2025-10-12T17:30",
            gate=None,
            terminal=None,
            status="ON_TIME",
            delay_minutes=None
        )
        
        script = summarizer._fallback_summary(raw, "en-US")
        
        # Check SSML has time tags
        assert '<say-as interpret-as="time">' in script.ssml
        # Check it's wrapped in speak tags
        assert script.ssml.startswith("<speak>")
        assert script.ssml.endswith("</speak>")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


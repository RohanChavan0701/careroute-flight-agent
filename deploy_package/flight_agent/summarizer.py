"""Groq-powered flight status summarizer."""

import json
import re
from typing import Dict, Any

import httpx

from .config import config
from .schemas import FlightRaw, Script


class SummarizerError(Exception):
    """Summarizer-related errors."""
    pass


class GroqSummarizer:
    """Groq LLM summarizer for flight status."""
    
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.model = config.GROQ_MODEL
        self.timeout = config.GROQ_TIMEOUT_SEC
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def summarize(self, raw: FlightRaw, locale: str = "en-US") -> Script:
        """Generate conversational summary from flight data.
        
        Args:
            raw: Normalized flight data
            locale: User locale for formatting
            
        Returns:
            Script with text and SSML
        """
        # Fallback if no API key
        if not self.api_key:
            return self._fallback_summary(raw, locale)
        
        try:
            # Build prompt
            prompt = self._build_prompt(raw, locale)
            
            # Call Groq
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful travel assistant. Summarize flight status in 1-2 sentences (max 220 chars). Return ONLY valid JSON: {\"text\": \"...\", \"ssml\": \"...\"}"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 200
                    }
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse response
            content = data["choices"][0]["message"]["content"]
            result = self._parse_json_response(content)
            
            return Script(
                text=result["text"][:220],
                ssml=result["ssml"][:300],
                style="conversational",
                locale=locale
            )
            
        except Exception as e:
            # Fallback on any error
            return self._fallback_summary(raw, locale)
    
    def _build_prompt(self, raw: FlightRaw, locale: str) -> str:
        """Build summarization prompt."""
        status_text = {
            "ON_TIME": "on time",
            "DELAYED": f"delayed{' by ' + str(raw.delay_minutes) + ' minutes' if raw.delay_minutes else ''}",
            "BOARDING": "now boarding",
            "IN_AIR": "in the air",
            "LANDED": "landed",
            "CANCELLED": "cancelled",
            "DIVERTED": "diverted",
            "UNKNOWN": "status unknown"
        }.get(raw.status, "status unknown")
        
        gate_info = f", gate {raw.gate}" if raw.gate else ""
        
        prompt = f"""Flight {raw.flight_number} from {raw.origin_iata} to {raw.destination_iata} is {status_text}{gate_info}.
Departure: {raw.estimated_departure_local or raw.scheduled_departure_local or 'TBD'}
Arrival: {raw.estimated_arrival_local or raw.scheduled_arrival_local or 'TBD'}

Generate:
1. "text": Plain English summary (1-2 sentences, max 220 chars)
2. "ssml": SSML version with <say-as interpret-as="time">HH:MM</say-as> for times and <emphasis> for delays/cancellations

Return ONLY valid JSON."""
        
        return prompt
    
    def _parse_json_response(self, content: str) -> Dict[str, str]:
        """Parse JSON from LLM response, handling markdown fences."""
        # Remove markdown code fences
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        try:
            result = json.loads(content)
            if "text" not in result or "ssml" not in result:
                raise ValueError("Missing required fields")
            return result
        except Exception:
            raise SummarizerError("Failed to parse LLM response")
    
    def _fallback_summary(self, raw: FlightRaw, locale: str) -> Script:
        """Deterministic fallback when Groq unavailable."""
        
        # Format time for locale
        dep_time = self._format_time(raw.estimated_departure_local or raw.scheduled_departure_local, locale)
        arr_time = self._format_time(raw.estimated_arrival_local or raw.scheduled_arrival_local, locale)
        
        # Build text based on status
        if raw.status == "CANCELLED":
            text = f"Flight {raw.flight_number} from {raw.origin_iata} to {raw.destination_iata} is cancelled."
            ssml = f"<speak>Flight {raw.flight_number} from {raw.origin_iata} to {raw.destination_iata} is <emphasis>cancelled</emphasis>.</speak>"
            
        elif raw.status == "DELAYED":
            delay_text = f" by {raw.delay_minutes} minutes" if raw.delay_minutes else ""
            text = f"Flight {raw.flight_number} is delayed{delay_text}. Departure at {dep_time}."
            ssml = f"<speak>Flight {raw.flight_number} is <emphasis>delayed{delay_text}</emphasis>. Departure at <say-as interpret-as=\"time\">{dep_time}</say-as>.</speak>"
            
        elif raw.status == "BOARDING":
            gate_text = f" at gate {raw.gate}" if raw.gate else ""
            text = f"Flight {raw.flight_number} is now boarding{gate_text}."
            ssml = f"<speak>Flight {raw.flight_number} is <emphasis>now boarding</emphasis>{gate_text}.</speak>"
            
        elif raw.status == "IN_AIR":
            text = f"Flight {raw.flight_number} is in the air. Expected arrival at {arr_time}."
            ssml = f"<speak>Flight {raw.flight_number} is in the air. Expected arrival at <say-as interpret-as=\"time\">{arr_time}</say-as>.</speak>"
            
        elif raw.status == "LANDED":
            text = f"Flight {raw.flight_number} has landed at {raw.destination_iata}."
            ssml = f"<speak>Flight {raw.flight_number} has landed at {raw.destination_iata}.</speak>"
            
        else:  # ON_TIME or UNKNOWN
            gate_text = f", gate {raw.gate}" if raw.gate else ""
            text = f"Flight {raw.flight_number} to {raw.destination_iata} departs at {dep_time}{gate_text}."
            ssml = f"<speak>Flight {raw.flight_number} to {raw.destination_iata} departs at <say-as interpret-as=\"time\">{dep_time}</say-as>{gate_text}.</speak>"
        
        # Ensure length limits
        text = text[:220]
        ssml = ssml[:300]
        
        return Script(text=text, ssml=ssml, style="conversational", locale=locale)
    
    def _format_time(self, time_str: str | None, locale: str) -> str:
        """Format time based on locale."""
        if not time_str:
            return "TBD"
        
        try:
            # Extract HH:MM from YYYY-MM-DDTHH:MM
            time_part = time_str.split('T')[-1][:5]
            
            if locale.startswith("en-US"):
                # Convert to 12-hour format
                hour, minute = map(int, time_part.split(':'))
                period = "AM" if hour < 12 else "PM"
                hour_12 = hour % 12 or 12
                return f"{hour_12}:{minute:02d} {period}"
            else:
                # Keep 24-hour format
                return time_part
                
        except Exception:
            return time_str


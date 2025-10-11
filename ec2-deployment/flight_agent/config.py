"""Configuration from environment variables."""

import os
from typing import Optional


class Config:
    """Application configuration loaded from environment."""
    
    # NATS (legacy)
    NATS_URL: str = os.getenv("NATS_URL", "nats://localhost:4222")
    NATS_SUBJECT: str = "guardian.flight.get_status.v1"
    
    # A2A Protocol
    A2A_PORT: int = int(os.getenv("A2A_PORT", "8001"))
    
    # Provider
    PROVIDER: str = os.getenv("PROVIDER", "flightaware")
    
    # FlightAware
    FA_API_KEY: str = os.getenv("FA_API_KEY", "")
    FA_BASE: str = os.getenv("FA_BASE", "https://aeroapi.flightaware.com/aeroapi")
    FA_TIMEOUT_SEC: float = float(os.getenv("FA_TIMEOUT_SEC", "6"))
    
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TIMEOUT_SEC: float = float(os.getenv("GROQ_TIMEOUT_SEC", "10"))
    
    # Retry settings
    RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_MS: list[int] = [100, 400, 900]
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls.PROVIDER == "flightaware" and not cls.FA_API_KEY:
            raise ValueError("FA_API_KEY is required when PROVIDER=flightaware")


config = Config()


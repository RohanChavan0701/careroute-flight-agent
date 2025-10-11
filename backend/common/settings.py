from typing import List

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class AppSettings(BaseSettings):
    """Centralized application settings loaded from environment variables.

    All secrets come from environment. No defaults for secrets except a development fallback
    for x-api-key to ease local testing.
    """

    api_key: str = Field(default_factory=lambda: os.getenv("API_KEY", "dev-key"))
    env: str = Field(default=os.getenv("ENV", "development"))

    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    # Provider protection
    provider_cache_ttl_seconds: int = Field(default=int(os.getenv("PROVIDER_CACHE_TTL_SECONDS", "60")))
    provider_rate_limit_per_key_per_minute: int = Field(
        default=int(os.getenv("PROVIDER_RATE_LIMIT_PER_KEY_PER_MINUTE", "10"))
    )

    # CORS (for Flutter mobile + local dev tooling)
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])

    # Flight provider selection
    flight_provider: str = Field(default=os.getenv("FLIGHT_PROVIDER", "mock"))
    
    # AeroDataBox config (when FLIGHT_PROVIDER=aerodatabox)
    aerobox_key: str = Field(default=os.getenv("AEROBOX_KEY", ""))
    aerobox_host: str = Field(default=os.getenv("AEROBOX_HOST", "aerodatabox.p.rapidapi.com"))
    aerobox_base: str = Field(default=os.getenv("AEROBOX_BASE", "https://aerodatabox.p.rapidapi.com"))
    aerobox_timeout: float = Field(default=float(os.getenv("AEROBOX_TIMEOUT_SEC", "6")))
    
    # FlightAware config (when FLIGHT_PROVIDER=flightaware)
    # Uses shorter env var names: FA_API_KEY, FA_BASE, FA_TIMEOUT_SEC
    fa_api_key: str = Field(default=os.getenv("FA_API_KEY", ""))
    fa_base: str = Field(default=os.getenv("FA_BASE", "https://aeroapi.flightaware.com/aeroapi"))
    fa_timeout: float = Field(default=float(os.getenv("FA_TIMEOUT_SEC", "6")))

    model_config = {"case_sensitive": False, "env_prefix": ""}


settings = AppSettings()



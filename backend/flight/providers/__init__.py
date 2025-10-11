"""Flight data providers - pluggable architecture for different APIs."""

__all__ = ["get_provider", "MockProvider", "AeroDataBoxProvider", "FlightAwareProvider"]

from .mock import MockProvider
from .aerodatabox import AeroDataBoxProvider
from .flightaware import FlightAwareProvider


def get_provider(provider_type: str):
    """Factory to create provider instances based on configuration."""
    providers = {
        "mock": MockProvider,
        "aerodatabox": AeroDataBoxProvider,
        "flightaware": FlightAwareProvider,
    }
    
    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_type}. Available: {list(providers.keys())}")
    
    return provider_class()


from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .common.errors import register_exception_handlers
from .common.logging_config import configure_logging, get_logger
from .common.settings import settings
from .flight.providers import get_provider
from .flight.repository import InMemoryFlightRepository
from .flight.router import create_router as create_flights_router
from .flight.service import FlightService
from .flight.tools_router import create_tools_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Guardian Buddy - API", version="0.1.0")

    # CORS for mobile + local tools
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    register_exception_handlers(app)

    # Wire services with configurable provider
    repo = InMemoryFlightRepository()
    provider = get_provider(settings.flight_provider)
    logger.info(f"Using flight provider: {settings.flight_provider}")
    flights = FlightService(repo=repo, provider=provider)

    app.include_router(create_flights_router(flights))
    app.include_router(create_tools_router(flights))

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()



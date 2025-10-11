from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..common.auth import require_api_key
from .models import TrackRequest
from .service import FlightService


def create_router(service: FlightService) -> APIRouter:
    router = APIRouter(prefix="/v1/flights", tags=["flights"], dependencies=[Depends(require_api_key)])

    @router.post("/track")
    def track(req: TrackRequest):
        return service.track(req)

    @router.get("/{flight_id}")
    def get_flight(flight_id: str):
        f = service.get(flight_id)
        if not f:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
        return f

    @router.get("/{flight_id}/events")
    def list_events(flight_id: str):
        return service.events(flight_id)

    @router.delete("/{flight_id}")
    def delete(flight_id: str):
        ok = service.delete(flight_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
        return {"ok": True}

    return router



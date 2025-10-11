from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..common.auth import require_api_key
from .service import FlightService


class ToolGetStatusRequest(BaseModel):
    flight_id: str


def create_tools_router(service: FlightService) -> APIRouter:
    router = APIRouter(prefix="/v1/tools", tags=["tools"], dependencies=[Depends(require_api_key)])

    @router.post("/get_flight_status")
    def get_flight_status(req: ToolGetStatusRequest):
        resp = service.tool_get_status(req.flight_id)
        if not resp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
        return resp

    return router



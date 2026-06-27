from __future__ import annotations

from fastapi import APIRouter, Query

from ..operation_service import list_recent_operations


router = APIRouter()


@router.get("/api/operations/recent")
async def api_recent_operations(limit: int = Query(20)) -> dict:
    return {"items": list_recent_operations(limit)}

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ai_bom.services.scanner import scan_repository


router = APIRouter()


class ScanRequest(BaseModel):
    dir: str = "."


@router.post("/scan")
async def scan(data: ScanRequest) -> Any:
    return scan_repository(data.dir)


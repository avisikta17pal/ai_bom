from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ai_bom.compliance.mapping import COMPLIANCE_MAPPING


router = APIRouter()


@router.get("/mappings")
async def get_mappings() -> Any:
    return {"mappings": COMPLIANCE_MAPPING}


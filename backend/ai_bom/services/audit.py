from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ai_bom.db.models import AuditLog


async def write_audit_log(
    session: AsyncSession,
    project_id: str,
    actor_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    data: dict[str, Any] | None = None,
) -> None:
    log = AuditLog(
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        data=data,
        created_at=datetime.utcnow(),
    )
    session.add(log)
    await session.commit()


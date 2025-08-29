from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_bom.core.security import get_current_user
from ai_bom.core.rbac import require_project_role
from ai_bom.db.models import BOM, BOMVersion, Project, User
from ai_bom.db.session import get_session
from ai_bom.services.exporter import export_bom
from ai_bom.services.storage import (
    presign_put,
    presign_get,
    create_multipart_upload,
    presign_upload_part,
    complete_multipart_upload,
)
from ai_bom.services.audit import write_audit_log


router = APIRouter()


class BOMComponent(BaseModel):
    component_id: str
    type: Literal["model", "dataset", "code", "dependency", "config", "artifact"]
    name: str
    description: str | None = None
    origin: dict | None = None
    fingerprint: dict
    license: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class Evaluation(BaseModel):
    eval_id: str | None = None
    dataset_id: str | None = None
    metrics: dict | None = None
    run_at: datetime | None = None
    notes: str | None = None


class BOMIn(BaseModel):
    name: str
    version: str
    description: str | None = None
    components: list[BOMComponent]
    evaluations: list[Evaluation] | None = None
    risk_assessment: dict | None = None
    signatures: list[dict] | None = None
    parent_bom: str | None = None


class BOMOut(BaseModel):
    id: str
    project_id: str
    name: str
    version: str
    description: str | None
    components: list[dict]
    signatures: list[dict] | None
    created_at: datetime


@router.post("/projects/{project_id}/boms", response_model=BOMOut, status_code=201)
async def create_bom(
    project_id: str,
    data: BOMIn,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: User = Depends(lambda project_id=Depends(lambda: None): None),
) -> Any:
    await require_project_role(project_id, ["owner", "editor"], session=session, user=user)
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    bom = BOM(project_id=project_id, name=data.name, description=data.description, created_by=user.id)
    session.add(bom)
    await session.flush()
    version = BOMVersion(
        bom_id=bom.id,
        version=data.version,
        components=[c.model_dump() for c in data.components],
        evaluations=[e.model_dump() for e in (data.evaluations or [])],
        risk_assessment=data.risk_assessment,
        signatures=data.signatures,
    )
    session.add(version)
    await session.commit()
    await write_audit_log(session, project_id=project_id, actor_id=user.id, entity_type="BOM", entity_id=bom.id, action="CREATE", data={"version_id": version.id})

    return BOMOut(
        id=version.id,
        project_id=project_id,
        name=bom.name,
        version=version.version,
        description=bom.description,
        components=version.components if isinstance(version.components, list) else [],
        signatures=version.signatures,
        created_at=version.created_at,
    )


@router.get("/boms/{version_id}", response_model=BOMOut)
async def get_bom(version_id: str, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> Any:
    result = await session.execute(select(BOMVersion, BOM.project_id, BOM.name, BOM.description).join(BOM, BOMVersion.bom_id == BOM.id).where(BOMVersion.id == version_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM not found")
    version, project_id, name, description = row
    return BOMOut(
        id=version.id,
        project_id=project_id,
        name=name,
        version=version.version,
        description=description,
        components=version.components if isinstance(version.components, list) else [],
        signatures=version.signatures,
        created_at=version.created_at,
    )


@router.get("/boms/{version_id}/export")
async def export_bom_endpoint(
    version_id: str,
    format: Literal["json", "jsonld", "pdf"] = Query(default="json"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Any:
    result = await session.execute(select(BOMVersion, BOM.name).join(BOM, BOMVersion.bom_id == BOM.id).where(BOMVersion.id == version_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="BOM not found")
    version, name = row
    bom = {
        "bom_id": version.id,
        "project_id": "",
        "name": name,
        "version": version.version,
        "components": version.components if isinstance(version.components, list) else [],
        "signatures": version.signatures or [],
        "created_by": "api",
        "created_at": version.created_at.replace(tzinfo=timezone.utc).isoformat(),
    }
    out_path = export_bom(bom, format)
    return {"path": out_path}


@router.post("/projects/{project_id}/uploads/presign")
async def create_presigned_upload(project_id: str, key: str, mime: str | None = None, size_bytes: int | None = None, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Any:
    await require_project_role(project_id, ["owner", "editor"], session=session, user=user)
    from ai_bom.core.config import get_settings

    settings = get_settings()
    if size_bytes and size_bytes > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    if mime and mime not in settings.allowed_upload_mime_types:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    return presign_put(f"{project_id}/{key}")


@router.get("/projects/{project_id}/downloads/presign")
async def create_presigned_download(project_id: str, key: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Any:
    await require_project_role(project_id, ["owner", "editor", "viewer"], session=session, user=user)
    return presign_get(f"{project_id}/{key}")


@router.post("/projects/{project_id}/uploads/multipart/init")
async def multipart_init(project_id: str, key: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Any:
    await require_project_role(project_id, ["owner", "editor"], session=session, user=user)
    return create_multipart_upload(f"{project_id}/{key}")


@router.get("/projects/{project_id}/uploads/multipart/part")
async def multipart_presign_part(project_id: str, key: str, upload_id: str, part_number: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Any:
    await require_project_role(project_id, ["owner", "editor"], session=session, user=user)
    return presign_upload_part(f"{project_id}/{key}", upload_id, part_number)


@router.post("/projects/{project_id}/uploads/multipart/complete")
async def multipart_complete(project_id: str, key: str, upload_id: str, parts: list[dict], user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Any:
    await require_project_role(project_id, ["owner", "editor"], session=session, user=user)
    return complete_multipart_upload(f"{project_id}/{key}", upload_id, parts)


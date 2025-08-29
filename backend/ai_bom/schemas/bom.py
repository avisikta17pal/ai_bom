from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


UUID_PATTERN = re.compile(r"^[0-9a-fA-F-]{36}$")
HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}|[0-9a-fA-F]{128}$")


class GitOrigin(BaseModel):
    repo: str | None = None
    commit: str | None = None
    path: str | None = None


class Origin(BaseModel):
    git: GitOrigin | None = None
    url: HttpUrl | None = None
    s3: str | None = None

    @field_validator("git", mode="before")
    @classmethod
    def empty_git_to_none(cls, v: Any) -> Any:
        if isinstance(v, dict) and not any(v.values()):
            return None
        return v

    @field_validator("s3")
    @classmethod
    def validate_s3(cls, v: Optional[str]) -> Optional[str]:
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[HttpUrl]) -> Optional[HttpUrl]:
        return v

    @field_validator("git", mode="after")
    @classmethod
    def ensure_any_present(cls, v: Any, info):  # type: ignore[no-untyped-def]
        data = info.data
        if not (v or data.get("url") or data.get("s3")):
            raise ValueError("At least one of git/url/s3 must be provided for origin")
        return v


class Fingerprint(BaseModel):
    algorithm: Literal["sha256", "sha512"]
    hash: str

    @field_validator("hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        if not HEX_PATTERN.match(v):
            raise ValueError("fingerprint.hash must be hex string (sha256 or sha512)")
        return v


class Component(BaseModel):
    component_id: str
    type: Literal["model", "dataset", "code", "dependency", "config", "artifact"]
    name: str
    description: str | None = None
    origin: Origin | None = None
    fingerprint: Fingerprint
    license: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Evaluation(BaseModel):
    eval_id: str | None = None
    dataset_id: str | None = None
    metrics: dict[str, Any] | None = None
    run_at: datetime | None = None
    notes: str | None = None


class Signature(BaseModel):
    key_id: str
    algorithm: str
    signature: str
    signed_at: datetime


class BOMModel(BaseModel):
    bom_id: str
    project_id: str
    name: str
    version: str
    description: str | None = None
    components: list[Component]
    evaluations: list[Evaluation] | None = None
    risk_assessment: dict[str, Any] | None = None
    signatures: list[Signature] | None = None
    created_by: str
    created_at: datetime
    parent_bom: str | None = None

    @field_validator("bom_id", "project_id")
    @classmethod
    def validate_uuid_like(cls, v: str) -> str:
        if not UUID_PATTERN.match(v):
            raise ValueError("must be uuid-like string")
        return v


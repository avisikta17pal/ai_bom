from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_bom.db.base import Base


class User(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("user.id"))

    owner: Mapped[User] = relationship("User")
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    boms: Mapped[list["BOM"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectRoleEnum(str, Enum):  # type: ignore[misc]
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class ProjectMember(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("project.id"))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("user.id"))
    role: Mapped[str] = mapped_column(String, default=ProjectRoleEnum.viewer)

    project: Mapped[Project] = relationship("Project", back_populates="memberships")
    user: Mapped[User] = relationship("User", back_populates="memberships")


class BOM(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("project.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("user.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="boms")
    versions: Mapped[list["BOMVersion"]] = relationship(back_populates="bom", cascade="all, delete-orphan")


class BOMVersion(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bom_id: Mapped[str] = mapped_column(String, ForeignKey("bom.id"), index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    components: Mapped[dict[str, Any] | list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    evaluations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    risk_assessment: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    signatures: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    parent_bom: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bom: Mapped[BOM] = relationship("BOM", back_populates="versions")


class AuditLog(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("project.id"))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str] = mapped_column(String, ForeignKey("user.id"))
    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


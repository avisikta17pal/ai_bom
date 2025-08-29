from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_bom.core.config import get_settings
from ai_bom.db.models import User
from ai_bom.db.session import get_session


pwd_hasher = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_hasher.verify(hashed, password)
    except Exception:
        return False


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    if expires_minutes is None:
        expires_minutes = settings.security.access_token_expires_minutes
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    result = await session.execute(select(User).where(User.id == sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


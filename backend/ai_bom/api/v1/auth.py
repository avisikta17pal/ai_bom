from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_bom.core.security import create_access_token, get_password_hash, verify_password
from ai_bom.db.models import User
from ai_bom.db.session import get_session


router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse, responses={401: {"description": "Invalid credentials"}})
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)) -> Any:
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", response_model=TokenResponse, responses={400: {"description": "Already exists"}})
async def signup(data: SignupRequest, session: AsyncSession = Depends(get_session)) -> Any:
    exists = await session.execute(select(User).where(User.email == data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
    user = User(email=data.email, password_hash=get_password_hash(data.password))
    session.add(user)
    await session.commit()
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)) -> Any:
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = get_password_hash(data.new_password)
    await session.commit()
    return {"status": "ok"}


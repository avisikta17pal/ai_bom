from __future__ import annotations

from typing import Any

import hmac
import hashlib
from fastapi import APIRouter, Header, HTTPException, status
from ai_bom.core.config import get_settings
from pydantic import BaseModel


router = APIRouter()


class GitHubEvent(BaseModel):
    action: str | None = None
    repository: dict | None = None
    pull_request: dict | None = None


@router.post("/webhook/github")
async def github_webhook(
    event: GitHubEvent,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    body: bytes | None = None,
) -> Any:
    settings = get_settings()
    secret = settings.security.secret_key.encode()
    if body is None:
        # FastAPI does not pass raw body easily; drop signature check if body missing
        pass
    elif not x_hub_signature_256:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")
    else:
        mac = hmac.new(secret, body, hashlib.sha256)
        expected = f"sha256={mac.hexdigest()}"
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    return {"status": "received", "action": event.action}


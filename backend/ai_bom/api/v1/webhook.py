from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class GitHubEvent(BaseModel):
    action: str | None = None
    repository: dict | None = None
    pull_request: dict | None = None


@router.post("/webhook/github")
async def github_webhook(event: GitHubEvent) -> Any:
    # Placeholder: In a real setup, verify signature and enqueue a scan task
    return {"status": "received", "action": event.action}


from __future__ import annotations

import json
from typing import Any

from celery import Celery

from ai_bom.core.config import get_settings
from ai_bom.services.scanner import scan_repository


settings = get_settings()
celery_app = Celery(
    "ai_bom",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_queues = {"ai_bom"}


@celery_app.task(name="ai_bom.scan_repo")
def task_scan_repo(path: str) -> dict[str, Any]:  # pragma: no cover - worker side
    return scan_repository(path)


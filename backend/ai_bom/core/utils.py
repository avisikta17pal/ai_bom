from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, BinaryIO

import boto3
import orjson

from ai_bom.core.config import get_settings


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_json(data: dict[str, Any]) -> bytes:
    return orjson.dumps(data, option=orjson.OPT_SORT_KEYS)


def aggregate_bom_hash(bom: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(bom)).hexdigest()


def get_git_info(dir: str | Path) -> dict[str, Any]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(dir)).decode().strip()
    except Exception:
        commit = ""
    try:
        repo = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], cwd=str(dir)).decode().strip()
    except Exception:
        repo = ""
    return {"repo": repo, "commit": commit}


def get_s3_client():  # pragma: no cover - external service
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=(f"https://{settings.s3.endpoint}" if settings.s3.secure else f"http://{settings.s3.endpoint}"),
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )


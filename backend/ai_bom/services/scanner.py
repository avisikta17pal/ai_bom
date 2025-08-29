from __future__ import annotations

import hashlib
import json
import os
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Any

from ai_bom.core.utils import get_git_info, sha256_file


MODEL_SUFFIXES = (".pt", ".ckpt", ".bin", ".h5")
DATA_SUFFIXES = (".csv", ".parquet", ".jsonl")


def _fingerprint_small(path: pathlib.Path, max_bytes: int = 2 * 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    read = 0
    with open(path, "rb") as f:
        while read < max_bytes:
            chunk = f.read(min(1024 * 1024, max_bytes - read))
            if not chunk:
                break
            hasher.update(chunk)
            read += len(chunk)
    return hasher.hexdigest()


def scan_repository(dir: str = ".") -> dict[str, Any]:
    base = pathlib.Path(dir)
    git = get_git_info(base)
    components: list[dict[str, Any]] = []

    # Detect dependencies
    deps: list[str] = []
    if (base / "pyproject.toml").exists():
        deps.append("pyproject.toml")
    if (base / "requirements.txt").exists():
        deps.append("requirements.txt")
    for d in deps:
        components.append(
            {
                "component_id": str(uuid.uuid4()),
                "type": "dependency",
                "name": d,
                "origin": {"git": git, "path": d},
                "fingerprint": {"algorithm": "sha256", "hash": sha256_file(base / d)},
            }
        )

    # Detect model files
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in MODEL_SUFFIXES:
            components.append(
                {
                    "component_id": str(uuid.uuid4()),
                    "type": "model",
                    "name": str(path.relative_to(base)),
                    "origin": {"git": git, "path": str(path)},
                    "fingerprint": {"algorithm": "sha256", "hash": sha256_file(path)},
                }
            )
        elif path.suffix.lower() in DATA_SUFFIXES:
            components.append(
                {
                    "component_id": str(uuid.uuid4()),
                    "type": "dataset",
                    "name": str(path.relative_to(base)),
                    "origin": {"git": git, "path": str(path)},
                    "fingerprint": {"algorithm": "sha256", "hash": _fingerprint_small(path)},
                }
            )

    bom = {
        "bom_id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "name": base.name,
        "version": "0.1.0",
        "description": f"Auto-scanned BOM for {base.name}",
        "components": components,
        "created_by": os.getenv("USER", "cli-user"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return bom


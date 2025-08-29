from __future__ import annotations

import json
import os
import pathlib
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

import typer

from ai_bom.core.config import get_settings
from ai_bom.services.scanner import scan_repository
from ai_bom.services.signer import (
    compute_bom_hash,
    ed25519_keygen,
    load_private_key,
    sign_bom,
    verify_bom_signature,
)
from ai_bom.services.exporter import export_bom


app = typer.Typer(help="ai-bom command line interface")


@app.command()
def init(dir: str = ".") -> None:
    """Initialize ai-bom project structure in the given directory."""
    base = pathlib.Path(dir)
    config_dir = base / ".ai-bom"
    keys_dir = config_dir / "keys"
    config_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)
    sample_bom = {
        "bom_id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "name": "sample-model",
        "version": "0.1.0",
        "description": "Sample AI-BOM",
        "components": [],
        "created_by": os.getenv("USER", "cli-user"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (base / "ai-bom.json").write_text(json.dumps(sample_bom, indent=2), encoding="utf-8")
    typer.echo(f"Initialized ai-bom in {base}")


@app.command()
def scan(dir: str = ".", output: str = "bom.json") -> None:
    """Scan repository to generate draft BOM JSON."""
    bom = scan_repository(dir)
    pathlib.Path(output).write_text(json.dumps(bom, indent=2), encoding="utf-8")
    typer.echo(f"Wrote {output}")


@app.command()
def keygen(outdir: str = ".ai-bom/keys") -> None:
    """Generate an ed25519 keypair."""
    private_path, public_path, key_id = ed25519_keygen(outdir)
    typer.echo(f"Generated keypair: {private_path} (private), {public_path} (public). key_id={key_id}")


@app.command()
def sign(bom_path: str, key: str) -> None:
    """Sign a BOM JSON with ed25519 private key."""
    data = json.loads(pathlib.Path(bom_path).read_text(encoding="utf-8"))
    private_key = load_private_key(key)
    signed = sign_bom(data, private_key)
    pathlib.Path(bom_path).write_text(json.dumps(signed, indent=2), encoding="utf-8")
    typer.echo("Signed BOM and updated file")


@app.command()
def verify(bom_path: str, public_key_path: Optional[str] = None) -> None:
    """Verify signature and fingerprints of a BOM."""
    data = json.loads(pathlib.Path(bom_path).read_text(encoding="utf-8"))
    ok = verify_bom_signature(data, public_key_path)
    if ok:
        typer.echo("Verification OK")
        raise typer.Exit(code=0)
    else:
        typer.echo("Verification FAILED")
        raise typer.Exit(code=1)


@app.command()
def export(bom_path: str, format: str = "json") -> None:  # noqa: A002 - typer arg name
    """Export a BOM and compliance dossier in the given format (json|jsonld|c2pa|pdf)."""
    data = json.loads(pathlib.Path(bom_path).read_text(encoding="utf-8"))
    out_path = export_bom(data, format)
    typer.echo(f"Exported to {out_path}")


@app.command("deploy-check")
def deploy_check(dir: str = ".") -> None:
    """Check presence of ai-bom.json or bom.json and that it's signed when model files are present."""
    base = pathlib.Path(dir)
    bom_path = None
    for candidate in ("ai-bom.json", "bom.json"):
        candidate_path = base / candidate
        if candidate_path.exists():
            bom_path = candidate_path
            break
    if not bom_path:
        typer.echo("No BOM file found", err=True)
        raise typer.Exit(code=2)
    data = json.loads(bom_path.read_text(encoding="utf-8"))
    # If there are model artifacts, require signature
    has_model = any(c.get("type") == "model" for c in data.get("components", []))
    if has_model and not data.get("signatures"):
        typer.echo("Unsigned BOM with model artifacts", err=True)
        raise typer.Exit(code=3)
    typer.echo("Deploy check passed")


def main() -> None:  # pragma: no cover - entrypoint
    app()


if __name__ == "__main__":  # pragma: no cover - script use
    main()


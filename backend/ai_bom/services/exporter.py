from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ai_bom.compliance.mapping import COMPLIANCE_MAPPING, build_compliance_report


def export_bom(bom: dict[str, Any], format: str = "json") -> str:  # noqa: A002 - param name by spec
    out_dir = Path("exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    if format == "json":
        path = out_dir / f"{bom['name']}-{bom['version']}.json"
        payload = dict(bom)
        payload["compliance_report"] = build_compliance_report(bom)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)
    elif format == "jsonld":
        path = out_dir / f"{bom['name']}-{bom['version']}.jsonld"
        jsonld = {
            "@context": "https://schema.org/",
            "@type": "Dataset",
            "name": bom["name"],
            "version": bom["version"],
            "hasPart": bom.get("components", []),
            "dateCreated": bom.get("created_at"),
        }
        path.write_text(json.dumps(jsonld, indent=2), encoding="utf-8")
        return str(path)
    elif format == "pdf":
        path = out_dir / f"{bom['name']}-{bom['version']}.pdf"
        _export_pdf(bom, str(path))
        return str(path)
    elif format == "c2pa":
        # Placeholder: return JSON with C2PA-like structure
        path = out_dir / f"{bom['name']}-{bom['version']}.c2pa.json"
        payload = {
            "manifest": {
                "title": bom["name"],
                "version": bom["version"],
                "assertions": [{"label": "ai-bom", "data": bom}],
            }
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)
    else:
        raise ValueError("Unsupported export format")


def _export_pdf(bom: dict[str, Any], path: str) -> None:
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"AI-BOM Technical File: {bom['name']} v{bom['version']}")
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Created at: {bom.get('created_at', '')}")
    y -= 20
    c.drawString(50, y, f"Description: {bom.get('description', '')[:80]}")
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Components:")
    c.setFont("Helvetica", 9)
    y -= 15
    for comp in bom.get("components", [])[:20]:
        text = f"- {comp.get('type')} {comp.get('name')} {comp.get('fingerprint', {}).get('hash', '')[:12]}"
        c.drawString(60, y, text)
        y -= 12
        if y < 80:
            c.showPage()
            y = height - 50
    c.showPage()
    c.save()


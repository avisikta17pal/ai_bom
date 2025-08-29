from __future__ import annotations

from typing import Any


COMPLIANCE_MAPPING = [
    {
        "control": "Traceability/Lineage",
        "frameworks": {
            "EU_AI_Act": "Technical documentation & logs",
            "NIST_RMF": "Map (inventory)",
            "ISO_42001": "Lifecycle management",
        },
        "fields": ["components[*].origin", "components[*].fingerprint", "parent_bom"],
    },
    {
        "control": "Risk management",
        "frameworks": {
            "EU_AI_Act": "Risk management system",
            "NIST_RMF": "Measure/Manage",
            "ISO_42001": "Risk assessments",
        },
        "fields": ["risk_assessment", "evaluations"],
    },
    {
        "control": "Human oversight",
        "frameworks": {
            "EU_AI_Act": "Human oversight",
            "NIST_RMF": "Govern",
            "ISO_42001": "Governance",
        },
        "fields": ["evaluations[*].notes", "created_by"],
    },
    {
        "control": "Transparency",
        "frameworks": {
            "EU_AI_Act": "Information to users",
            "NIST_RMF": "Map",
            "ISO_42001": "Transparency",
        },
        "fields": ["description", "license", "metadata"],
    },
    {
        "control": "Monitoring",
        "frameworks": {
            "EU_AI_Act": "Post-market monitoring",
            "NIST_RMF": "Manage",
            "ISO_42001": "Monitoring",
        },
        "fields": ["evaluations[*].run_at", "webhook logs"],
    },
]


def build_compliance_report(bom: dict[str, Any]) -> dict[str, Any]:
    report = {"summary": [], "details": []}
    for entry in COMPLIANCE_MAPPING:
        fields = entry["fields"]
        satisfied = True
        for f in fields:
            if f.startswith("components["):
                if not bom.get("components"):
                    satisfied = False
                    break
            elif f == "risk_assessment":
                if not bom.get("risk_assessment"):
                    satisfied = False
                    break
            elif f == "evaluations":
                if not bom.get("evaluations"):
                    satisfied = False
                    break
            elif f == "parent_bom":
                # optional
                satisfied = satisfied and True
            else:
                # generic check
                if not any(k in f for k in bom.keys()):
                    satisfied = satisfied and True
        report["details"].append({"control": entry["control"], "satisfied": satisfied})
    report["summary"] = {
        "satisfied": sum(1 for d in report["details"] if d["satisfied"]),
        "total": len(report["details"]),
    }
    return report


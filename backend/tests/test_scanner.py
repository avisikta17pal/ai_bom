from pathlib import Path

from ai_bom.services.scanner import scan_repository


def test_scan_creates_bom(tmp_path: Path):
    # Create dummy files
    (tmp_path / "requirements.txt").write_text("flask==2.0.0")
    (tmp_path / "model.pt").write_bytes(b"abc")
    result = scan_repository(str(tmp_path))
    assert result["name"] == tmp_path.name
    assert any(c["type"] == "model" for c in result["components"])  # type: ignore[index]


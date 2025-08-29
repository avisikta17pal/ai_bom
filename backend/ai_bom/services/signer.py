from __future__ import annotations

import base64
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Any, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from ai_bom.core.utils import aggregate_bom_hash, canonical_json


def ed25519_keygen(outdir: str | pathlib.Path) -> tuple[str, str, str]:
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = str(uuid.uuid4())
    private_path = out / f"{key_id}.key"
    public_path = out / f"{key_id}.pub"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    return str(private_path), str(public_path), key_id


def load_private_key(path: str | pathlib.Path) -> Ed25519PrivateKey:
    data = pathlib.Path(path).read_bytes()
    return serialization.load_pem_private_key(data, password=None)


def load_public_key(path: str | pathlib.Path) -> Ed25519PublicKey:
    data = pathlib.Path(path).read_bytes()
    return serialization.load_pem_public_key(data)


def compute_bom_hash(bom: dict[str, Any]) -> str:
    return aggregate_bom_hash(bom)


def sign_bom(bom: dict[str, Any], private_key: Ed25519PrivateKey) -> dict[str, Any]:
    payload = {k: v for k, v in bom.items() if k != "signatures"}
    digest_hex = compute_bom_hash(payload)
    signature = private_key.sign(bytes.fromhex(digest_hex))
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    key_id = base64.urlsafe_b64encode(public_bytes).decode()
    signed = dict(bom)
    signatures = list(bom.get("signatures", []))
    signatures.append(
        {
            "key_id": key_id,
            "algorithm": "ed25519-sha256",
            "signature": base64.b64encode(signature).decode(),
            "signed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    signed["signatures"] = signatures
    return signed


def verify_bom_signature(bom: dict[str, Any], public_key_path: str | None = None) -> bool:
    signatures = bom.get("signatures") or []
    if not signatures:
        return False
    sig = signatures[-1]
    digest_hex = compute_bom_hash({k: v for k, v in bom.items() if k != "signatures"})
    signature = base64.b64decode(sig.get("signature", ""))
    try:
        if public_key_path:
            public_key = load_public_key(public_key_path)
        else:
            # Attempt to reconstruct from key_id (raw ed25519 key in base64url)
            key_bytes = base64.urlsafe_b64decode(sig["key_id"])  # type: ignore[arg-type]
            public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
        public_key.verify(signature, bytes.fromhex(digest_hex))
        return True
    except Exception:
        return False


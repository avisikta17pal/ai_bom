from ai_bom.services.signer import ed25519_keygen, load_private_key, sign_bom, verify_bom_signature


def test_sign_and_verify(tmp_path):
    priv, pub, key_id = ed25519_keygen(tmp_path)
    private_key = load_private_key(priv)
    bom = {"name": "x", "version": "1", "components": [], "created_by": "t", "created_at": "2024-01-01T00:00:00Z", "project_id": "p", "bom_id": "b"}
    signed = sign_bom(bom, private_key)
    assert verify_bom_signature(signed)


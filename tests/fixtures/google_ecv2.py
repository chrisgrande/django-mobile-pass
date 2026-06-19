"""ECv2SigningOnly fixtures for Google Wallet callback tests."""

from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from django_mobile_pass.google.callback_verification import PROTOCOL_VERSION, SENDER_ID, build_signed_string

_FIXTURES_DIR = Path(__file__).resolve().parent / "ecv2"


def load_ec_keypair(private_pem_path: Path | str) -> dict[str, str]:
    private_pem = Path(private_pem_path).read_text()
    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise RuntimeError(f"Expected an EC private key in {private_pem_path}")

    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    public_base64 = re.sub(r"\s+|-----(BEGIN|END) PUBLIC KEY-----", "", public_pem)
    return {"private": private_pem, "public_base64": public_base64}


def ecv2_root_keypair() -> dict[str, str]:
    return load_ec_keypair(_FIXTURES_DIR / "ecv2-root-key.pem")


def ecv2_intermediate_keypair() -> dict[str, str]:
    return load_ec_keypair(_FIXTURES_DIR / "ecv2-intermediate-key.pem")


def ecv2_stale_root_keypair() -> dict[str, str]:
    return load_ec_keypair(_FIXTURES_DIR / "ecv2-stale-root-key.pem")


def ecdsa_sign(private_pem: str, data: bytes) -> bytes:
    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise RuntimeError("Expected an EC private key for ECDSA signing.")
    return private_key.sign(data, ec.ECDSA(hashes.SHA256()))


def build_ecv2_callback_payload(
    *,
    root_private_pem: str,
    intermediate_private_pem: str,
    intermediate_public_base64: str,
    issuer_id: str,
    message: dict,
    intermediate_expiration_ms: int | None = None,
) -> dict:
    intermediate_expiration_ms = intermediate_expiration_ms or int(round((time.time() + 86400) * 1000))

    signed_key = json.dumps(
        {
            "keyValue": intermediate_public_base64,
            "keyExpiration": str(intermediate_expiration_ms),
        },
        separators=(",", ":"),
    )

    intermediate_signed_string = build_signed_string([SENDER_ID, PROTOCOL_VERSION, signed_key])
    intermediate_signature = ecdsa_sign(root_private_pem, intermediate_signed_string)

    signed_message = json.dumps(message, separators=(",", ":"))
    message_signed_string = build_signed_string([SENDER_ID, issuer_id, PROTOCOL_VERSION, signed_message])
    message_signature = ecdsa_sign(intermediate_private_pem, message_signed_string)

    return {
        "protocolVersion": PROTOCOL_VERSION,
        "intermediateSigningKey": {
            "signedKey": signed_key,
            "signatures": [base64.b64encode(intermediate_signature).decode()],
        },
        "signature": base64.b64encode(message_signature).decode(),
        "signedMessage": signed_message,
    }


def root_keys_response(root_public_base64: str, root_expiration_ms: int | None = None) -> dict:
    root_expiration_ms = root_expiration_ms or int(round((time.time() + 7 * 86400) * 1000))
    return {
        "keys": [
            {
                "keyValue": root_public_base64,
                "protocolVersion": PROTOCOL_VERSION,
                "keyExpiration": str(root_expiration_ms),
            }
        ]
    }

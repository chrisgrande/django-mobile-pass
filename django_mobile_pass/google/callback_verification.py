from __future__ import annotations

import base64
import json
import struct
import time
from typing import Any

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

SENDER_ID = "GooglePayPasses"
PROTOCOL_VERSION = "ECv2SigningOnly"
ROOT_KEYS_URL = "https://pay.google.com/gp/m/issuer/keys"
ROOT_KEYS_CACHE_KEY = "mobile-pass.google.root-keys"
ROOT_KEYS_FALLBACK_TTL_SECONDS = 1800
ROOT_KEYS_MIN_TTL_SECONDS = 60
ROOT_KEYS_TTL_SAFETY_MARGIN_SECONDS = 60
ROOT_KEYS_HTTP_TIMEOUT_SECONDS = 5


class GoogleCallbackVerificationError(Exception):
    pass


def build_signed_string(parts: list[str]) -> bytes:
    output = b""
    for part in parts:
        part_bytes = part.encode("utf-8")
        output += struct.pack("<I", len(part_bytes)) + part_bytes
    return output


def base64_to_pem(value: str) -> str:
    if "-----BEGIN" in value:
        return value
    chunked = "\n".join(value[i : i + 64] for i in range(0, len(value), 64))
    return f"-----BEGIN PUBLIC KEY-----\n{chunked}\n-----END PUBLIC KEY-----\n"


def verify_signature(signed_string: bytes, base64_signature: str, base64_public_key: str) -> bool:
    try:
        signature = base64.b64decode(base64_signature, validate=True)
    except (ValueError, TypeError):
        return False

    try:
        public_key = serialization.load_pem_public_key(base64_to_pem(base64_public_key).encode())
    except (ValueError, TypeError):
        return False

    try:
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(signature, signed_string, padding.PKCS1v15(), hashes.SHA256())
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(signature, signed_string, ec.ECDSA(hashes.SHA256()))
        else:
            return False
        return True
    except InvalidSignature:
        return False


def now_millis() -> int:
    return int(round(time.time() * 1000))


def extract_usable_key_values(keys: list[Any]) -> list[str]:
    now = now_millis()
    usable: list[str] = []
    for key in keys:
        if not isinstance(key, dict):
            continue
        if key.get("protocolVersion") != PROTOCOL_VERSION:
            continue
        expiration = key.get("keyExpiration")
        if expiration is not None and int(expiration) <= now:
            continue
        key_value = str(key.get("keyValue", ""))
        if key_value:
            usable.append(key_value)
    return usable


def resolve_cache_ttl_seconds(keys: list[Any]) -> int:
    now = now_millis()
    earliest_expiration: int | None = None
    for key in keys:
        if not isinstance(key, dict) or "keyExpiration" not in key:
            continue
        expiration = int(key["keyExpiration"])
        if expiration <= now:
            continue
        if earliest_expiration is None or expiration < earliest_expiration:
            earliest_expiration = expiration
    if earliest_expiration is None:
        return ROOT_KEYS_FALLBACK_TTL_SECONDS
    seconds_until_expiration = (earliest_expiration - now) // 1000
    ttl = seconds_until_expiration - ROOT_KEYS_TTL_SAFETY_MARGIN_SECONDS
    return min(seconds_until_expiration, max(ROOT_KEYS_MIN_TTL_SECONDS, ttl))


def fetch_root_keys_from_google() -> list[Any]:
    response = requests.get(ROOT_KEYS_URL, timeout=ROOT_KEYS_HTTP_TIMEOUT_SECONDS)
    if not response.ok:
        raise GoogleCallbackVerificationError("Failed to fetch Google root keys.")
    payload = response.json()
    return list(payload.get("keys", []))


def verify_intermediate_signing_key(payload: dict[str, Any], root_keys: list[str]) -> str:
    intermediate = payload.get("intermediateSigningKey")
    if not isinstance(intermediate, dict):
        raise GoogleCallbackVerificationError("Missing intermediateSigningKey.")

    signed_key = str(intermediate.get("signedKey", ""))
    signatures = intermediate.get("signatures")
    if not signed_key or not isinstance(signatures, list) or not signatures:
        raise GoogleCallbackVerificationError("Missing signedKey or signatures.")

    signed_string = build_signed_string([SENDER_ID, PROTOCOL_VERSION, signed_key])
    verified = any(
        verify_signature(signed_string, str(signature), root_key)
        for signature in signatures
        for root_key in root_keys
    )
    if not verified:
        raise GoogleCallbackVerificationError("Intermediate signing key signature failed verification.")

    signed_key_data = json.loads(signed_key)
    if not isinstance(signed_key_data, dict):
        raise GoogleCallbackVerificationError("signedKey is not valid JSON.")

    expiration = int(signed_key_data.get("keyExpiration", 0))
    if expiration <= now_millis():
        raise GoogleCallbackVerificationError("Intermediate signing key has expired.")

    key_value = str(signed_key_data.get("keyValue", ""))
    if not key_value:
        raise GoogleCallbackVerificationError("Missing keyValue in intermediate signing key.")
    return key_value


def verify_signed_message(payload: dict[str, Any], intermediate_key: str, issuer_id: str) -> str:
    signature = str(payload.get("signature", ""))
    signed_message = str(payload.get("signedMessage", ""))
    if not signature or not signed_message:
        raise GoogleCallbackVerificationError("Missing signature or signedMessage.")

    signed_string = build_signed_string([SENDER_ID, issuer_id, PROTOCOL_VERSION, signed_message])
    if not verify_signature(signed_string, signature, intermediate_key):
        raise GoogleCallbackVerificationError("Message signature failed verification.")
    return signed_message


def verify_with_keys(payload: dict[str, Any], issuer_id: str, keys: list[Any]) -> dict[str, Any]:
    usable_keys = extract_usable_key_values(keys)
    if not usable_keys:
        raise GoogleCallbackVerificationError("No usable Google root keys available.")

    intermediate_key = verify_intermediate_signing_key(payload, usable_keys)
    signed_message = verify_signed_message(payload, intermediate_key, issuer_id)
    claims = json.loads(signed_message)
    if not isinstance(claims, dict):
        raise GoogleCallbackVerificationError("Signed message is not valid JSON.")
    return claims


def verify_and_decode(payload: dict[str, Any], issuer_id: str) -> dict[str, Any]:
    from django.core.cache import cache

    cached_keys = cache.get(ROOT_KEYS_CACHE_KEY)
    if isinstance(cached_keys, list) and extract_usable_key_values(cached_keys):
        return verify_with_keys(payload, issuer_id, cached_keys)

    fresh_keys = fetch_root_keys_from_google()
    cache.set(ROOT_KEYS_CACHE_KEY, fresh_keys, resolve_cache_ttl_seconds(fresh_keys))
    return verify_with_keys(payload, issuer_id, fresh_keys)

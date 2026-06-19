from __future__ import annotations

import re
from datetime import date, datetime
from uuid import uuid4

from django.core import signing


def headline(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def filter_empty(values: dict) -> dict:
    return {key: value for key, value in values.items() if value not in (None, [], {}, "")}


def isoformat(value: datetime | date | None) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    return datetime.combine(value, datetime.min.time()).isoformat()


def new_suffix() -> str:
    return str(uuid4())


def build_wifi_uri(ssid: str, password: str | None = None, hidden: bool = False) -> str:
    has_password = bool(password)
    parts = [
        f"S:{escape_wifi_value(ssid)}",
        f"T:{'WPA' if has_password else 'nopass'}",
    ]

    if has_password:
        parts.append(f"P:{escape_wifi_value(password or '')}")

    if hidden:
        parts.append("H:true")

    return f"WIFI:{';'.join(parts)};;"


def escape_wifi_value(value: str) -> str:
    return re.sub(r'([\\;,:"])', r"\\\1", value)


def sign_value(value: str) -> str:
    return signing.Signer(salt="django-mobile-pass").sign(value).rsplit(":", 1)[1]


def verify_signed_value(value: str, signature: str) -> bool:
    try:
        signing.Signer(salt="django-mobile-pass").unsign(f"{value}:{signature}")
    except signing.BadSignature:
        return False
    return True

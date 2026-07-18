from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from uuid import uuid4

from django.core import signing

from django_mobile_pass.exceptions import InvalidPass

_ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"  # date + hours + minutes
    r"(?::\d{2}(?:\.\d+)?)?"  # optional seconds / fractional seconds
    r"(?:Z|[+-]\d{2}:?\d{2})?$"  # optional timezone
)


def headline(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def filter_empty(values: dict) -> dict:
    return {key: value for key, value in values.items() if value not in (None, [], {}, "")}


def isoformat(value: datetime | date | None) -> str | None:
    """Return a W3C datetime stamp suitable for Apple Wallet pass.json.

    Apple rejects timestamps that omit a timezone designator (for example
    ``2026-08-01T19:00:00``). Naive datetimes are treated as UTC. Fractional
    seconds are stripped because PassKit examples use whole seconds.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.combine(value, time.min)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    dt = dt.replace(microsecond=0)
    formatted = dt.isoformat()
    if formatted.endswith("+00:00"):
        return f"{formatted[:-6]}Z"
    return formatted


def ensure_w3c_datetime(value: str) -> str:
    """Normalize a datetime string to a W3C stamp with timezone.

    Plain non-datetime strings are returned unchanged so text field values are
    not affected. Values that look like ISO datetimes but cannot be parsed are
    rejected — PassKit fails the entire pass for those. Bare calendar dates
    (``YYYY-MM-DD``) are expanded to midnight UTC.
    """
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        normalized_date = isoformat(date.fromisoformat(value))
        assert normalized_date is not None
        return normalized_date

    if not _ISO_DATETIME_RE.match(value):
        return value

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidPass(
            f"Date value {value!r} must be a W3C datetime "
            f"(e.g. 2026-08-01T19:00:00Z or 2026-08-01T19:00:00-05:00)."
        ) from exc

    normalized = isoformat(parsed)
    if normalized is None:
        raise InvalidPass(f"Date value {value!r} could not be normalized.")
    return normalized


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

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from django_mobile_pass.exceptions import InvalidConfig


@dataclass(slots=True)
class AppleSettings:
    organization_name: str | None = None
    type_identifier: str | None = None
    team_identifier: str | None = None
    certificate: str | None = None
    certificate_path: str | None = None
    certificate_password: str | None = None
    apple_push_base_url: str = "https://api.push.apple.com/3/device"
    webservice_secret: str | None = None
    webservice_host: str | None = None

    def certificate_bytes(self) -> bytes:
        if self.certificate:
            raw = self.certificate.strip()
            if raw.startswith("-----BEGIN"):
                return raw.encode()

            try:
                return base64.b64decode(raw)
            except Exception as exc:
                raise InvalidConfig("MOBILE_PASS.apple.certificate must be base64-encoded PKCS#12 data.") from exc

        if self.certificate_path:
            return Path(self.certificate_path).read_bytes()

        raise InvalidConfig("Set MOBILE_PASS['apple']['certificate'] or MOBILE_PASS['apple']['certificate_path'].")


@dataclass(slots=True)
class GoogleSettings:
    issuer_id: str | None = None
    service_account_key: str | None = None
    service_account_key_path: str | None = None
    origins: list[str] | None = None
    api_base_url: str = "https://walletobjects.googleapis.com/walletobjects/v1"

    def key_info(self) -> dict:
        if self.service_account_key:
            raw = self.service_account_key.strip()
            if raw.startswith("{"):
                return json.loads(raw)
            return json.loads(base64.b64decode(raw))

        if self.service_account_key_path:
            return json.loads(Path(self.service_account_key_path).read_text())

        raise InvalidConfig(
            "Set MOBILE_PASS['google']['service_account_key'] or MOBILE_PASS['google']['service_account_key_path']."
        )

    @property
    def client_email(self) -> str:
        return str(self.key_info()["client_email"])

    @property
    def private_key(self) -> str:
        return str(self.key_info()["private_key"])


@dataclass(slots=True)
class QueueSettings:
    backend: str | None = None
    name: str = "default"


@dataclass(slots=True)
class MobilePassSettings:
    apple: AppleSettings
    google: GoogleSettings
    model: str = "django_mobile_pass.MobilePass"
    apple_device_model: str = "django_mobile_pass.AppleMobilePassDevice"
    apple_registration_model: str = "django_mobile_pass.AppleMobilePassRegistration"
    google_event_model: str = "django_mobile_pass.GoogleMobilePassEvent"
    public_url: str | None = None
    push_updates_on_save: bool = True
    max_request_body_bytes: int = 65536
    queue: QueueSettings | None = None
    actions: dict | None = None
    builders: dict | None = None


def _default_google_origins(config: dict, google: dict) -> list[str]:
    if google.get("origins"):
        return google["origins"]

    public_url = config.get("public_url")
    if public_url:
        return [public_url.rstrip("/")]

    return []


def get_mobile_pass_settings() -> MobilePassSettings:
    config = getattr(settings, "MOBILE_PASS", {})
    apple = config.get("apple", {})
    google = config.get("google", {})
    queue = config.get("queue", {})

    return MobilePassSettings(
        apple=AppleSettings(
            organization_name=apple.get("organization_name"),
            type_identifier=apple.get("type_identifier"),
            team_identifier=apple.get("team_identifier"),
            certificate=apple.get("certificate"),
            certificate_path=apple.get("certificate_path"),
            certificate_password=apple.get("certificate_password"),
            apple_push_base_url=apple.get("apple_push_base_url", "https://api.push.apple.com/3/device"),
            webservice_secret=apple.get("webservice_secret"),
            webservice_host=apple.get("webservice_host"),
        ),
        google=GoogleSettings(
            issuer_id=google.get("issuer_id"),
            service_account_key=google.get("service_account_key"),
            service_account_key_path=google.get("service_account_key_path"),
            origins=_default_google_origins(config, google),
            api_base_url=google.get("api_base_url", "https://walletobjects.googleapis.com/walletobjects/v1"),
        ),
        model=config.get("model", "django_mobile_pass.MobilePass"),
        apple_device_model=config.get("apple_device_model", "django_mobile_pass.AppleMobilePassDevice"),
        apple_registration_model=config.get(
            "apple_registration_model", "django_mobile_pass.AppleMobilePassRegistration"
        ),
        google_event_model=config.get("google_event_model", "django_mobile_pass.GoogleMobilePassEvent"),
        public_url=config.get("public_url"),
        push_updates_on_save=config.get("push_updates_on_save", True),
        max_request_body_bytes=config.get("max_request_body_bytes", 65536),
        queue=QueueSettings(
            backend=queue.get("backend"),
            name=queue.get("name", "default"),
        ),
        actions=config.get("actions", {}),
        builders=config.get("builders", {}),
    )

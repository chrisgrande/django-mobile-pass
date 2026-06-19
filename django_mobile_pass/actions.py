from __future__ import annotations

import tempfile

from django.utils import timezone

from django_mobile_pass.enums import Platform
from django_mobile_pass.exceptions import AppleWalletRequestFailed
from django_mobile_pass.google.client import GoogleWalletClient
from django_mobile_pass.models import (
    AppleMobilePassDevice,
    AppleMobilePassRegistration,
    GoogleMobilePassEvent,
    MobilePass,
)
from django_mobile_pass.registry import get_action_class, get_model_class
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.signals import mobile_pass_added, mobile_pass_removed


def mobile_pass_model():
    return get_model_class("model", "django_mobile_pass.MobilePass", MobilePass)


def apple_device_model():
    return get_model_class("apple_device_model", "django_mobile_pass.AppleMobilePassDevice", AppleMobilePassDevice)


def apple_registration_model():
    return get_model_class(
        "apple_registration_model",
        "django_mobile_pass.AppleMobilePassRegistration",
        AppleMobilePassRegistration,
    )


def google_event_model():
    return get_model_class("google_event_model", "django_mobile_pass.GoogleMobilePassEvent", GoogleMobilePassEvent)


class RegisterDeviceAction:
    def execute(self, device_id: str, push_token: str, pass_type_id: str, pass_serial: str):
        mobile_pass = mobile_pass_model().objects.get(pk=pass_serial)
        if mobile_pass.platform != Platform.APPLE:
            raise mobile_pass_model().DoesNotExist()

        expected_pass_type = mobile_pass.content.get("passTypeIdentifier")
        if expected_pass_type and expected_pass_type != pass_type_id:
            raise mobile_pass_model().DoesNotExist()

        device, _ = apple_device_model().objects.update_or_create(
            id=device_id,
            defaults={"push_token": push_token},
        )
        registration, created = apple_registration_model().objects.get_or_create(
            device=device,
            pass_type_id=pass_type_id,
            mobile_pass=mobile_pass,
        )
        registration.was_recently_created = created
        if created:
            mobile_pass_added.send(sender=mobile_pass.__class__, mobile_pass=mobile_pass)
        return registration


class UnregisterDeviceAction:
    def execute(self, device_id: str, pass_serial: str) -> None:
        registrations = apple_registration_model().objects.select_related("mobile_pass").filter(
            device_id=device_id,
            mobile_pass_id=pass_serial,
        )
        for registration in registrations:
            mobile_pass = registration.mobile_pass
            registration.delete()
            mobile_pass_removed.send(sender=mobile_pass.__class__, mobile_pass=mobile_pass)


class NotifyAppleOfPassUpdateAction:
    def execute(self, mobile_pass) -> None:
        for registration in mobile_pass.apple_registrations.select_related("device", "mobile_pass"):
            self.notify_update(registration)

    def notify_update(self, registration) -> None:
        import requests

        cert_file = self._certificate_file()
        try:
            response = requests.post(
                registration.apple_update_url(),
                headers={"apns-topic": registration.pass_type_id},
                json={},
                cert=cert_file.name,
                timeout=30,
            )
        finally:
            cert_file.close()

        if response.status_code == 410:
            registration.delete()
            return

        if not response.ok:
            payload = {}
            try:
                payload = response.json()
            except ValueError:
                pass
            raise AppleWalletRequestFailed(
                f"Apple Wallet update request failed for {registration.apple_update_url()}",
                status=response.status_code,
                payload=payload,
            )

    def _certificate_file(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import pkcs12

        apple = get_mobile_pass_settings().apple
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            apple.certificate_bytes(),
            apple.certificate_password.encode() if apple.certificate_password else None,
        )
        if private_key is None or certificate is None:
            raise AppleWalletRequestFailed("Apple certificate must include a private key and certificate.")

        handle = tempfile.NamedTemporaryFile("wb", suffix=".pem")
        handle.write(
            certificate.public_bytes(serialization.Encoding.PEM)
            + private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        handle.flush()
        return handle


class HandleGoogleCallbackAction:
    def execute(self, claims: dict) -> None:
        object_id = claims.get("objectId")
        if object_id is None:
            return

        event_type = {"save": "save", "del": "remove"}.get(claims.get("eventType"))
        if event_type is None:
            return

        mobile_pass = (
            mobile_pass_model()
            .objects.filter(content__googleObjectId=str(object_id))
            .first()
        )
        if mobile_pass is None:
            return

        google_event_model().objects.create(
            mobile_pass=mobile_pass,
            event_type=event_type,
            received_at=timezone.now(),
            raw_payload=claims,
        )
        signal = mobile_pass_added if event_type == "save" else mobile_pass_removed
        signal.send(sender=mobile_pass.__class__, mobile_pass=mobile_pass)


class NotifyGoogleOfPassUpdateAction:
    def __init__(self, client: GoogleWalletClient | None = None):
        self.client = client or GoogleWalletClient()

    def execute(self, mobile_pass) -> None:
        google_class_type = mobile_pass.content.get("googleClassType")
        object_id = mobile_pass.content.get("googleObjectId")
        if not google_class_type or not object_id:
            return
        resource = google_class_type.replace("Class", "Object")
        self.client.patch_object(resource, object_id, mobile_pass.content.get("googleObjectPayload", {}))


def notify_pass_update(mobile_pass) -> None:
    from django_mobile_pass.tasks import dispatch_pass_update

    dispatch_pass_update(mobile_pass)

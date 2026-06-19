from __future__ import annotations

from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.db import models

from django_mobile_pass.enums import PassType, Platform
from django_mobile_pass.exceptions import CannotDownload, PlatformDoesntSupport
from django_mobile_pass.google.auth import GoogleJwtSigner
from django_mobile_pass.registry import get_builder_class
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.utils import sign_value


class MobilePassQuerySet(models.QuerySet):
    def apple(self):
        return self.filter(platform=Platform.APPLE)

    def google(self):
        return self.filter(platform=Platform.GOOGLE)


class MobilePass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    type = models.CharField(max_length=32, choices=[(choice.value, choice.value) for choice in PassType])
    platform = models.CharField(max_length=16, choices=[(choice.value, choice.value) for choice in Platform])
    builder_name = models.CharField(max_length=64)
    content = models.JSONField(default=dict)
    images = models.JSONField(default=dict)
    download_name = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = MobilePassQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.platform}:{self.builder_name}:{self.pk}"

    @property
    def is_apple(self) -> bool:
        return self.platform == Platform.APPLE

    @property
    def is_google(self) -> bool:
        return self.platform == Platform.GOOGLE

    def expire(self) -> "MobilePass":
        if self.is_apple:
            content = dict(self.content)
            content["voided"] = True
            content["expirationDate"] = timezone.now().isoformat()
        else:
            content = dict(self.content)
            object_payload = dict(content.get("googleObjectPayload", {}))
            object_payload["state"] = "EXPIRED"
            content["googleObjectPayload"] = object_payload

        self.content = content
        self.expired_at = timezone.now()
        self.save(update_fields=["content", "expired_at", "updated_at"])
        return self

    def registrations(self):
        return self.apple_registrations.all()

    def devices(self):
        return AppleMobilePassDevice.objects.filter(registrations__mobile_pass=self).distinct()

    def is_currently_saved_to_google_wallet(self) -> bool:
        latest = self.google_events.order_by("-received_at").first()
        return latest is not None and latest.event_type == "save"

    def is_currently_in_wallet(self) -> bool:
        if self.is_apple:
            return self.apple_registrations.exists()
        return self.is_currently_saved_to_google_wallet()

    def builder(self):
        if not self.is_apple:
            raise PlatformDoesntSupport("Only Apple passes can be hydrated back into updateable builders.")

        builder_class = get_builder_class(self.builder_name, self.platform)
        return builder_class.hydrate(self)

    def update_field(self, key: str, value: str, change_message: str | None = None, label: str | None = None) -> "MobilePass":
        if not self.is_apple:
            raise PlatformDoesntSupport("Only Apple passes support update_field().")
        self.builder().update_field(key, value, change_message=change_message, label=label).save()
        self.refresh_from_db()
        return self

    def generate(self) -> bytes:
        if not self.is_apple:
            raise PlatformDoesntSupport("Only Apple passes generate .pkpass archives.")
        return self.builder().generate()

    def add_to_wallet_url(self, request=None) -> str:
        if self.is_apple:
            return self.apple_add_to_wallet_url(request=request)
        return self.google_add_to_wallet_url()

    def apple_add_to_wallet_url(self, request=None) -> str:
        if not self.is_apple:
            raise PlatformDoesntSupport("Only Apple passes can produce an Apple Wallet download URL.")

        try:
            path = reverse("django_mobile_pass:apple-download", kwargs={"mobile_pass_id": self.pk})
        except NoReverseMatch:
            path = reverse("apple-download", kwargs={"mobile_pass_id": self.pk})
        separator = "&" if "?" in path else "?"
        path = f"{path}{separator}signature={sign_value(str(self.pk))}"

        if request is not None:
            return request.build_absolute_uri(path)

        public_url = get_mobile_pass_settings().public_url
        if public_url:
            return f"{public_url.rstrip('/')}{path}"

        return path

    def google_add_to_wallet_url(self) -> str:
        if not self.is_google:
            raise PlatformDoesntSupport("Only Google passes can produce a Google Wallet save URL.")
        object_resource = self.content["googleClassType"].replace("Class", "Object")
        jwt_token = GoogleJwtSigner().sign_save_url_jwt(
            {f"{object_resource}s": [{"id": self.content["googleObjectId"]}]}
        )
        return f"https://pay.google.com/gp/v/save/{jwt_token}"

    def download_response(self, name: str | None = None) -> HttpResponse:
        if not self.is_apple:
            raise CannotDownload("Only Apple passes can be downloaded as .pkpass archives.")
        filename = (name or self.download_name or "pass").removesuffix(".pkpass")
        response = HttpResponse(self.generate(), content_type="application/vnd.apple.pkpass")
        response["Content-Disposition"] = f'inline; filename="{filename}.pkpass"'
        return response

    def download(self) -> bytes:
        if not self.is_apple:
            raise CannotDownload("Only Apple passes can be downloaded as .pkpass archives.")
        return self.generate()

    def email_attachment(self, name: str | None = None) -> tuple[str, bytes, str]:
        filename = (name or self.download_name or "pass").removesuffix(".pkpass")
        return (f"{filename}.pkpass", self.download(), "application/vnd.apple.pkpass")

    def was_updated_after(self, since=None) -> bool:
        if since is None:
            return True
        return self.updated_at > since

    def to_response(self):
        if self.is_apple:
            return self.download_response()
        return redirect(self.google_add_to_wallet_url())

    def attach_to(self, instance: models.Model) -> "MobilePass":
        self.content_object = instance
        self.save(update_fields=["content_type", "object_id", "updated_at"])
        return self


class AppleMobilePassDevice(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    push_token = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "apple_mobile_pass_devices"

    def __str__(self) -> str:
        return self.id


class AppleMobilePassRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    device = models.ForeignKey(AppleMobilePassDevice, related_name="registrations", on_delete=models.CASCADE)
    pass_type_id = models.CharField(max_length=255)
    mobile_pass = models.ForeignKey(
        MobilePass,
        db_column="pass_serial",
        related_name="apple_registrations",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "apple_mobile_pass_registrations"
        indexes = [
            models.Index(fields=["device", "mobile_pass"]),
            models.Index(fields=["device", "pass_type_id"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["device", "pass_type_id", "mobile_pass"], name="uniq_apple_pass_registration")
        ]

    @property
    def pass_serial(self):
        return self.mobile_pass_id

    def apple_update_url(self) -> str:
        base_url = get_mobile_pass_settings().apple.apple_push_base_url
        return f"{base_url.rstrip('/')}/{self.device.push_token}"


class GoogleMobilePassEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    mobile_pass = models.ForeignKey(MobilePass, related_name="google_events", on_delete=models.CASCADE)
    event_type = models.CharField(max_length=32)
    received_at = models.DateTimeField()
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mobile_pass_google_events"
        indexes = [
            models.Index(fields=["mobile_pass", "event_type"]),
            models.Index(fields=["received_at"]),
        ]

    @classmethod
    def saves(cls):
        return cls.objects.filter(event_type="save")

    @classmethod
    def removes(cls):
        return cls.objects.filter(event_type="remove")

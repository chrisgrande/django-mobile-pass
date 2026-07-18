from __future__ import annotations

import hmac
from datetime import timezone as dt_timezone
from email.utils import parsedate_to_datetime

from django.core.exceptions import ValidationError
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseNotModified,
    JsonResponse,
)
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import http_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from django_mobile_pass.actions import (
    HandleGoogleCallbackAction,
    RegisterDeviceAction,
    UnregisterDeviceAction,
    apple_registration_model,
    mobile_pass_model,
)
from django_mobile_pass.enums import Platform
from django_mobile_pass.google.callback_verification import (
    GoogleCallbackVerificationError,
    PROTOCOL_VERSION,
    verify_and_decode,
)
from django_mobile_pass.models import MobilePass
from django_mobile_pass.registry import get_action_class
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.signals import apple_mobile_pass_logs_received
from django_mobile_pass.utils import verify_signed_value


def _json_body(request) -> dict:
    import json

    if _body_too_large(request):
        return {}

    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode(request.encoding or "utf-8"))
    except ValueError:
        return {}


def _apple_authorized(request) -> bool:
    secret = get_mobile_pass_settings().apple.webservice_secret
    if not secret:
        return False

    expected = f"ApplePass {secret}"
    provided = request.headers.get("Authorization", "")
    return hmac.compare_digest(provided, expected)


def _require_apple_auth(request):
    if not _apple_authorized(request):
        return HttpResponseForbidden("Invalid PassKit authorization header.")
    return None


def _body_too_large(request) -> bool:
    content_length = request.META.get("CONTENT_LENGTH")
    if content_length:
        try:
            return int(content_length) > get_mobile_pass_settings().max_request_body_bytes
        except ValueError:
            return True
    return False


def _request_entity_too_large() -> HttpResponse:
    return HttpResponse("Request body too large.", status=413)


def _valid_path_value(value: str, max_length: int = 255) -> bool:
    return 0 < len(value) <= max_length


def _stored_pass_matches_type(mobile_pass: MobilePass, pass_type_id: str) -> bool:
    if mobile_pass.platform != Platform.APPLE:
        return False
    expected = mobile_pass.content.get("passTypeIdentifier")
    return expected is None or expected == pass_type_id


def _find_pass_by_serial(pass_serial) -> MobilePass:
    """Resolve a PassKit serial to a stored pass.

    Apple Wallet uses the serialNumber embedded in pass.json when it calls the
    web service, so match that first and fall back to the primary key.
    """
    model_class = mobile_pass_model()
    serial = str(pass_serial)

    mobile_pass = model_class.objects.filter(content__serialNumber=serial).first()
    if mobile_pass is not None:
        return mobile_pass

    try:
        return model_class.objects.get(pk=serial)
    except (model_class.DoesNotExist, ValueError, ValidationError):
        raise model_class.DoesNotExist()


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def device_registration(request, device_id: str, pass_type_id: str, pass_serial):
    if request.method == "DELETE":
        return unregister_device(request, device_id, pass_type_id, pass_serial)
    return register_device(request, device_id, pass_type_id, pass_serial)


def register_device(request, device_id: str, pass_type_id: str, pass_serial):
    forbidden = _require_apple_auth(request)
    if forbidden:
        return forbidden

    if _body_too_large(request):
        return _request_entity_too_large()

    body = _json_body(request)
    push_token = str(body.get("pushToken", ""))
    if (
        not _valid_path_value(device_id)
        or not _valid_path_value(pass_type_id)
        or not _valid_path_value(str(pass_serial))
        or not push_token
        or len(push_token) > 512
    ):
        return HttpResponseBadRequest("Invalid PassKit registration payload.")

    try:
        mobile_pass = _find_pass_by_serial(pass_serial)
    except MobilePass.DoesNotExist:
        return HttpResponseNotFound()

    action_class = get_action_class(
        "register_device",
        "django_mobile_pass.actions.RegisterDeviceAction",
        base_class=RegisterDeviceAction,
    )
    try:
        registration = action_class().execute(
            device_id=device_id,
            push_token=push_token,
            pass_type_id=pass_type_id,
            pass_serial=str(mobile_pass.pk),
        )
    except MobilePass.DoesNotExist:
        return HttpResponseNotFound()

    return HttpResponse(status=201 if getattr(registration, "was_recently_created", False) else 200)


@csrf_exempt
def unregister_device(request, device_id: str, pass_type_id: str, pass_serial):
    forbidden = _require_apple_auth(request)
    if forbidden:
        return forbidden

    if not _valid_path_value(device_id) or not _valid_path_value(pass_type_id) or not _valid_path_value(str(pass_serial)):
        return HttpResponseBadRequest("Invalid PassKit registration path.")

    try:
        mobile_pass = _find_pass_by_serial(pass_serial)
    except MobilePass.DoesNotExist:
        return HttpResponseNotFound()
    if not _stored_pass_matches_type(mobile_pass, pass_type_id):
        return HttpResponseNotFound()

    action_class = get_action_class(
        "unregister_device",
        "django_mobile_pass.actions.UnregisterDeviceAction",
        base_class=UnregisterDeviceAction,
    )
    action_class().execute(device_id=device_id, pass_serial=str(mobile_pass.pk))
    return HttpResponse(status=204)


@require_http_methods(["GET"])
def check_for_updates(request, pass_type_id: str, pass_serial):
    forbidden = _require_apple_auth(request)
    if forbidden:
        return forbidden

    try:
        mobile_pass = _find_pass_by_serial(pass_serial)
    except MobilePass.DoesNotExist:
        return HttpResponseNotFound()
    if not _stored_pass_matches_type(mobile_pass, pass_type_id):
        return HttpResponseNotFound()

    if_modified_since = request.headers.get("If-Modified-Since")
    try:
        since = parsedate_to_datetime(if_modified_since) if if_modified_since else None
    except (TypeError, ValueError, IndexError, OverflowError):
        since = None
    updated_at = mobile_pass.updated_at

    if since is not None:
        if timezone.is_naive(since):
            since = since.replace(tzinfo=dt_timezone.utc)
        if timezone.is_naive(updated_at):
            since = timezone.make_naive(since, dt_timezone.utc)
        # Last-Modified has second precision, so drop microseconds before comparing.
        if updated_at.replace(microsecond=0) <= since:
            return HttpResponseNotModified()

    response = HttpResponse(mobile_pass.generate(), content_type="application/vnd.apple.pkpass")
    response["Last-Modified"] = http_date(updated_at.timestamp())
    return response


@require_http_methods(["GET"])
def associated_serials(request, device_id: str, pass_type_id: str):
    if not _valid_path_value(device_id) or not _valid_path_value(pass_type_id):
        return HttpResponseBadRequest("Invalid PassKit registration path.")

    updated_since = request.GET.get("passesUpdatedSince")
    updated_since_dt = parse_datetime(updated_since) if updated_since else None

    queryset = apple_registration_model().objects.select_related("mobile_pass").filter(
        device_id=device_id,
        pass_type_id=pass_type_id,
    )
    if updated_since_dt:
        queryset = queryset.filter(mobile_pass__updated_at__gt=updated_since_dt)

    registrations = list(queryset)
    if not registrations:
        return HttpResponse(status=204)

    latest = max(registration.mobile_pass.updated_at for registration in registrations)
    last_updated = latest.astimezone(dt_timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return JsonResponse(
        {
            "lastUpdated": last_updated,
            # Devices fetch passes by the serialNumber inside pass.json, so
            # return that value (falling back to the primary key).
            "serialNumbers": [
                (registration.mobile_pass.content or {}).get("serialNumber") or str(registration.mobile_pass_id)
                for registration in registrations
            ],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def mobile_pass_logs(request):
    if _body_too_large(request):
        return _request_entity_too_large()

    logs = _json_body(request).get("logs")
    apple_mobile_pass_logs_received.send(sender=None, logs=logs)
    return HttpResponse(status=204)


@require_http_methods(["GET"])
def download_apple_pass(request, mobile_pass_id):
    signature = request.GET.get("signature", "")
    if not verify_signed_value(str(mobile_pass_id), signature):
        return HttpResponseForbidden("Invalid download signature.")
    model_class = mobile_pass_model()
    try:
        mobile_pass = model_class.objects.get(pk=mobile_pass_id)
    except model_class.DoesNotExist:
        return HttpResponseNotFound()
    return mobile_pass.download_response()


@csrf_exempt
@require_http_methods(["POST"])
def google_callback(request):
    if _body_too_large(request):
        return _request_entity_too_large()

    payload = _json_body(request)
    if not payload:
        return HttpResponseBadRequest("Invalid Google callback payload.")

    if payload.get("protocolVersion") != PROTOCOL_VERSION:
        return HttpResponseForbidden("Unsupported Google callback protocol version.")

    issuer_id = get_mobile_pass_settings().google.issuer_id
    if not issuer_id:
        return HttpResponseForbidden("No Google issuer id configured.")

    try:
        claims = verify_and_decode(payload, issuer_id)
    except GoogleCallbackVerificationError:
        return HttpResponseForbidden("Invalid Google callback signature.")

    action_class = get_action_class(
        "handle_google_callback",
        "django_mobile_pass.actions.HandleGoogleCallbackAction",
        base_class=HandleGoogleCallbackAction,
    )
    action_class().execute(claims)
    return HttpResponse(status=204)

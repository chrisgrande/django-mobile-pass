---
title: Configuration reference
weight: 4
---

# Configuration reference

All package behavior is driven by the `MOBILE_PASS` dictionary in Django settings.

```python
MOBILE_PASS = {
    "public_url": "https://example.com",
    "push_updates_on_save": True,
    "max_request_body_bytes": 65536,
    "model": "django_mobile_pass.MobilePass",
    "apple_device_model": "django_mobile_pass.AppleMobilePassDevice",
    "apple_registration_model": "django_mobile_pass.AppleMobilePassRegistration",
    "google_event_model": "django_mobile_pass.GoogleMobilePassEvent",
    "actions": {},
    "builders": {},
    "apple": { ... },
    "google": { ... },
}
```

## Top-level options

| Key | Default | Purpose |
|-----|---------|---------|
| `public_url` | `None` | Public site URL used when building signed Apple download links outside a request context. |
| `push_updates_on_save` | `True` | When `False`, saving an existing `MobilePass` does not notify Apple or Google. |
| `queue` | `{}` | Optional async update delivery. See [Queue-backed updates](#queue-backed-updates). |
| `max_request_body_bytes` | `65536` | Maximum PassKit log, callback, and registration body size. |
| `model` | `django_mobile_pass.MobilePass` | Dotted app label and model name for stored passes. |
| `apple_device_model` | `django_mobile_pass.AppleMobilePassDevice` | Model for registered Apple devices. |
| `apple_registration_model` | `django_mobile_pass.AppleMobilePassRegistration` | Model for device/pass registrations. |
| `google_event_model` | `django_mobile_pass.GoogleMobilePassEvent` | Model for Google save/remove callback events. |
| `actions` | `{}` | Override built-in action classes. See [Customizing actions](advanced-usage/customizing-actions.md). |
| `builders` | `{}` | Register custom pass builders by platform and snake_case name. |

## Apple settings

| Key | Required | Purpose |
|-----|----------|---------|
| `organization_name` | For production passes | Organization name embedded in each pass. |
| `type_identifier` | Yes | Apple Pass Type ID. Must match the signing certificate. |
| `team_identifier` | Yes | Apple Developer Team ID. |
| `certificate_path` | One of certificate options | Path to the PKCS#12 `.p12` signing bundle. |
| `certificate` | One of certificate options | Inline base64 PKCS#12 bytes. |
| `certificate_password` | If the `.p12` is encrypted | Password for the PKCS#12 bundle. |
| `webservice_secret` | Yes for PassKit routes | Long random token. Wallet sends `Authorization: ApplePass <secret>`. |
| `webservice_host` | Recommended | Public HTTPS host for PassKit web service calls. Falls back to Django `APP_URL` when omitted. |
| `apple_push_base_url` | Has default | APNs device endpoint used for update notifications. |

Certificates can be supplied either as a file path or inline base64 content. Exactly one certificate source must be configured before generating Apple passes.

## Google settings

| Key | Required | Purpose |
|-----|----------|---------|
| `issuer_id` | Yes | Google Wallet issuer ID. Also required for ECv2 callback verification. |
| `service_account_key_path` | One of key options | Path to the Google service account JSON file. |
| `service_account_key` | One of key options | Inline raw or base64-encoded service account JSON. |
| `origins` | Yes for Save to Wallet links | Allowed web origins in Save to Wallet JWTs. Defaults to `[public_url]` when omitted. |
| `api_base_url` | Has default | Google Wallet Objects API base URL. |

Service account credentials can be supplied either as a file path or inline JSON. Exactly one key source must be configured before creating Google classes or objects.

## Custom actions

Override any built-in action by dotted import path:

```python
MOBILE_PASS = {
    "actions": {
        "register_device": "myapp.wallet_actions.AuditRegisterDeviceAction",
        "unregister_device": "django_mobile_pass.actions.UnregisterDeviceAction",
        "notify_apple_of_pass_update": "django_mobile_pass.actions.NotifyAppleOfPassUpdateAction",
        "notify_google_of_pass_update": "django_mobile_pass.actions.NotifyGoogleOfPassUpdateAction",
        "handle_google_callback": "django_mobile_pass.actions.HandleGoogleCallbackAction",
    },
}
```

## Custom builders

Register additional builders under the platform key:

```python
MOBILE_PASS = {
    "builders": {
        "apple": {
            "vip_event_ticket": "myapp.builders.VipEventTicketPassBuilder",
        },
        "google": {
            "vip_event_ticket": "myapp.builders.VipEventTicketPassBuilder",
        },
    },
}
```

Built-in builders are registered automatically. Only add entries for builders you have authored yourself.

Built-in registry keys:

| Platform | Names |
|----------|-------|
| Apple | `airline`, `boarding`, `coupon`, `event_ticket`, `generic`, `store_card` |
| Google | `boarding`, `event_ticket`, `generic`, `loyalty`, `offer` |

## Queue-backed updates

When an existing `MobilePass` is saved and `push_updates_on_save` is `True`, the package notifies Apple (APNs) and/or patches Google objects. By default this runs **synchronously** in the `post_save` signal.

For async update delivery, configure a queue backend:

```python
MOBILE_PASS = {
    "queue": {
        "backend": "celery",  # omit or null for synchronous delivery
        "name": "default",    # Celery queue name when backend is "celery"
    },
}
```

| `queue.backend` | Behavior |
|-----------------|----------|
| omitted / `None` | Run update actions synchronously |
| `"celery"` | Dispatch `django_mobile_pass.push_pass_update` via Celery |
| dotted import path | Call `your.callable(mobile_pass_id, action_name)` |

Register a Celery task in your project:

```python
from celery import shared_task
from django_mobile_pass.tasks import CELERY_TASK_NAME, push_pass_update_task

@shared_task(name=CELERY_TASK_NAME)
def celery_push_pass_update(mobile_pass_id, action_name):
    push_pass_update_task(mobile_pass_id, action_name)
```

Custom action and builder overrides are validated at import time — subclasses must extend the package default classes.

## Cache

Google callback verification caches root keys from `https://pay.google.com/gp/m/issuer/keys`. Configure Django's default cache backend in production so key fetches are not repeated on every callback.

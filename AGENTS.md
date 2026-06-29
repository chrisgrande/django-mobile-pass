# Agent guide: django-mobile-pass

This repository ships **django-mobile-pass** — a Django 5.2+ package for **Apple Wallet** (PassKit / `.pkpass`) and **Google Wallet** (Wallet Objects API).

Use this file when an agent needs to integrate, extend, or debug wallet passes inside a Django application. For longer integration walkthroughs, see [`docs/agent-integration.md`](docs/agent-integration.md).

## What the two wallet systems are

| Platform | User-facing result | Backend mechanism |
|----------|-------------------|-------------------|
| **Apple Wallet** | `.pkpass` file or PassKit download URL | Signed ZIP (`pass.json` + images + manifest + PKCS#7 signature); PassKit web service for device registration and updates; APNs wake-up notifications |
| **Google Wallet** | “Save to Google Wallet” link | Class (template) + object (instance) via REST API; Save-to-Wallet JWT; ECv2-signed save/remove callbacks |

Both platforms share the `MobilePass` Django model, pass builders, update notifications, and optional attachment to domain models via `HasMobilePasses`.

## Quick integration checklist

1. **Install** — `pip install -e .` (or add to project dependencies).
2. **Enable app** — add `"django.contrib.contenttypes"` and `"django_mobile_pass"` to `INSTALLED_APPS`.
3. **Migrate** — `python manage.py migrate`.
4. **Configure** — set `MOBILE_PASS` in Django settings (see [`docs/configuration.md`](docs/configuration.md)).
5. **Mount routes** — `path("", include("django_mobile_pass.urls"))`.
6. **Expose publicly** — Apple PassKit and Google callbacks require HTTPS endpoints reachable from Apple/Google.

### Minimal settings

```python
MOBILE_PASS = {
    "public_url": "https://example.com",
    "push_updates_on_save": True,
    "apple": {
        "organization_name": "Example Inc",
        "type_identifier": "pass.com.example.tickets",
        "team_identifier": "ABCDE12345",
        "certificate_path": "/path/to/pass.p12",  # or inline base64 via "certificate"
        "certificate_password": "secret",
        "webservice_secret": "long-random-string-min-16-chars",
        "webservice_host": "https://example.com",
    },
    "google": {
        "issuer_id": "3388000000022791700",
        "service_account_key_path": "/path/to/service-account.json",  # or inline via "service_account_key"
        "origins": ["https://example.com"],  # defaults to public_url when omitted
    },
}
```

## Core modules (where to look)

| Task | Module / path |
|------|----------------|
| Issue an Apple pass | `django_mobile_pass.apple.builders.*` |
| Issue a Google pass | `django_mobile_pass.google.builders.*` |
| Stored pass model | `django_mobile_pass.models.MobilePass` |
| PassKit HTTP routes | `django_mobile_pass.views` + `django_mobile_pass.urls` |
| Device registration / APNs / Google PATCH | `django_mobile_pass.actions` |
| Async update dispatch | `django_mobile_pass.tasks.dispatch_pass_update` |
| Builder / action / model resolution | `django_mobile_pass.registry` |
| Payload validation | `django_mobile_pass.validation` |
| Settings wrapper | `django_mobile_pass.settings.get_mobile_pass_settings()` |
| Inspect `.pkpass` archives | `django_mobile_pass.apple.reader.PkPassReader` |
| Enums (`Platform`, `PassType`, `BarcodeType`, …) | `django_mobile_pass.enums` |
| Typed exceptions | `django_mobile_pass.exceptions` |

## Issuing passes

### Apple event ticket

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_organization_name("Example Inc")
    .set_serial_number("TICKET-0042")
    .set_description("Concert ticket")
    .add_field("event", "Main Stage")
    .add_field("seat", "A12")
    .set_remote_logo_image("https://cdn.example.com/logo.png")
    .save()
)

# In a view:
return mobile_pass.download_response()
# Or hand out a link:
url = mobile_pass.add_to_wallet_url(request)
```

### Google loyalty card

```python
from django_mobile_pass.google.builders import LoyaltyPassClass, LoyaltyPassBuilder

LoyaltyPassClass.make("rewards-v1").set_program_name("Rewards").save()

mobile_pass = (
    LoyaltyPassBuilder.make()
    .set_class("rewards-v1")
    .set_account_id("user-123")
    .save()
)

# Redirect user to Google Wallet:
return mobile_pass.to_response(request)  # or mobile_pass.add_to_wallet_url()
```

## Built-in pass builders

| Platform | Registry keys |
|----------|---------------|
| Apple | `airline`, `boarding`, `coupon`, `event_ticket`, `generic`, `store_card` |
| Google | `boarding`, `event_ticket`, `generic`, `loyalty`, `offer` |

Resolve custom builders via `MOBILE_PASS["builders"]`. Overrides must subclass `ApplePassBuilder` or `GooglePassBuilder`.

## `MobilePass` model API

| Method / property | Platform | Purpose |
|-------------------|----------|---------|
| `download_response()` / `download()` | Apple | Return `.pkpass` bytes or HTTP response |
| `add_to_wallet_url(request=None)` | Both | Signed Apple URL or Google Save-to-Wallet URL |
| `to_response()` | Both | Apple download response or Google redirect |
| `email_attachment()` | Apple | `(filename, bytes, mime)` tuple for email |
| `builder()` | Apple | Rehydrate stored pass into an updateable builder |
| `update_field(key, value, change_message=…)` | Apple | Update one field and save (use `:value` placeholder in change messages) |
| `expire()` | Both | Mark pass void/expired in wallet content |
| `is_currently_in_wallet()` | Both | Apple registrations exist, or latest Google callback was `save` |
| `is_currently_saved_to_google_wallet()` | Google | Latest Google callback event was `save` |
| `attach_to(instance)` | Both | Link pass to a domain model via generic foreign key |
| `generate()` | Apple | Raw signed `.pkpass` bytes |
| `registrations()` / `devices()` | Apple | Related PassKit registration rows |

Query scopes on `MobilePass.objects`:

```python
MobilePass.objects.apple()
MobilePass.objects.google()
```

## HTTP routes (mount under site root)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST/DELETE | `/passkit/v1/devices/{device_id}/registrations/{pass_type_id}/{pass_serial}` | `ApplePass` | Apple register/unregister |
| GET | `/passkit/v1/passes/{pass_type_id}/{pass_serial}` | `ApplePass` | Apple update check + download |
| GET | `/passkit/v1/devices/{device_id}/registrations/{pass_type_id}` | `ApplePass` | Apple associated serials |
| POST | `/passkit/v1/log` | None | Apple Wallet client logs |
| GET | `/passkit/v1/apple/{mobile_pass_id}/download?signature=…` | HMAC signature | Signed `.pkpass` download |
| POST | `/passkit/v1/google/callbacks` | ECv2 | Google save/remove callbacks |

`pass_serial` in PassKit routes is the `MobilePass` UUID primary key.

## Updating passes after issue

- **Apple** — hydrate builder from stored pass, change fields, `save()`; or `mobile_pass.update_field(key, value, change_message="Gate changed to :value")`.
- **Google** — update `content["googleObjectPayload"]` on the `MobilePass` and `save()`; the package PATCHes the Google object.
- **Notifications** — when `push_updates_on_save` is `True`, saving an existing pass dispatches Apple APNs and/or Google PATCH.

### Queue-backed updates (optional)

For async update delivery:

```python
MOBILE_PASS = {
    "queue": {
        "backend": "celery",  # or a dotted path to a callable(mobile_pass_id, action_name)
        "name": "default",
    },
}
```

Register a Celery task in your project:

```python
from celery import shared_task
from django_mobile_pass.tasks import CELERY_TASK_NAME, push_pass_update_task

@shared_task(name=CELERY_TASK_NAME)
def celery_push_pass_update(mobile_pass_id, action_name):
    push_pass_update_task(mobile_pass_id, action_name)
```

When `queue.backend` is omitted, updates run synchronously on `post_save`.

## Attaching passes to domain models

```python
from django_mobile_pass.mixins import HasMobilePasses

class Order(models.Model, HasMobilePasses):
    ...
```

```python
order.add_mobile_pass(mobile_pass)  # or builder .save() with content_object=order
order.apple_passes()
order.google_passes()
order.first_apple_pass()
order.first_google_pass()
```

Use `order.apple_passes()` / `order.google_passes()` on model instances. The generic relation manager does not expose queryset helpers like `.apple()` directly.

## Customization hooks

| Config key | Validates against |
|------------|-------------------|
| `model`, `apple_device_model`, `apple_registration_model`, `google_event_model` | respective default model class |
| `actions.*` | respective default action class |
| `builders.apple.*` / `builders.google.*` | `ApplePassBuilder` / `GooglePassBuilder` |

Built-in action keys: `register_device`, `unregister_device`, `notify_apple_of_pass_update`, `notify_google_of_pass_update`, `handle_google_callback`.

## Signals

- `mobile_pass_added` — Apple device registered or Google save callback
- `mobile_pass_removed` — Apple unregister or Google remove callback
- `apple_mobile_pass_logs_received` — Apple Wallet posted logs

## Validation

Per-type validators in `django_mobile_pass.validation` validate pass payloads before save/API insert. Builders call `validator_class().validate(payload)` automatically. Validation failures raise `InvalidPass`.

## Inspecting `.pkpass` archives

```python
from django_mobile_pass.apple.reader import PkPassReader

archive = mobile_pass.generate()
reader = PkPassReader.from_bytes(archive)
pass_json = reader.pass_properties()
```

## Exceptions

| Exception | Typical cause |
|-----------|---------------|
| `InvalidPass` | Builder payload validation failed |
| `InvalidConfig` | Missing or malformed `MOBILE_PASS` settings |
| `InvalidCertificate` | Apple PKCS#12 cannot be read or signed |
| `ImageNotFound` | Local Apple image path missing |
| `CannotDownload` / `PlatformDoesntSupport` | Platform-specific helper used on wrong pass type |
| `AppleWalletRequestFailed` / `GoogleWalletRequestFailed` | Outbound APNs or Google API error |

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Use `tests/` for PassKit routes, signing, ECv2 verification, and builder behavior.

## Project layout

- **Package code:** `django_mobile_pass/`
- **Documentation:** `docs/`
- **Tests:** `tests/`
- **Feature matrix:** [`docs/feature-matrix.md`](docs/feature-matrix.md)

## Common pitfalls

1. **Google images** must be public HTTPS URLs (not local paths).
2. **Apple `webservice_host`** must be `https://` for production PassKit.
3. **Google `origins`** must include your site origin for Save-to-Wallet JWTs (defaults from `public_url` when not set).
4. **Certificate / service account secrets** belong in environment or secret stores, never committed.
5. **Pass serial in PassKit** is the Django `MobilePass.pk`, not necessarily `pass.json` `serialNumber`.
6. **HasMobilePasses filtering** — use `instance.apple_passes()` / `instance.google_passes()`; the generic relation manager does not expose queryset helpers like `.apple()` directly.
7. **Apple change messages** — use the `:value` placeholder; it is converted to Apple's `%@` token automatically.

## Agent workflow summary

1. Read `MOBILE_PASS` settings and confirm credentials exist for the target platform.
2. Pick the builder from the registry table above (or a custom registered builder).
3. Build pass → `.save()` persists `MobilePass`.
4. Distribute via `download_response()`, `add_to_wallet_url()`, or `to_response()`.
5. For live updates, mutate stored content and `save()`; confirm `push_updates_on_save` / queue settings.
6. Listen to signals if the app needs side effects on wallet add/remove.

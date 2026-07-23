# django-mobile-pass

`django-mobile-pass` is a Django 5.2+ app and reusable Python package for issuing Apple Wallet and Google Wallet passes.

Full documentation lives in [`docs/`](docs/_index.md). AI agents should start with [`AGENTS.md`](AGENTS.md).

## Requirements

- Python 3.11+
- Django 5.2+
- `django.contrib.contenttypes`
- Apple PKCS#12 signing certificate for Apple passes
- Google Wallet issuer account and service account JSON for Google passes

## Install

```bash
pip install -e .
```

Add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django_mobile_pass",
]
```

Run the migration:

```bash
python manage.py migrate
```

## Settings

Configure credentials in `settings.py`:

```python
MOBILE_PASS = {
    "public_url": "https://example.com",
    "push_updates_on_save": True,
    "apple": {
        "organization_name": "Fab Four Promotions",
        "type_identifier": "pass.com.example.tickets",
        "team_identifier": "ABCDE12345",
        "certificate_path": "/absolute/path/to/pass-certificate.p12",
        "certificate_password": "secret",
        "webservice_secret": "replace-with-a-long-random-string",
        "webservice_host": "https://example.com",
    },
    "google": {
        "issuer_id": "3388000000022791700",
        "service_account_key_path": "/absolute/path/to/google-service-account.json",
        "origins": ["https://example.com"],
    },
}
```

See [`docs/configuration.md`](docs/configuration.md) for every available option, including custom models, actions, and builders.

Mount the wallet routes:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("django_mobile_pass.urls")),
]
```

## Apple Wallet example

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_organization_name("Fab Four Promotions")
    .set_serial_number("BTL-SHEA-0042")
    .set_description("The Beatles at Shea Stadium")
    .add_field("event", "Beatles Live at Shea")
    .add_field("attendee", "John Lennon", label="Name")
    .add_field("seat", "Floor A, Row 12")
    .set_remote_logo_image("https://cdn.example.com/logo.png")
    .save()
)
```

In a Django view:

```python
from django_mobile_pass.models import MobilePass

def download_pass(request, pass_id):
    mobile_pass = MobilePass.objects.get(pk=pass_id)
    return mobile_pass.download_response()
```

## Google Wallet example

Create a Google class once:

```python
from django_mobile_pass.google.builders import EventTicketPassClass

(
    EventTicketPassClass.make("beatles-shea-1965")
    .set_issuer_name("Fab Four Promotions")
    .set_event_name("Beatles Live at Shea")
    .set_logo_url("https://cdn.example.com/logo.png")
    .save()
)
```

Issue a Google Wallet object:

```python
from django_mobile_pass.enums import BarcodeType
from django_mobile_pass.google.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_class("beatles-shea-1965")
    .set_attendee_name("John Lennon")
    .set_section("Floor A")
    .set_row("12")
    .set_seat("24")
    .set_barcode(BarcodeType.QR, "TICKET-12345")
    .save()
)
```

Redirect the user to Google Wallet:

```python
def add_google_pass(request, pass_id):
    mobile_pass = MobilePass.objects.get(pk=pass_id)
    return mobile_pass.to_response()
```

## Stored model

The package ships with a `MobilePass` model that stores:

- the pass platform and type
- the builder name used to create it
- compiled Apple or Google payload JSON
- Apple image references (local paths or remote URLs)
- an optional download filename

**PassKit routes use `MobilePass.pk` (UUID) as the path `pass_serial`.** Sync the `serialNumber` in `pass.json` if you need them to match.

Apple passes can be rehydrated and updated later:

```python
mobile_pass.update_field("seat", "Floor B, Row 1", change_message="Seat changed to :value")
```

Attach passes to your own models with `HasMobilePasses`:

```python
from django.db import models
from django_mobile_pass.mixins import HasMobilePasses

class Ticket(HasMobilePasses, models.Model):
    event_name = models.CharField(max_length=255)
```

## Pass types

| Platform | Builders |
|----------|----------|
| Apple | `EventTicketPassBuilder`, `CouponPassBuilder`, `StoreCardPassBuilder`, `GenericPassBuilder`, `PosterGenericPassBuilder`, `BoardingPassBuilder`, `AirlinePassBuilder` |
| Google | `EventTicketPassClass` / `EventTicketPassBuilder`, `BoardingPassClass` / `BoardingPassBuilder`, `GenericPassClass` / `GenericPassBuilder`, `LoyaltyPassClass` / `LoyaltyPassBuilder`, `OfferPassClass` / `OfferPassBuilder` |

## Runtime URLs

The Django URL module provides the wallet service surface:

| Route | Purpose |
|-------|---------|
| `POST/DELETE /passkit/v1/devices/{device_id}/registrations/{pass_type_id}/{pass_serial}` | Register or unregister an Apple device |
| `GET /passkit/v1/passes/{pass_type_id}/{pass_serial}` | Return the latest `.pkpass` when updated |
| `GET /passkit/v1/devices/{device_id}/registrations/{pass_type_id}` | List serials updated since a timestamp |
| `POST /passkit/v1/log` | Receive Apple Wallet log messages |
| `GET /passkit/v1/apple/{mobile_pass_id}/download` | Signed Apple download URL |
| `POST /passkit/v1/google/callbacks` | Google save/remove callbacks (ECv2 verified) |

Saving an existing `MobilePass` triggers Apple APNs or Google object patch notifications when `push_updates_on_save` is enabled.

## Signals

The package emits Django signals you can connect to in your app config:

- `mobile_pass_added`
- `mobile_pass_removed`
- `apple_mobile_pass_logs_received`

## Testing

```bash
pip install -e ".[dev]"
python -m pytest tests/
```

## Documentation

- [Introduction](docs/introduction.md)
- [Installation and setup](docs/installation-setup.md)
- [Configuration reference](docs/configuration.md)
- [Basic usage](docs/basic-usage/_index.md)
- [Apple Wallet](docs/apple-wallet/_index.md)
- [Google Wallet](docs/google-wallet/_index.md)
- [Advanced usage](docs/advanced-usage/_index.md)
- [Changelog](docs/changelog.md)

## Project layout

```
django_mobile_pass/   # Python package
tests/                # pytest suite
docs/                 # Documentation
```

## What is included

- Apple Wallet builders for event tickets, coupons, store cards, generic cards, poster generic cards, and airline boarding passes
- `.pkpass` generation and PKCS#7 signing from a PKCS#12 certificate
- Local and remote Apple image support
- Google Wallet class and object builders for event tickets, flights, generic passes, loyalty cards, and offers
- a Django model and migration for storing issued passes
- Google Wallet JWT signing, REST client helpers, and ECv2 callback verification
- PassKit web service routes, signed Apple downloads, and wallet update notifications

## License

MIT — see [`LICENSE.md`](LICENSE.md).

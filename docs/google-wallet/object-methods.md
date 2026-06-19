---
title: Object methods
weight: 32
---

# Object methods

Object builders issue individual Google Wallet passes. Every object builder extends `GooglePassBuilder`.

## Shared object methods

| Method | Description |
|--------|-------------|
| `make()` | Create a new object builder. |
| `set_class(suffix)` | Link to a previously saved class suffix (required before `save()`). |
| `set_object_suffix(suffix)` | Pin a specific object suffix; otherwise one is generated automatically. |
| `set_barcode(format, message, alt_text=None)` | Add a scannable barcode (`BarcodeType.QR`, `PDF417`, `AZTEC`, `CODE128`). |
| `set_wifi_barcode(ssid, password=None, hidden=False, alt_text=None)` | Encode a WiFi network as a QR barcode. |
| `save()` | Insert the object via the Google Wallet API and persist a `MobilePass`. |

After saving, use `mobile_pass.to_response()` to redirect users to Google Wallet, or `mobile_pass.google_add_to_wallet_url()` for a Save to Wallet link.

## Event ticket object

```python
from django_mobile_pass.google.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_class("concert-2026")
    .set_object_suffix("ada-lovelace")
    .set_attendee_name("Ada Lovelace")
    .set_section("A")
    .set_row("12")
    .set_seat("4")
    .set_barcode(BarcodeType.QR, "TICKET-12345")
    .save()
)
```

## Boarding pass object

```python
from django_mobile_pass.google.builders import BoardingPassBuilder

mobile_pass = (
    BoardingPassBuilder.make()
    .set_class("sfo-jfk")
    .set_passenger_name("Ada Lovelace")
    .set_seat_number("12A")
    .set_confirmation_code("ABC123")
    .save()
)
```

## Generic object

```python
from django_mobile_pass.google.builders import GenericPassBuilder

mobile_pass = (
    GenericPassBuilder.make()
    .set_class("membership")
    .set_header("Ada Lovelace")
    .set_card_title("Member Card")
    .set_subheader("Gold tier")
    .set_expiry_notification_enabled(True)
    .save()
)
```

## Loyalty object

```python
from django_mobile_pass.google.builders import LoyaltyPassBuilder

mobile_pass = (
    LoyaltyPassBuilder.make()
    .set_class("rewards")
    .set_account_id("MEMBER-42")
    .set_account_name("Ada Lovelace")
    .set_balance_string("1,250 points")
    .save()
)
```

## Offer object

```python
from django_mobile_pass.google.builders import OfferPassBuilder

mobile_pass = (
    OfferPassBuilder.make()
    .set_class("spring-sale")
    .set_title("20% off everything")
    .set_redemption_code("SPRING20")
    .save()
)
```

Object IDs follow the same pattern as classes: `{issuer_id}.{suffix}`.

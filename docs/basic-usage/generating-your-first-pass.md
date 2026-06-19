---
title: Generating your first pass
weight: 11
---

# Generating your first pass

## PassKit serial identity

Apple Wallet PassKit routes in this package use the stored `MobilePass.pk` UUID as the path segment named `pass_serial`. The human-readable `serialNumber` inside `pass.json` can be different, but **device registration and update checks only work when the URL UUID matches the database row**.

Recommended pattern:

```python
mobile_pass = EventTicketPassBuilder.make().set_description("Launch").save()
mobile_pass.content["serialNumber"] = str(mobile_pass.pk)
mobile_pass.save(update_fields=["content", "updated_at"])
```

Or set `serial_number=str(uuid4())` before `save()` and use that same value in PassKit URLs.

## Apple event ticket

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("The Beatles at Shea Stadium")
    .add_field("event", "Beatles Live at Shea")
    .add_field("attendee", "John Lennon", label="Name")
    .add_field("seat", "Floor A, Row 12")
    .save()
)
mobile_pass.content["serialNumber"] = str(mobile_pass.pk)
mobile_pass.save(update_fields=["content", "updated_at"])
```

The package auto-fills `organization_name` from settings when omitted and generates a UUID `serialNumber` when you do not set one.

## Google event ticket

Create the class once:

```python
from django_mobile_pass.google.builders import EventTicketPassClass

(
    EventTicketPassClass.make("beatles-shea-1965")
    .set_issuer_name("Fab Four Promotions")
    .set_event_name("Beatles Live at Shea")
    .save()
)
```

Issue the object:

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

## Web service URL

Apple passes embed `webServiceURL` as `{webservice_host}/passkit`. Set `MOBILE_PASS["apple"]["webservice_host"]` to your public HTTPS origin, or rely on Django `APP_URL` as a fallback when the host is omitted.

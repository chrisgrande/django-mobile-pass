---
title: Event ticket
weight: 42
---

# Event ticket

Use Apple `EventTicketPassBuilder` or Google `EventTicketPassClass` plus `EventTicketPassBuilder` for concerts, conferences, shows, games, or admissions.

## Apple event ticket

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.enums import BarcodeType

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("Summer Concert")
    .add_field("event", "River Festival")
    .add_secondary_field("venue", "Main Hall")
    .add_auxiliary_field("seat", "A-12")
    .add_back_field("terms", "No refunds after doors open.")
    .set_barcode(BarcodeType.QR, "TICKET-12345", alt_text="Ticket 12345")
    .save()
)
```

Event tickets support back fields (`include_back_fields = True`), so `add_back_field()` is serialized into the pass.

## Google event ticket

Create the class first, then the object:

```python
from datetime import datetime

from django_mobile_pass.enums import BarcodeType
from django_mobile_pass.google.builders import EventTicketPassClass, EventTicketPassBuilder

(
    EventTicketPassClass.make("river-festival")
    .set_issuer_name("Example Events")
    .set_event_name("River Festival")
    .set_venue_name("Main Hall")
    .set_start_date(datetime(2026, 8, 1, 19, 0))
    .set_logo_url("https://cdn.example.test/logo.png")
    .save()
)

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_class("river-festival")
    .set_attendee_name("Ada Lovelace")
    .set_section("A")
    .set_row("12")
    .set_seat("4")
    .set_barcode(BarcodeType.QR, "TICKET-12345")
    .save()
)
```

Hand out the pass with `mobile_pass.to_response()` or attach it to a model with `mobile_pass.attach_to(order)`.

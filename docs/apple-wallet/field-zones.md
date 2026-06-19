---
title: Field zones
weight: 22
---

# Field zones

Apple passes display fields in distinct zones. Use the zone-specific helpers for precise placement, or `add_field()` for primary fields.

## Zone helpers

| Method | Zone | Typical use |
|--------|------|-------------|
| `add_field(key, value, ...)` | Primary | Main headline value |
| `add_header_field(...)` | Header | Top-right metadata (date, status) |
| `add_secondary_field(...)` | Secondary | Supporting labels below primary |
| `add_auxiliary_field(...)` | Auxiliary | Extra detail row |
| `add_back_field(...)` | Back | Terms, instructions (pass-type dependent) |

Each helper accepts optional `label`, `change_message`, `date_style`, `time_style`, and `show_date_as_relative` arguments.

## Example

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.enums import DateType, TimeStyleType
from datetime import datetime

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("River Festival")
    .add_field("event", "Main Stage")
    .add_header_field("date", datetime(2026, 8, 1, 19, 0).isoformat(),
                       date_style=DateType.MEDIUM, time_style=TimeStyleType.SHORT)
    .add_secondary_field("venue", "Main Hall")
    .add_auxiliary_field("seat", "A-12")
    .add_back_field("terms", "No refunds after doors open.")
    .save()
)
```

Back fields are only serialized for pass types with `include_back_fields = True` (event ticket, boarding pass, coupon).

## Updating fields on saved passes

```python
mobile_pass.update_field("seat", "B-4", change_message="Seat changed")
```

This hydrates the builder, updates the field value, re-saves, and optionally pushes an APNs update when `push_updates_on_save` is enabled.

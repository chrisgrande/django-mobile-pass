---
title: Pass relevance
weight: 23
---

# Pass relevance

Apple Wallet can surface passes on the lock screen when they are relevant by time or location. Configure relevance on any Apple builder.

## Relevant date

```python
from datetime import datetime, timezone

from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("River Festival")
    .add_field("event", "Main Stage")
    .set_relevant_date(datetime(2026, 8, 1, 19, 0, tzinfo=timezone.utc))
    .save()
)
```

## Locations

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("River Festival")
    .add_field("event", "Main Stage")
    .add_location(37.7749, -122.4194, relevant_text="You're near the venue")
    .add_location(37.7750, -122.4190, relevant_text="Main entrance")
    .save()
)
```

## Maximum distance

Limit how far from a relevant location the pass appears:

```python
builder.set_max_distance(500)  # meters
```

Relevance hints are advisory — Wallet decides when to show a pass based on user settings, Focus modes, and other signals. Google passes do not use these Apple-specific relevance fields; use class-level dates and notifications on the Google side instead.

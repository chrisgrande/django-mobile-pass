---
title: Customizing models
weight: 51
---

# Customizing models

Point `MOBILE_PASS` at your own models when you need extra fields or different table names.

```python
MOBILE_PASS = {
    "model": "myapp.CustomMobilePass",
    "apple_device_model": "myapp.CustomAppleDevice",
    "apple_registration_model": "myapp.CustomAppleRegistration",
    "google_event_model": "myapp.CustomGoogleEvent",
}
```

## Subclassing MobilePass

```python
from django.db import models
from django_mobile_pass.models import MobilePass as BaseMobilePass

class CustomMobilePass(BaseMobilePass):
    order = models.ForeignKey("shop.Order", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "custom_mobile_passes"
```

Custom models must preserve:

- The `content` and `images` JSON fields
- `platform`, `type`, `builder_name` fields used by builders
- Relationships expected by actions (`apple_registrations`, `google_events`)
- Methods used by views: `builder()`, `generate()`, `was_updated_after()`, `expire()`

Subclassing is the safest approach — you inherit behavior and add fields.

## Device and registration models

```python
from django_mobile_pass.models import (
    AppleMobilePassDevice as BaseDevice,
    AppleMobilePassRegistration as BaseRegistration,
)

class CustomAppleRegistration(BaseRegistration):
    notified_at = models.DateTimeField(null=True, blank=True)

    def apple_update_url(self) -> str:
        return super().apple_update_url()
```

`AppleMobilePassRegistration` must expose `apple_update_url()`, `pass_type_id`, `device`, and `mobile_pass`.

## Google event model

```python
from django_mobile_pass.models import GoogleMobilePassEvent as BaseGoogleEvent

class CustomGoogleEvent(BaseGoogleEvent):
    processed = models.BooleanField(default=False)
```

Callbacks create events via `HandleGoogleCallbackAction`; keep `event_type`, `mobile_pass`, `received_at`, and `raw_payload` intact.

Run migrations after defining custom models, then update `MOBILE_PASS` model paths before creating passes.

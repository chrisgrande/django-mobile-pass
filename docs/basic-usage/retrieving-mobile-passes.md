---
title: Retrieving mobile passes
weight: 13
---

# Retrieving mobile passes

Query the `MobilePass` model directly, or attach passes to your own models with `HasMobilePasses`.

## Direct queries

```python
from django_mobile_pass.models import MobilePass
from django_mobile_pass.enums import Platform

# All Apple passes
apple_passes = MobilePass.objects.apple()

# All Google passes
google_passes = MobilePass.objects.google()

# Lookup by primary key (also used in PassKit routes)
mobile_pass = MobilePass.objects.get(pk=pass_uuid)
```

PassKit web service routes use the `MobilePass` UUID (`pk`) as the path `pass_serial`, not the human-readable `serialNumber` inside `pass.json`.

## Attaching to your models

```python
from django.db import models
from django_mobile_pass.mixins import HasMobilePasses

class Customer(HasMobilePasses, models.Model):
    email = models.EmailField()
```

Mixin helpers:

| Method | Returns |
|--------|---------|
| `add_mobile_pass(pass_)` | Attach a pass via generic foreign key |
| `apple_passes()` | Apple passes linked to this model |
| `google_passes()` | Google passes linked to this model |
| `first_apple_pass()` | First Apple pass or `None` |
| `first_google_pass()` | First Google pass or `None` |

```python
customer = Customer.objects.get(email="ada@example.test")
ticket = customer.first_apple_pass()

if ticket and ticket.is_currently_in_wallet():
    ticket.update_field("gate", "B12", change_message="Gate changed")
```

## Hydrating builders

Apple passes can be reloaded into an updateable builder:

```python
builder = mobile_pass.builder()
payload = builder.data()
```

Google passes store API payloads in `content["googleObjectPayload"]` and are updated through the Google Wallet client or by re-saving a hydrated builder where supported.

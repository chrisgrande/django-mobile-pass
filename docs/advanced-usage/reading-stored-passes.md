---
title: Reading stored passes
weight: 55
---

# Reading stored passes

Stored pass payloads live in `MobilePass.content`; Apple image references live in `MobilePass.images`. Google callback history is in `GoogleMobilePassEvent`; Apple device links are in `AppleMobilePassRegistration`.

## Common fields

| Field | Purpose |
|-------|---------|
| `content` | Compiled Apple `pass.json` payload or Google class/object metadata and payloads |
| `images` | Apple image paths or remote URLs keyed by slot (`logo`, `icon`, `strip`, …) |
| `builder_name` | Registry key used to create the pass (for example `event_ticket`) |
| `platform` | `apple` or `google` |
| `type` | Pass style (`eventTicket`, `coupon`, `boardingPass`, …) |
| `expired_at` | Set when `expire()` runs |
| `content_object` | Optional generic foreign key to your domain model |

## Apple-only reload

```python
builder = mobile_pass.builder()
payload = builder.data()
updated = builder.update_field("gate", "B12").save()
```

## Google object payload

Google object fields live under `mobile_pass.content["googleObjectPayload"]`. Update that dict, then `save()` to PATCH the live Google object when `push_updates_on_save` is enabled.

## Related rows

```python
mobile_pass.apple_registrations.all()
mobile_pass.google_events.order_by("-received_at")
GoogleMobilePassEvent.saves()
GoogleMobilePassEvent.removes()
```

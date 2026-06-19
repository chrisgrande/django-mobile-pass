---
title: Updating a pass
weight: 14
---

# Updating a pass

## Apple field updates

Apple field updates rehydrate the stored builder, update the field, save the new payload, and notify registered devices when `push_updates_on_save` is enabled:

```python
mobile_pass.update_field(
    "seat",
    "Floor B, Row 1",
    change_message="Seat changed to :value",
)
```

The `:value` placeholder becomes Apple's `%@` change message token on the lock screen.

For multiple changes, hydrate the builder directly:

```python
mobile_pass.builder().update_field("seat", "12A").update_field("gate", "B2").save()
```

## Google object updates

Mutate the stored Google object payload, then save:

```python
content = dict(mobile_pass.content)
object_payload = dict(content["googleObjectPayload"])
object_payload["state"] = "ACTIVE"
object_payload["textModulesData"] = [{"header": "Status", "body": "Confirmed"}]
content["googleObjectPayload"] = object_payload
mobile_pass.content = content
mobile_pass.save()
```

Saving an existing `MobilePass` triggers `NotifyGoogleOfPassUpdateAction` when `MOBILE_PASS["push_updates_on_save"]` is true.

## Update delivery model

By default, wallet update notifications run **synchronously** on save. For async delivery, configure `MOBILE_PASS.queue` (see [Configuration](../configuration.md#queue-backed-updates)). Disable notifications with:

```python
MOBILE_PASS = {
    "push_updates_on_save": False,
}
```

Apple still requires your PassKit routes to stay online so devices can download the refreshed `.pkpass` after the APNs wake-up notification.

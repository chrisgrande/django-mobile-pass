---
title: Expiring passes
weight: 15
---

# Expiring passes

Call `expire()` on a stored `MobilePass` to mark it void in the user's wallet.

```python
mobile_pass.expire()
```

## What happens per platform

**Apple** — the stored content is updated with:

- `voided: true`
- `expirationDate` set to the current timestamp

Registered devices receive an APNs push when `push_updates_on_save` is enabled, prompting Wallet to download the updated pass.

**Google** — the stored `googleObjectPayload` is patched with `state: "EXPIRED"`. The next `NotifyGoogleOfPassUpdateAction` (or a manual `save()` with updated content) syncs the change to Google Wallet.

## Checking expiry

```python
if mobile_pass.expired_at is not None:
    ...
```

`expired_at` is set on the model when `expire()` runs, regardless of platform.

## Re-activating

There is no built-in `unexpire()` helper. Create a new pass or manually update `content` and clear `expired_at` if your business logic requires re-issuing.

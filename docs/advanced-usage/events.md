---
title: Signals
weight: 53
---

# Signals

The package exposes Django signals you can connect to in your app config:

- `mobile_pass_added`
- `mobile_pass_removed`
- `apple_mobile_pass_logs_received`

## When signals fire

| Signal | Trigger |
|--------|---------|
| `mobile_pass_added` | New Apple device registration, or Google callback `save` event |
| `mobile_pass_removed` | Apple device unregister, or Google callback `del` event |
| `apple_mobile_pass_logs_received` | `POST /passkit/v1/log` with a `logs` payload |

```python
from django_mobile_pass.signals import mobile_pass_added

def on_pass_added(sender, mobile_pass, **kwargs):
    ...

mobile_pass_added.connect(on_pass_added)
```

## Wallet presence helpers

```python
mobile_pass.is_currently_in_wallet()
mobile_pass.is_currently_saved_to_google_wallet()
mobile_pass.google_events.order_by("-received_at")
GoogleMobilePassEvent.saves()
GoogleMobilePassEvent.removes()
```

Apple registrations are removed per device. Google presence is inferred from the latest callback event.

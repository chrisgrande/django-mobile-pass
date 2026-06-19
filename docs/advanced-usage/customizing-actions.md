---
title: Customizing actions
weight: 52
---

# Customizing actions

Subclass or replace the built-in action classes when your app needs additional side effects. Import the defaults from `django_mobile_pass.actions`.

Available action keys in `MOBILE_PASS["actions"]`:

| Key | Default class | Responsibility |
|-----|---------------|----------------|
| `register_device` | `RegisterDeviceAction` | Store Apple device registrations from PassKit |
| `unregister_device` | `UnregisterDeviceAction` | Remove registrations and emit `mobile_pass_removed` |
| `notify_apple_of_pass_update` | `NotifyAppleOfPassUpdateAction` | Send APNs update notifications |
| `notify_google_of_pass_update` | `NotifyGoogleOfPassUpdateAction` | Patch the stored Google object |
| `handle_google_callback` | `HandleGoogleCallbackAction` | Record Google save/remove events |

Example override:

```python
from django_mobile_pass.actions import RegisterDeviceAction

class AuditRegisterDeviceAction(RegisterDeviceAction):
    def execute(self, device_id, push_token, pass_type_id, pass_serial):
        registration = super().execute(device_id, push_token, pass_type_id, pass_serial)
        # audit logging here
        return registration

MOBILE_PASS = {
    "actions": {
        "register_device": "myapp.wallet_actions.AuditRegisterDeviceAction",
    },
}
```

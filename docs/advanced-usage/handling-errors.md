---
title: Handling errors
weight: 54
---

# Handling errors

The package raises typed exceptions from `django_mobile_pass.exceptions`:

| Exception | When it fires |
|-----------|---------------|
| `InvalidPass` | Builder validation failed (missing required Apple/Google fields) |
| `InvalidConfig` | Missing or malformed `MOBILE_PASS` credentials |
| `InvalidCertificate` | Apple PKCS#12 bundle cannot be read or signed |
| `ImageNotFound` | Local Apple image path does not exist |
| `CannotDownload` | Download helpers called on a Google pass |
| `PlatformDoesntSupport` | Apple-only helpers called on a Google pass |
| `AppleWalletRequestFailed` | APNs update request failed (`status`, `payload` attributes) |
| `GoogleWalletRequestFailed` | Google Wallet API request failed (`status`, `payload` attributes) |

Catch builder errors when creating passes:

```python
from django_mobile_pass.exceptions import InvalidPass

try:
    mobile_pass = EventTicketPassBuilder.make().save()
except InvalidPass as exc:
    ...
```

PassKit routes return HTTP status codes instead of raising to callers: `403` for bad auth, `404` for unknown passes, `413` for oversized bodies.

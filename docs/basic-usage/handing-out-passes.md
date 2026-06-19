---
title: Handing out passes
weight: 12
---

# Handing out passes

## From a Django view

Return an Apple download or Google redirect:

```python
from django_mobile_pass.models import MobilePass

def add_to_wallet(request, pass_id):
    return MobilePass.objects.get(pk=pass_id).to_response()
```

- Apple: `to_response()` serves a signed `.pkpass` download.
- Google: `to_response()` redirects to the Save to Wallet URL.

## Platform-specific helpers

```python
mobile_pass = MobilePass.objects.get(pk=pass_id)

# Absolute signed Apple download link
apple_url = mobile_pass.add_to_wallet_url(request=request)

# Google Save to Wallet URL
google_url = mobile_pass.google_add_to_wallet_url()

# Raw .pkpass bytes or HTTP response
pkpass_bytes = mobile_pass.download()
response = mobile_pass.download_response(name="ticket")

# Email attachment tuple: (filename, bytes, mime)
filename, data, mime = mobile_pass.email_attachment()
```

Set `MOBILE_PASS["public_url"]` when you need absolute Apple links outside a request context.

## QR codes and links

Generate a QR code from `add_to_wallet_url(request)` for Apple passes, or from `google_add_to_wallet_url()` for Google passes. Treat signed Apple download URLs as bearer links.

## Check wallet state

```python
mobile_pass.is_currently_in_wallet()
mobile_pass.is_currently_saved_to_google_wallet()  # Google only
```

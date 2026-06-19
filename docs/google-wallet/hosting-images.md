---
title: Hosting images
weight: 33
---

# Hosting images

Google Wallet classes fetch images from public HTTPS URLs at render time. Local file paths are **not** supported for Google passes — use hosted assets only.

## Class image setters

| Class | Logo | Hero |
|-------|------|------|
| `EventTicketPassClass` | `set_logo_url(url)` | `set_hero_image_url(url)` |
| `BoardingPassClass` | `set_logo_url(url)` | `set_hero_image_url(url)` |
| `GenericPassClass` | `set_logo_url(url)` | `set_hero_image_url(url)` |
| `LoyaltyPassClass` | `set_program_logo_url(url)` | — |
| `OfferPassClass` | `set_logo_url(url)` | — |

## Requirements

- URLs must be reachable over **HTTPS** from Google's servers.
- Images should be PNG or JPEG; keep file sizes reasonable for fast Wallet rendering.
- Use a CDN or object store with stable, long-lived URLs. Rotating URLs break passes already saved to wallets.
- Apple passes can use local files (`set_logo_image`) or remote URLs (`set_remote_logo_image`). Google passes cannot.

## Example

```python
from django_mobile_pass.google.builders import EventTicketPassClass

(
    EventTicketPassClass.make("festival-2026")
    .set_issuer_name("Example Events")
    .set_event_name("River Festival")
    .set_logo_url("https://cdn.example.test/wallet/logo@2x.png")
    .set_hero_image_url("https://cdn.example.test/wallet/hero.jpg")
    .save()
)
```

For Apple remote images, see [Adding images](../basic-usage/adding-images.md).

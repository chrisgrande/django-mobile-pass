---
title: Attaching WiFi credentials
weight: 25
---

# Attaching WiFi credentials

Apple passes can embed WiFi network details so Wallet can offer to join a network. Both Apple and Google builders support WiFi QR barcodes.

## Apple WiFi semantics

Add structured WiFi credentials with `add_wifi_network()`:

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("Conference pass")
    .add_field("guest", "Ada Lovelace")
    .add_wifi_network("Conference-Guest", "secret-password")
    .save()
)
```

This serializes WiFi details into the pass payload for Wallet's native join-network flow.

## WiFi QR barcode (Apple and Google)

Encode a WiFi network as a scannable QR barcode:

```python
builder.set_wifi_barcode("Conference-Guest", password="secret-password", hidden=False, alt_text="Conference WiFi")
```

The barcode uses the standard `WIFI:` URI format. Users scan it with any QR reader or Wallet's barcode scanner.

## When to use which

| Approach | Platform | Best for |
|----------|----------|----------|
| `add_wifi_network()` | Apple only | One-tap join from Wallet |
| `set_wifi_barcode()` | Apple + Google | Universal QR scanning |

You can combine both on an Apple pass if you want Wallet-native join and a visible QR fallback.

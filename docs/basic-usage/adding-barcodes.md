---
title: Adding barcodes
weight: 16
---

# Adding barcodes

Both Apple and Google builders support barcodes through `set_barcode()` and WiFi-specific `set_wifi_barcode()`. Apple builders also support `add_barcode()` for iOS 27 multi-format fallbacks.

## Standard barcodes

```python
from django_mobile_pass.enums import BarcodeType

builder.set_barcode(BarcodeType.QR, "TICKET-12345", alt_text="Ticket 12345")
```

Supported formats:

| `BarcodeType` | Apple Wallet | Google Wallet |
|---------------|--------------|---------------|
| `QR` | Yes | Yes |
| `PDF417` | Yes | Yes |
| `AZTEC` | Yes | Yes |
| `CODE128` | Yes | Yes |
| `CODE39` | Yes (iOS 27+) | No |
| `CODABAR` | Yes (iOS 27+) | No |
| `EAN13` | Yes (iOS 27+) | No |
| `ITF` | Yes (iOS 27+) | No |

`alt_text` is shown to accessibility tools and when the barcode cannot be rendered.

## Apple multi-barcode fallbacks (iOS 27+)

Wallet picks the first format it can render. Lead with your preferred format and append a widely supported fallback (such as QR) for older iOS:

```python
builder.set_barcode(BarcodeType.CODABAR, "123456789")
builder.add_barcode(BarcodeType.QR, "123456789")
```

`set_barcode()` replaces the list. `add_barcode()` appends. The legacy top-level `barcode` key is set to the first entry.

## WiFi barcodes

```python
builder.set_wifi_barcode("Guest WiFi", password="secret", hidden=False, alt_text="Guest WiFi")
```

This encodes a `WIFI:` URI suitable for QR scanning. See [Attaching WiFi credentials](../apple-wallet/attaching-wifi-credentials.md) for Apple-native network join via `add_wifi_network()`.

## Apple example

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.enums import BarcodeType

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("River Festival")
    .add_field("event", "Main Stage")
    .set_barcode(BarcodeType.QR, "TICKET-12345", alt_text="Ticket 12345")
    .save()
)
```

## Google example

```python
from django_mobile_pass.google.builders import EventTicketPassBuilder
from django_mobile_pass.enums import BarcodeType

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_class("river-festival")
    .set_barcode(BarcodeType.QR, "TICKET-12345")
    .save()
)
```

Google builders store one barcode. Apple builders can store multiple via `add_barcode()` as shown above.

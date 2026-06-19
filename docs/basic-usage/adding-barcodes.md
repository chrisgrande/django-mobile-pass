---
title: Adding barcodes
weight: 16
---

# Adding barcodes

Both Apple and Google builders support barcodes through `set_barcode()` and WiFi-specific `set_wifi_barcode()`.

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

`alt_text` is shown to accessibility tools and when the barcode cannot be rendered.

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

Only one barcode is stored per builder instance. Set it before calling `save()`.

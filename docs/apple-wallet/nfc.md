---
title: NFC
weight: 24
---

# NFC

Apple passes can carry NFC payloads when your Pass Type ID and signing certificate support NFC. Use `set_nfc()` on any Apple builder.

```python
from django_mobile_pass.apple.builders import EventTicketPassBuilder

mobile_pass = (
    EventTicketPassBuilder.make()
    .set_description("VIP access")
    .add_field("guest", "Ada Lovelace")
    .set_nfc(
        message="ticket:12345",
        encryption_public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...",
        requires_authentication=False,
    )
    .save()
)
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `message` | Payload delivered to your NFC reader infrastructure. |
| `encryption_public_key` | EC public key (base64) used to encrypt the NFC message per Apple's spec. |
| `requires_authentication` | When `True`, the user must authenticate before the NFC payload is transmitted. |

NFC requires additional entitlement configuration in your Apple Developer account. Without the correct Pass Type ID capability, Wallet will not expose the NFC interaction even if the field is present in `pass.json`.

For barcode-based scanning instead of NFC, see [Adding barcodes](../basic-usage/adding-barcodes.md).

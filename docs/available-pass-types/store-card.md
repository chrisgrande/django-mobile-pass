---
title: Store card
weight: 47
---

# Store card

Apple store cards use `StoreCardPassBuilder`. They are the Apple Wallet equivalent of loyalty or gift cards.

```python
from django_mobile_pass.apple.builders import StoreCardPassBuilder
from django_mobile_pass.enums import BarcodeType

mobile_pass = (
    StoreCardPassBuilder.make()
    .set_description("Rewards card")
    .add_field("balance", "$42.00")
    .add_secondary_field("member", "Ada Lovelace")
    .add_auxiliary_field("tier", "Gold")
    .set_barcode(BarcodeType.QR, "MEMBER-42")
    .save()
)
```

Update balances on saved passes with `update_field()`:

```python
mobile_pass.update_field("balance", "$50.00", change_message="Balance updated")
```

When `push_updates_on_save` is enabled, registered devices receive an APNs notification so Wallet fetches the new pass content.

For Google loyalty programs, use [Loyalty](loyalty.md) instead.

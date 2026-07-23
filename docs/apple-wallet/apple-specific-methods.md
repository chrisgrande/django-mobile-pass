---
title: Apple-specific methods
weight: 21
---

# Apple-specific methods

Apple builders support:

- Identity: `set_serial_number`, `set_organization_name`, `set_description`, `set_download_name`
- Colors: `set_background_color`, `set_foreground_color`, `set_label_color`
- Relevance: `set_relevant_date`, `add_location`, `set_max_distance`
- Connectivity: `set_nfc`, `add_wifi_network`
- Barcodes: `set_barcode`, `add_barcode`, `set_wifi_barcode`
- Featured actions (iOS 27+): `add_featured_action` (max two; see `FeaturedActionType`)
- Pricing: `set_total_price`
- Fields: `add_field`, `add_header_field`, `add_secondary_field`, `add_auxiliary_field`, `add_back_field`, `add_footer_field`
- Local images: `set_icon_image`, `set_logo_image`, `set_strip_image`, `set_thumbnail_image`, `set_background_image`, `set_primary_logo_image`
- Remote images: `set_remote_icon_image`, `set_remote_logo_image`, `set_remote_strip_image`, `set_remote_thumbnail_image`, `set_remote_background_image`, `set_remote_primary_logo_image`
- Output: `data()`, `generate()`, `save()`

### Featured actions

```python
from django_mobile_pass.enums import FeaturedActionType

builder.add_featured_action(
    "offers",
    FeaturedActionType.MEMBERSHIP_BENEFITS,
    "https://example.com/offers",
)
```

Each pass may include up to two featured actions. Wallet draws them below the pass face on iOS 27+.

Hydrate a stored pass back into a builder with `mobile_pass.builder()`, then call `update_field()` or builder methods before `save()`.

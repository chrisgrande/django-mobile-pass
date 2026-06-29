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
- Barcodes: `set_barcode`, `set_wifi_barcode`
- Pricing: `set_total_price`
- Fields: `add_field`, `add_header_field`, `add_secondary_field`, `add_auxiliary_field`, `add_back_field`
- Local images: `set_icon_image`, `set_logo_image`, `set_strip_image`, `set_thumbnail_image`
- Remote images: `set_remote_icon_image`, `set_remote_logo_image`, `set_remote_strip_image`, `set_remote_thumbnail_image`
- Output: `data()`, `generate()`, `save()`

Hydrate a stored pass back into a builder with `mobile_pass.builder()`, then call `update_field()` or builder methods before `save()`.

---
title: Coupon
weight: 44
---

# Coupon

Apple coupons use `CouponPassBuilder`. Google offers use `OfferPassClass` plus `OfferPassBuilder`.

## Apple coupon

```python
from django_mobile_pass.apple.builders import CouponPassBuilder
from django_mobile_pass.enums import BarcodeType

mobile_pass = (
    CouponPassBuilder.make()
    .set_description("Spring sale")
    .add_field("offer", "20% off")
    .add_secondary_field("expires", "June 30")
    .add_back_field("terms", "In-store only. One per customer.")
    .set_barcode(BarcodeType.CODE128, "SPRING20")
    .save()
)
```

## Google offer

Google offer classes require a title.

```python
from django_mobile_pass.google.builders import OfferPassClass, OfferPassBuilder

(
    OfferPassClass.make("spring-sale")
    .set_issuer_name("Example Shop")
    .set_title("20% off everything")
    .set_provider("Example Shop")
    .set_details("Valid in-store through June 30.")
    .set_redemption_channel("INSTORE")
    .set_logo_url("https://cdn.example.test/logo.png")
    .save()
)

mobile_pass = (
    OfferPassBuilder.make()
    .set_class("spring-sale")
    .set_title("20% off everything")
    .set_redemption_code("SPRING20")
    .save()
)
```

Expire redeemed offers with `mobile_pass.expire()` so Wallet shows them as voided.

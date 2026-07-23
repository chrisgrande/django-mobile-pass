---
title: Generic
weight: 45
---

# Generic

Use Apple `GenericPassBuilder` / `PosterGenericPassBuilder`, or Google `GenericPassClass` plus `GenericPassBuilder`, for simple wallet cards that do not need a specialized wallet layout.

## Apple generic pass

```python
from django_mobile_pass.apple.builders import GenericPassBuilder

mobile_pass = (
    GenericPassBuilder.make()
    .set_description("Access card")
    .add_field("member", "Ada Lovelace")
    .add_secondary_field("id", "MEMBER-42")
    .add_header_field("status", "Active")
    .add_back_field("terms", "Membership terms apply.")
    .save()
)
```

## Apple poster generic pass (iOS 27+)

`PosterGenericPassBuilder` emits the iOS 27 `posterGeneric` style and also includes a classic `generic` section so devices on iOS 26 and earlier can still add the pass.

```python
from django_mobile_pass.apple.builders import PosterGenericPassBuilder
from django_mobile_pass.enums import BarcodeType, FeaturedActionType

mobile_pass = (
    PosterGenericPassBuilder.make()
    .set_description("Gym membership")
    .add_header_field("memberID", "102035", label="Guest No.")
    .add_field("name", "Finley")  # omit label for a bold poster title
    .add_footer_field("org", "Example Gym")
    .set_remote_background_image("https://cdn.example.com/member.jpg")
    .set_remote_primary_logo_image("https://cdn.example.com/logo.png")
    .set_barcode(BarcodeType.CODABAR, "123456789")
    .add_barcode(BarcodeType.QR, "123456789")  # fallback for older iOS
    .add_featured_action(
        "offers", FeaturedActionType.MEMBERSHIP_BENEFITS, "https://example.com/offers"
    )
    .save()
)
```

Poster passes support a single footer field on the face (`add_footer_field`). Extra footer fields are stored, but Wallet only displays the first.

## Google generic pass

```python
from django_mobile_pass.google.builders import GenericPassClass, GenericPassBuilder

(
    GenericPassClass.make("access-card")
    .set_issuer_name("Example Club")
    .set_card_title("Member Card")
    .set_subheader("Gold tier")
    .set_logo_url("https://cdn.example.test/logo.png")
    .save()
)

mobile_pass = (
    GenericPassBuilder.make()
    .set_class("access-card")
    .set_header("Ada Lovelace")
    .set_card_title("Member Card")
    .set_subheader("Valid through 2027")
    .save()
)
```

Generic passes work well for membership cards, simple access credentials, or any pass where specialized semantics are not required.

---
title: Generic
weight: 45
---

# Generic

Use Apple `GenericPassBuilder` or Google `GenericPassClass` plus `GenericPassBuilder` for simple wallet cards that do not need a specialized wallet layout.

## Apple generic pass

```python
from django_mobile_pass.apple.builders import GenericPassBuilder

mobile_pass = (
    GenericPassBuilder.make()
    .set_description("Access card")
    .add_field("member", "Ada Lovelace")
    .add_secondary_field("id", "MEMBER-42")
    .add_header_field("status", "Active")
    .save()
)
```

Generic Apple passes do not serialize back fields — use event ticket or coupon builders if you need `add_back_field()`.

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

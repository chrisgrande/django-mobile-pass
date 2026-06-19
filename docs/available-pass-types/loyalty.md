---
title: Loyalty
weight: 46
---

# Loyalty

Google loyalty passes use `LoyaltyPassClass` and `LoyaltyPassBuilder`. Apple store-card style passes use `StoreCardPassBuilder`.

## Google loyalty pass

```python
from django_mobile_pass.google.builders import LoyaltyPassClass, LoyaltyPassBuilder

(
    LoyaltyPassClass.make("rewards-plus")
    .set_issuer_name("Example Retail")
    .set_program_name("Rewards Plus")
    .set_program_logo_url("https://cdn.example.test/program.png")
    .set_rewards_tier("Gold")
    .set_rewards_tier_label("Tier")
    .set_account_name_label("Member")
    .set_account_id_label("ID")
    .save()
)

mobile_pass = (
    LoyaltyPassBuilder.make()
    .set_class("rewards-plus")
    .set_account_id("MEMBER-42")
    .set_account_name("Ada Lovelace")
    .set_balance_string("1,250 points")
    .save()
)
```

Update balances by re-saving the object builder or patching via `NotifyGoogleOfPassUpdateAction` after changing stored content.

## Apple store card

```python
from django_mobile_pass.apple.builders import StoreCardPassBuilder

mobile_pass = (
    StoreCardPassBuilder.make()
    .set_description("Rewards card")
    .add_field("balance", "$42.00")
    .add_secondary_field("member", "Ada Lovelace")
    .add_auxiliary_field("tier", "Gold")
    .save()
)
```

See also [Store card](store-card.md) for Apple-specific store card details.

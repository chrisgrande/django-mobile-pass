---
title: Pass classes
weight: 31
---

# Pass classes

Google Wallet passes are split into a **class** (template) and an **object** (individual pass). Create and save the class before issuing objects.

All class builders extend `GooglePassClass` and share these methods:

| Method | Description |
|--------|-------------|
| `make(suffix)` | Start a class with a unique suffix (combined with your issuer ID). |
| `set_issuer_name(name)` | Display name shown in Wallet. |
| `set_background_color(hex)` | Card background color, e.g. `#4285f4`. |
| `save()` | Insert the class via the Google Wallet API. |
| `retire()` | Mark the class `REJECTED` so new objects cannot be issued. |
| `find(suffix)` | Fetch a class by suffix, or `None` if missing. |
| `all()` | List every class of this type for your issuer. |

Class IDs are always `{issuer_id}.{suffix}`.

## Event ticket class

```python
from datetime import datetime

from django_mobile_pass.google.builders import EventTicketPassClass

(
    EventTicketPassClass.make("concert-2026")
    .set_issuer_name("Example Events")
    .set_event_name("Summer Concert")
    .set_venue_name("Main Hall")
    .set_venue_address("1 Example Street")
    .set_start_date(datetime(2026, 7, 15, 20, 0))
    .set_logo_url("https://cdn.example.test/logo.png")
    .set_hero_image_url("https://cdn.example.test/hero.jpg")
    .set_background_color("#1a1a2e")
    .save()
)
```

## Boarding pass class

```python
from datetime import datetime

from django_mobile_pass.google.builders import BoardingPassClass

(
    BoardingPassClass.make("sfo-jfk")
    .set_issuer_name("Example Air")
    .set_airline_code("EX")
    .set_flight_number("123")
    .set_origin_airport_code("SFO")
    .set_destination_airport_code("JFK")
    .set_local_scheduled_departure_datetime(datetime(2026, 6, 1, 9, 30))
    .set_logo_url("https://cdn.example.test/airline-logo.png")
    .save()
)
```

## Generic class

```python
from django_mobile_pass.google.builders import GenericPassClass

(
    GenericPassClass.make("membership")
    .set_issuer_name("Example Club")
    .set_card_title("Member Card")
    .set_subheader("Valid through 2027")
    .set_header("Ada Lovelace")
    .set_logo_url("https://cdn.example.test/logo.png")
    .save()
)
```

## Loyalty class

```python
from django_mobile_pass.google.builders import LoyaltyPassClass

(
    LoyaltyPassClass.make("rewards")
    .set_issuer_name("Example Retail")
    .set_program_name("Rewards Plus")
    .set_program_logo_url("https://cdn.example.test/program.png")
    .set_rewards_tier("Gold")
    .set_rewards_tier_label("Tier")
    .set_account_name_label("Member")
    .set_account_id_label("ID")
    .save()
)
```

## Offer class

Google offer classes require a title.

```python
from django_mobile_pass.google.builders import OfferPassClass

(
    OfferPassClass.make("spring-sale")
    .set_issuer_name("Example Shop")
    .set_title("20% off everything")
    .set_provider("Example Shop")
    .set_details("Valid in-store only.")
    .set_fine_print("Cannot be combined with other offers.")
    .set_redemption_channel("INSTORE")
    .set_logo_url("https://cdn.example.test/logo.png")
    .save()
)
```

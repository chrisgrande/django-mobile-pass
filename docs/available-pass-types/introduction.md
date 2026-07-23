---
title: Pass type introduction
weight: 41
---

# Pass type introduction

Choose the wallet type that matches the data model users expect. Each type maps to a dedicated builder pair (Apple + Google where supported).

## Apple pass types

| Builder | Use for |
|---------|---------|
| `EventTicketPassBuilder` | Concerts, conferences, admissions |
| `BoardingPassBuilder` / `AirlinePassBuilder` | Transit and airline boarding |
| `CouponPassBuilder` | Discounts and promotional offers |
| `StoreCardPassBuilder` | Loyalty, gift, and membership cards |
| `GenericPassBuilder` | Simple cards without specialized layout |
| `PosterGenericPassBuilder` | iOS 27+ artwork-first membership / loyalty cards |

## Google pass types

| Class + object builders | Use for |
|-------------------------|---------|
| `EventTicketPassClass` / `EventTicketPassBuilder` | Tickets and admissions |
| `BoardingPassClass` / `BoardingPassBuilder` | Flight boarding passes |
| `OfferPassClass` / `OfferPassBuilder` | Coupons and offers |
| `LoyaltyPassClass` / `LoyaltyPassBuilder` | Loyalty and rewards programs |
| `GenericPassClass` / `GenericPassBuilder` | General-purpose cards |

## Choosing a type

- **Event tickets** and **boarding passes** have specialized wallet semantics (seat info, gate changes, transit status).
- **Coupons/offers** emphasize redemption codes and expiry.
- **Store cards/loyalty** emphasize balances, tiers, and account identifiers.
- **Generic** works when you only need a few labeled fields and a barcode.
- **Poster generic** (Apple, iOS 27+) uses a full-bleed background image with a classic `generic` fallback for older devices.

All builders follow the same pattern: configure fields, optionally add images and barcodes, then call `save()` to persist a `MobilePass` record.

See the per-type pages for complete examples:

- [Event ticket](event-ticket.md)
- [Boarding pass](boarding-pass.md)
- [Coupon](coupon.md)
- [Store card](store-card.md)
- [Loyalty](loyalty.md)
- [Generic](generic.md)

---
title: Feature matrix
weight: 94
---

# Feature matrix: Apple Wallet vs Google Wallet

This page maps capabilities across both wallet platforms.

## Platform overview

| Capability | Apple Wallet | Google Wallet |
|------------|:------------:|:-------------:|
| Pass file / save link | `.pkpass` download | Save-to-Wallet JWT URL |
| Template + instance model | Single signed JSON pass | Class + object REST resources |
| Barcodes (QR, PDF417, Aztec, Code128) | Yes | Yes |
| Barcodes (Code39, Codabar, EAN13, ITF) | Yes (iOS 27+) | No |
| Multi-barcode fallback array | Yes (`add_barcode`) | No |
| Featured actions | Yes (`add_featured_action`, iOS 27+) | No |
| WiFi QR barcode helper | Yes (`set_wifi_barcode`) | Yes (`set_wifi_barcode`) |
| Local image files | Yes | No — public HTTPS URLs only |
| Remote HTTPS images | Yes | Yes |
| Pass expiration | `voided` + `expirationDate` | `state: EXPIRED` |
| In-wallet detection | Device registrations | Save/remove callback events |
| Push updates on save | APNs empty push | Objects API PATCH |
| Optional async updates | `MOBILE_PASS.queue` | `MOBILE_PASS.queue` |
| NFC payload | Yes (`set_nfc`) | Not in this package |
| Native WiFi join (Apple semantics) | Yes (`add_wifi_network`) | WiFi QR only |
| Location / relevance | Yes | Limited (type-specific) |
| Field-level live update API | `update_field()` | Update stored object payload + save |
| Inspect existing `.pkpass` | `PkPassReader` | N/A |

## Pass types

| Use case | Apple builder key | Google builder key |
|----------|-------------------|-------------------|
| Event ticket | `event_ticket` | `event_ticket` |
| Boarding / flight | `boarding`, `airline` | `boarding` |
| Coupon / offer | `coupon` | `offer` |
| Store / loyalty card | `store_card` | `loyalty` |
| Generic card | `generic` | `generic` |
| Poster generic card (iOS 27+) | `poster_generic` | — |

## HTTP / infrastructure

| Endpoint | Apple | Google |
|----------|:-----:|:------:|
| Device registration web service | PassKit routes | N/A |
| Signed pass download | `/passkit/v1/apple/{id}/download` | N/A |
| Save/remove callbacks | N/A | `/passkit/v1/google/callbacks` (ECv2) |
| Auth on protected routes | `Authorization: ApplePass <secret>` | ECv2 signature verification |

## Package capabilities

| Area | Status |
|------|--------|
| Apple builders (7 types) | Supported |
| Google class/object builders (5 types) | Supported |
| Per-type payload validators | Supported (`django_mobile_pass.validation`) |
| PassKit routes | Supported |
| Google ECv2 callbacks | Supported |
| Custom models, actions, builders | Supported with subclass validation |
| Queue-backed update delivery | Supported via `MOBILE_PASS.queue` |
| Remote Apple images | Supported |
| Signals / events | Supported |

### Notable behaviors

- Associated serials listing is unauthenticated per Apple's spec (device library identifier is the credential); response contains only serial numbers.
- Apple download URLs use HMAC `?signature=` query parameters.
- `google.origins` defaults to `[public_url]` when `origins` is omitted.

### Additional helpers

- `PkPassReader` for inspecting `.pkpass` archives
- `MobilePassQuerySet.apple()` / `.google()` scopes
- Unique constraint on Apple device registrations

## Deferred / out of scope

- Google Smart Tap NFC
- Hosting Google images from local disk (platform limitation)

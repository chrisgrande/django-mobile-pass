---
title: Google Wallet
weight: 30
---

# Google Wallet

Google support includes class builders, object builders, REST API create/patch helpers, Save to Wallet JWTs, ECv2 callback verification, save/remove event storage, and object update notifications.

## How Google Wallet resources fit together

Every issued Google pass has a class and an object. The class is a reusable template for shared data; the object is the individual pass instance. The package stores the created object ID and payload on `MobilePass.content` so later saves can patch the same Google object.

The built-in class resources are:

- `eventTicketClass`
- `flightClass`
- `genericClass`
- `loyaltyClass`
- `offerClass`

The matching object resources are:

- `eventTicketObject`
- `flightObject`
- `genericObject`
- `loyaltyObject`
- `offerObject`

## Save to Wallet links

Users add Google passes through a Save to Wallet URL containing a signed JWT. The package signs that JWT with the configured service account private key. The JWT includes issuer, audience, type, issued-at time, allowed origins, and the object IDs to save.

## Callbacks and events

Google can call `/passkit/v1/google/callbacks` when a pass is saved or removed. The package verifies the callback with **ECv2SigningOnly**, resolves the stored pass by `googleObjectId`, and writes a `GoogleMobilePassEvent` row with event type `save` or `remove`.

Callbacks arrive as JSON bodies with `protocolVersion`, `intermediateSigningKey`, `signature`, and `signedMessage`. The verifier fetches Google root keys, validates the intermediate key and message signature, and decodes the signed claims.

Use `mobile_pass.is_currently_saved_to_google_wallet()` when you need the latest saved/removed state inferred from callback history.

## Operational notes

- Google class images must be public HTTPS URLs because Google fetches and displays them from its own services.
- Demo or review-limited issuer accounts may show test labeling until Google grants publishing access.
- Removing a pass from a user's wallet does not delete the Google object from the Wallet Objects API.
- Class updates can propagate to all linked objects; object updates affect one issued pass.
- Configure a Django cache backend in production so Google root keys are not refetched on every callback.

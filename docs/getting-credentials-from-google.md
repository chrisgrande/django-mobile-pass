---
title: Getting credentials from Google
weight: 5
---

# Getting credentials from Google

Enable Google Wallet API for your issuer account, create a service account, grant it access to the issuer, and store the service account JSON. Set `issuer_id`, `service_account_key_path` or `service_account_key`, and `origins`.

Configure Google to send save/remove callbacks to `/passkit/v1/google/callbacks`. The package verifies callbacks with Google's **ECv2SigningOnly** protocol. It fetches and caches root keys from `https://pay.google.com/gp/m/issuer/keys`, verifies the signed payload against your configured `issuer_id`, and records save/remove events on the matching stored pass.

## What each credential does

- `issuer_id` is the Google Wallet issuer ID. Class and object IDs are built as `{issuer_id}.{suffix}`. Callback verification also includes this value in the signed message.
- `service_account_key_path` or `service_account_key` supplies the Google Cloud service account JSON used for OAuth access tokens and Save to Wallet JWT signing.
- `origins` lists the web origins allowed for Save to Wallet JWT usage. Google requires this claim for web buttons and links.
- `api_base_url` defaults to the Wallet Objects API v1 base URL.

## Class and object model

Google Wallet separates shared pass data from per-user pass data:

- Classes hold common data for a group of passes. Examples: event name, venue, flight route, program name, offer title, logo, background color, and review status.
- Objects hold one issued pass's data. Examples: attendee name, seat, passenger name, account ID, barcode, balance, and redemption code.

Objects reference classes through `classId`. Updating a class changes shared information for all objects linked to it. Updating an object changes one issued pass.

## Issuing flow

Create or patch the class first, create the object, then send the user to a Save to Wallet URL. The URL is `https://pay.google.com/gp/v/save/{jwt}` where the JWT is signed with the service account private key and contains object IDs in its payload.

When a user removes a pass, Google de-links the object from that user's account; it does not delete the object itself. The same object can be saved again later.

References: [Google Wallet classes and objects](https://developers.google.com/wallet/generic/overview/how-classes-objects-work), [creating classes and objects](https://developers.google.com/wallet/generic/use-cases/create), and [Google Wallet JWTs](https://developers.google.com/wallet/generic/use-cases/jwt).

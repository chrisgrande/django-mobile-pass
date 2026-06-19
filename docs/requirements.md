---
title: Requirements
weight: 2
---

# Requirements

- Python 3.11+
- Django 5.2+
- `django.contrib.contenttypes` in `INSTALLED_APPS`
- `cryptography`, `PyJWT`, and `requests`
- A configured Django cache backend for Google ECv2 callback verification in production
- Apple Wallet pass certificate for Apple passes
- Google Wallet issuer account and service account key for Google passes

## Apple infrastructure

Apple Wallet passes are signed archives. A production Apple pass flow needs:

- A Pass Type ID in the Apple Developer portal.
- A pass signing certificate exported as a PKCS#12 `.p12` file.
- A stable `passTypeIdentifier`, `teamIdentifier`, and unique pass `serialNumber`.
- HTTPS hosting for the PassKit web service URL on real devices.
- A long `authenticationToken`/web service secret. Wallet sends it as `Authorization: ApplePass <token>` when it registers, checks for updates, or unregisters a pass.
- Outbound access to Apple Push Notification service when notifying devices that an updated pass is available.

Apple update pushes are notifications, not the updated pass body. After APNs wakes the device, Wallet calls the package's PassKit web service endpoints to ask which serials changed and to download the fresh `.pkpass`.

## Google infrastructure

Google Wallet passes are based on two resources:

- A Passes Class, which acts as the shared template for common fields such as issuer, event name, venue, logo, and review state.
- A Passes Object, which carries per-user details such as seat number, account ID, barcode, balance, or passenger name.

A production Google Wallet flow needs:

- A Google Wallet API issuer account.
- A Google Cloud service account authorized for that issuer.
- A service account JSON key for REST API calls and Save to Wallet JWT signing.
- `origins` configured for the domains that will render Save to Wallet links or buttons.
- Public HTTPS URLs for images used on Google classes.
- Google save/remove callbacks configured to POST ECv2-signed payloads to `/passkit/v1/google/callbacks`.

The package creates/patches classes and objects through the Google Wallet Objects API, then hands the user a signed Save to Wallet JWT URL.

## Request limits

The package rejects request bodies larger than `MOBILE_PASS["max_request_body_bytes"]`, which defaults to 64 KiB. Increase it only if you have a concrete reason; PassKit logs and callbacks should be small.

References: [Apple PassKit](https://developer.apple.com/documentation/passkit), [Apple pass update web service](https://developer.apple.com/documentation/walletpasses/register-a-pass-for-update-notifications), [Google Wallet classes and objects](https://developers.google.com/wallet/generic/overview/how-classes-objects-work), [Google Wallet JWTs](https://developers.google.com/wallet/reference/rest/v1/Jwt).

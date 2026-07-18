---
title: Questions and issues
weight: 90
---

# Questions and issues

## Troubleshooting checklist

1. Inspect the stored `MobilePass.content` JSON and regenerate with `mobile_pass.generate()` for Apple passes.
2. Verify Apple PKCS#12 credentials and Google service account JSON paths.
3. Confirm PassKit routes are mounted and reachable over HTTPS on real devices.
4. Confirm `MOBILE_PASS["google"]["issuer_id"]` is set — Google ECv2 callbacks require it.
5. Configure a Django cache backend so Google root keys are not refetched on every callback.
6. Use public HTTPS URLs for Google class images.

## Common Apple issues

- **PassKit registration fails:** ensure the URL UUID matches `MobilePass.pk`, not only the human-readable `serialNumber` in `pass.json`.
- **Updates never arrive:** check `webservice_host`, `webservice_secret`, and that `push_updates_on_save` is not disabled.
- **Certificate errors:** verify the `.p12` password and that the Pass Type ID matches the certificate.
- **Safari on Mac shows `PKPassKitErrorDomain error 1`:** inspect `pass.json` for invalid dates. `relevantDate`, `expirationDate`, and any field with `dateStyle`/`timeStyle` must use a W3C datetime with a timezone (e.g. `2026-08-01T19:00:00Z`). Also confirm `icon.png` is bundled and the PKCS#12 chain includes Apple's WWDR intermediate.

## Common Google issues

- **Save to Wallet link fails:** check `origins` includes your site URL.
- **Callbacks not recorded:** Google posts ECv2-signed JSON bodies to `/passkit/v1/google/callbacks`; Bearer JWT verification is no longer used.
- **Class images missing:** Google fetches logo and hero URLs from the public internet.

## Operational notes

- Wallet update notifications run synchronously on save by default. Configure `MOBILE_PASS.queue` for async delivery.
- Associated-serials listing requires Apple PassKit authorization.
- Apple download links use HMAC signatures.

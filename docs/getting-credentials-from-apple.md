---
title: Getting credentials from Apple
weight: 4
---

# Getting credentials from Apple

Create a Pass Type ID and pass certificate in the Apple Developer portal. Export the certificate as a `.p12` file and set `MOBILE_PASS["apple"]["certificate_path"]` plus `certificate_password`.

Set `type_identifier` to the Pass Type ID, `team_identifier` to your Apple team ID, and `webservice_secret` to a long random token. Apple sends this token in `Authorization: ApplePass <secret>` for registration, update, and unregister calls.

## What each credential does

- `organization_name` is the human-readable organization name embedded in each pass.
- `type_identifier` is Apple's Pass Type ID. It must match the certificate used to sign the pass.
- `team_identifier` is your Apple Developer Team ID.
- `certificate_path` or `certificate` provides the PKCS#12 pass signing certificate and private key.
- `certificate_password` unlocks the PKCS#12 bundle.
- `webservice_secret` becomes the pass `authenticationToken`; Wallet uses it in the `ApplePass` authorization header.
- `webservice_host` is the public HTTPS host Wallet uses to call your Django PassKit endpoints.
- `apple_push_base_url` defaults to Apple's APNs device endpoint and is used when the package notifies registered devices about updates.

## PassKit web service lifecycle

When a user adds an Apple pass, Wallet can register the device for updates. The package stores the device library identifier, push token, pass type identifier, and pass serial. When your app updates the stored `MobilePass`, the package sends an APNs notification to each registered device. The device then calls the web service to ask for changed serial numbers and downloads the updated `.pkpass`.

The relevant package routes are:

- `POST /passkit/v1/devices/{device_id}/registrations/{pass_type_id}/{pass_serial}` for device registration.
- `GET /passkit/v1/devices/{device_id}/registrations/{pass_type_id}` for serial numbers updated since an optional timestamp.
- `GET /passkit/v1/passes/{pass_type_id}/{pass_serial}` for the latest signed pass archive.
- `DELETE /passkit/v1/devices/{device_id}/registrations/{pass_type_id}/{pass_serial}` to unregister a device/pass pair.
- `POST /passkit/v1/log` for Wallet log messages (no `Authorization` header required).

PassKit authorization rules in Django:

| Endpoint | `Authorization: ApplePass <secret>` required |
|----------|---------------------------------------------|
| Register / unregister device | Yes |
| Check for updates (`GET /passes/...`) | Yes |
| List associated serials | Yes |
| Download signed Apple pass | No — uses `?signature=` query param |
| Wallet logs (`POST /log`) | No |

The `pass_serial` path segment is the `MobilePass.pk` UUID, not necessarily the human-readable `serialNumber` stored in `pass.json`.

See Apple's PassKit web service documentation: [register a pass for update notifications](https://developer.apple.com/documentation/walletpasses/register-a-pass-for-update-notifications), [send an updated pass](https://developer.apple.com/documentation/walletpasses/send-an-updated-pass), and [unregister a pass](https://developer.apple.com/documentation/walletpasses/unregister-a-pass-for-update-notifications).

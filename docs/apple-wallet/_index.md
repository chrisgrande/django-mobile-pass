---
title: Apple Wallet
weight: 20
---

# Apple Wallet

Apple support includes `.pkpass` archive generation, PKCS#7 manifest signing, PassKit web service routes, device registrations, logs, signed downloads, update checks, unregister calls, and APNs update notifications.

## How Apple updates work

Apple Wallet does not receive the full updated pass through APNs. APNs is only the wake-up signal. After your Django app changes a stored pass, the package notifies Apple's push endpoint with the registered device token and pass type topic. The user's device then calls your `webServiceURL` to check which serial numbers changed and downloads the latest `.pkpass`.

This means the public PassKit routes must stay available after a pass is issued. A pass installed on a device can call back days or months later.

## Important pass fields

- `passTypeIdentifier` must match the Pass Type ID tied to your signing certificate.
- `serialNumber` uniquely identifies one issued pass under that pass type.
- `teamIdentifier` identifies your Apple Developer team.
- `authenticationToken` is the shared secret Wallet sends in the `ApplePass` authorization header.
- `webServiceURL` tells Wallet where to register, unregister, list updates, and download the latest pass.
- `changeMessage` controls lock-screen update text when a visible field changes. The builder accepts `:value` and converts it to Apple's `%@` placeholder.

## Operational notes

- Real devices require HTTPS for the web service host.
- Device registrations should be treated as long-lived state.
- A `410` response from APNs means the registration is stale; the package removes it.
- Image files for Apple are packaged into the signed archive. Use local file paths or remote HTTPS URLs with the `set_remote_*_image` builder methods.
- Configure a non-empty `webservice_secret`. The package rejects PassKit registration and update requests when no Apple web service secret is configured.

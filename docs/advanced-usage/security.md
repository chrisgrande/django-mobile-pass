---
title: Security
weight: 57
---

# Security

Keep wallet credentials out of source control. Use environment-backed Django settings for Apple `.p12` material, Google service account JSON, and web service secrets.

## Apple PassKit endpoints

The package requires `Authorization: ApplePass <webservice_secret>` on PassKit endpoints that expose registration state or pass contents. Configure a non-empty `MOBILE_PASS["apple"]["webservice_secret"]`; requests are rejected when it is missing.

Protected routes: device register/unregister and check for updates (get latest pass). The list-registrations endpoint (`GET /passkit/v1/devices/<deviceLibraryIdentifier>/registrations/<passTypeIdentifier>`) is unauthenticated per Apple's PassKit Web Service spec — Wallet does not send an `Authorization` header because the request can span multiple passes with different tokens; the opaque device library identifier acts as the credential, and the response contains only serial numbers (no pass content). The log endpoint and signed Apple download URL also do not use the `ApplePass` header.

Apple pass update routes also verify that the requested serial belongs to an Apple pass and that the URL pass type matches the stored `passTypeIdentifier`.

## Signed downloads

Apple download URLs are signed with Django's signing framework and `SECRET_KEY`. Treat generated links as bearer URLs. Regenerate `SECRET_KEY` only with a migration plan because existing signed links will stop validating.

## Google callbacks

Google callbacks must use the **ECv2SigningOnly** protocol. The package verifies the signed JSON payload against Google root keys and your configured `issuer_id`. Invalid callbacks are rejected without returning parser details to the caller.

Configure a cache backend so root key fetches are not repeated on every request.

## Request limits

`MOBILE_PASS["max_request_body_bytes"]` defaults to 64 KiB. Oversized log, callback, and registration bodies are rejected before parsing.

## Outbound requests

Apple update notifications go to APNs. Google class/object operations go to the Google Wallet Objects API. Google callback verification fetches root keys from `pay.google.com`. Restrict outbound network access at the infrastructure layer if your deployment environment supports egress controls.

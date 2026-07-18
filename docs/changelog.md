---
title: Changelog
weight: 91
---

# Changelog

## Unreleased

- **Fixed**: pass update notifications triggered by saving a `MobilePass` are now deferred with `transaction.on_commit`. Previously the APNs push (or queue task) was dispatched from `post_save` before the surrounding transaction committed, so devices could fetch the pass before the new content was visible (receiving `304 Not Modified` or stale data) or be notified about a change that later rolled back. Outside a transaction the dispatch still runs immediately.

## 0.1.1

- Added migration `0002` for `MobilePass` field choices and renamed Apple/Google indexes so model state matches migrations.
- **Fixed**: PassKit web service routes now resolve `pass_serial` using the `serialNumber` inside `pass.json` (with a primary-key fallback), and Apple passes issued without an explicit serial use the `MobilePass` UUID for both, so device registration and update checks work end to end.
- **Fixed**: `HasMobilePasses` is now an abstract model so its `mobile_passes` generic relation is actually contributed to concrete models. Inherit it directly (`class Order(HasMobilePasses)`) or list it before other bases.
- **Fixed**: APNs update notifications are sent over HTTP/2 via `httpx` (Apple's push API rejects HTTP/1.1 connections). `httpx[http2]` is now a dependency.
- **Fixed**: `If-Modified-Since` handling in the pass update endpoint now truncates microseconds (`Last-Modified` has second precision) and tolerates naive or malformed header values, so devices receive `304 Not Modified` correctly.
- Added `content_object=` support to Apple and Google builder `save()` so passes can be attached to a domain model at creation time.
- `MobilePass.to_response()` accepts an optional `request` argument as documented.
- PassKit views now honor custom `MOBILE_PASS` model overrides (`model`, `apple_registration_model`) instead of hard-coding the defaults.
- The associated-serials endpoint returns the `pass.json` serial numbers devices actually use for follow-up requests.
- Expanded [`AGENTS.md`](../AGENTS.md) with `MobilePass` API, exceptions, `PkPassReader`, and corrected `HasMobilePasses` usage.
- Fixed incorrect `PkPassReader` examples in the testing guide.
- Added documentation drift tests for `PkPassReader` and `HasMobilePasses` APIs.
- Expanded the reading stored passes guide with common fields and related-row helpers.

## Previous

- Added Google Wallet callback verification (`ECv2SigningOnly`).
- Added remote Apple Wallet image support.
- Removed the deprecated Google callback public-key setting from Django settings and documentation.
- Added a Python configuration reference and refreshed README, security, requirements, and image docs.

## Django rewrite

This repository is a Django 5.2+ package with pass builders, storage models, Apple PassKit routes, Google callbacks, signed downloads, and wallet update actions.

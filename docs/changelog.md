---
title: Changelog
weight: 91
---

# Changelog

## Unreleased

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

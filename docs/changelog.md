---
title: Changelog
weight: 91
---

# Changelog

## Unreleased

- Added per-type Apple and Google payload validators (`django_mobile_pass.validation`).
- Added optional queue-backed pass update delivery via `MOBILE_PASS.queue` (Celery or custom callable).
- Added subclass validation for custom models, actions, and builders in `django_mobile_pass.registry`.
- `google.origins` now defaults to `[public_url]` when not set explicitly.
- Added [`AGENTS.md`](../AGENTS.md), [feature matrix](feature-matrix.md), and [agent integration guide](agent-integration.md).

## Previous

- Added Google Wallet callback verification (`ECv2SigningOnly`).
- Added remote Apple Wallet image support.
- Removed the deprecated Google callback public-key setting from Django settings and documentation.
- Added a Python configuration reference and refreshed README, security, requirements, and image docs.

## Django rewrite

This repository is a Django 5.2+ package with pass builders, storage models, Apple PassKit routes, Google callbacks, signed downloads, and wallet update actions.

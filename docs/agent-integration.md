---
title: Agent integration guide
weight: 3
---

# Agent integration guide

This page is written for **AI coding agents** (Cursor, Codex, etc.) that need to add wallet passes to a Django application without reading the entire codebase.

The canonical agent instructions live in [`AGENTS.md`](../AGENTS.md) at the repository root. This document expands on integration patterns.

## Decision tree

```
Need a wallet pass?
├── Apple devices only → use django_mobile_pass.apple.builders
├── Google devices only → use django_mobile_pass.google.builders
└── Both → create one MobilePass per platform (or two builders saving separate rows)
```

## Step-by-step: add Apple Wallet to an existing Django app

1. Add `django_mobile_pass` to `INSTALLED_APPS` and run migrations.
2. Obtain Apple Pass Type ID certificate (`.p12`) — see [Getting credentials from Apple](getting-credentials-from-apple.md).
3. Configure `MOBILE_PASS` with Apple keys and `public_url`.
4. Include `django_mobile_pass.urls` in root `urlpatterns`.
5. In your business logic, call a builder's `.save()` and return `download_response()` or `add_to_wallet_url(request)`.

## Step-by-step: add Google Wallet

1. Complete steps 1 and 4 above (shared infrastructure).
2. Create a Google Cloud service account with Wallet Objects API access — see [Getting credentials from Google](getting-credentials-from-google.md).
3. Configure `MOBILE_PASS.google` with `issuer_id`, service account key, and `origins`.
4. Create a **class** once (`LoyaltyPassClass.make("suffix").save()`), then create **objects** per user with the matching builder.
5. Redirect users to `mobile_pass.add_to_wallet_url()` or `mobile_pass.to_response(request)`.

## Updating passes in production

| Platform | Pattern |
|----------|---------|
| Apple | `mobile_pass.update_field("gate", "B12", change_message="Gate changed to :value")` |
| Google | Mutate `mobile_pass.content["googleObjectPayload"]`, then `mobile_pass.save()` |
| Either | Set `push_updates_on_save: True` (default) so wallets refresh automatically |

For high-volume updates, set `MOBILE_PASS.queue.backend` to `"celery"` and register the task documented in [Configuration](configuration.md#queue-backed-updates).

## Files agents should not modify

- `django_mobile_pass/migrations/0001_initial.py` — unless intentionally shipping a new migration

## Files agents commonly extend

| File | When |
|------|------|
| `myapp/builders.py` | Custom pass layout or branding |
| `myapp/wallet_actions.py` | Audit logging around register/notify/callback actions |
| `myapp/models.py` | `HasMobilePasses` on orders, tickets, memberships |
| Project `settings.py` | `MOBILE_PASS` credentials and overrides |

## Verify integration

```bash
pytest tests/test_apple.py tests/test_google.py
```

Manually test:

1. Apple — download `.pkpass`, open on iOS, confirm add-to-wallet.
2. Google — open save URL in Chrome/Android, confirm save callback row in `GoogleMobilePassEvent`.
3. Update pass content, save, confirm device receives update (Apple) or Google object reflects change.

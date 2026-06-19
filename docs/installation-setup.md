---
title: Installation and setup
weight: 3
---

# Installation and setup

Install the package and add the Django app:

```bash
pip install -e .
python manage.py migrate
```

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django_mobile_pass",
]

from django.urls import include, path

urlpatterns = [
    path("", include("django_mobile_pass.urls")),
]
```

Configure credentials in `settings.py`:

```python
MOBILE_PASS = {
    "public_url": "https://example.com",
    "apple": {
        "organization_name": "Example Inc",
        "type_identifier": "pass.com.example.tickets",
        "team_identifier": "ABCDE12345",
        "certificate_path": BASE_DIR / "certs/pass.p12",
        "certificate_password": "secret",
        "webservice_secret": "at-least-16-characters",
        "webservice_host": "https://example.com",
    },
    "google": {
        "issuer_id": "3388000000022791700",
        "service_account_key_path": BASE_DIR / "certs/google.json",
        "origins": ["https://example.com"],
    },
}
```

See [Configuration reference](configuration.md) for every available `MOBILE_PASS` option, custom model paths, action overrides, and builder registration.

## Credentials

- [Getting credentials from Apple](getting-credentials-from-apple.md)
- [Getting credentials from Google](getting-credentials-from-google.md)

## Next steps

1. Create your first pass in [Generating your first pass](basic-usage/generating-your-first-pass.md).
2. Return it from a view in [Handing out passes](basic-usage/handing-out-passes.md).
3. Enable update notifications by keeping `push_updates_on_save` enabled and exposing the built-in PassKit routes.

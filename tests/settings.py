SECRET_KEY = "test-secret"
ROOT_URLCONF = "django_mobile_pass.urls"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django_mobile_pass",
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

MOBILE_PASS = {
    "public_url": "https://wallet.example.test",
    "push_updates_on_save": False,
    "apple": {
        "organization_name": "Example Org",
        "type_identifier": "pass.example.test",
        "team_identifier": "TEAM12345",
        "webservice_secret": "1234567890123456",
        "webservice_host": "https://wallet.example.test",
        "apple_push_base_url": "https://example.com",
    },
    "google": {
        "issuer_id": "issuer",
        "origins": ["https://wallet.example.test"],
    },
}


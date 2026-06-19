from __future__ import annotations

import time

from django.core.cache import cache

from django_mobile_pass.settings import get_mobile_pass_settings


class GoogleCredentials:
    @classmethod
    def key_info(cls) -> dict:
        return get_mobile_pass_settings().google.key_info()

    @classmethod
    def private_key(cls) -> str:
        return get_mobile_pass_settings().google.private_key

    @classmethod
    def client_email(cls) -> str:
        return get_mobile_pass_settings().google.client_email

    @classmethod
    def issuer_id(cls) -> str:
        return str(get_mobile_pass_settings().google.issuer_id)


class GoogleJwtSigner:
    TOKEN_CACHE_KEY = "django_mobile_pass.google.access_token"
    SCOPE = "https://www.googleapis.com/auth/wallet_object.issuer"

    def sign_save_url_jwt(self, payload: dict) -> str:
        import jwt

        claims = {
            "iss": GoogleCredentials.client_email(),
            "aud": "google",
            "typ": "savetowallet",
            "iat": int(time.time()),
            "origins": get_mobile_pass_settings().google.origins or [],
            "payload": payload,
        }
        return jwt.encode(claims, GoogleCredentials.private_key(), algorithm="RS256")

    def access_token(self) -> str:
        import requests

        cached = cache.get(self.TOKEN_CACHE_KEY)
        if cached:
            return str(cached)

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self._sign_assertion_jwt(),
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        token = str(payload["access_token"])
        ttl = max(60, int(payload.get("expires_in", 3600)) - 30)
        cache.set(self.TOKEN_CACHE_KEY, token, ttl)
        return token

    def _sign_assertion_jwt(self) -> str:
        import jwt

        now = int(time.time())
        claims = {
            "iss": GoogleCredentials.client_email(),
            "scope": self.SCOPE,
            "aud": "https://oauth2.googleapis.com/token",
            "iat": now,
            "exp": now + 3600,
        }
        return jwt.encode(claims, GoogleCredentials.private_key(), algorithm="RS256")

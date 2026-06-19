import time
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase

from django_mobile_pass.apple.entities import AppleImage
from django_mobile_pass.enums import PassType, Platform
from django_mobile_pass.google.callback_verification import (
    PROTOCOL_VERSION,
    ROOT_KEYS_CACHE_KEY,
    GoogleCallbackVerificationError,
    build_signed_string,
    verify_and_decode,
)
from django_mobile_pass.models import MobilePass
from tests.fixtures.google_ecv2 import (
    build_ecv2_callback_payload,
    ecv2_intermediate_keypair,
    ecv2_root_keypair,
    ecv2_stale_root_keypair,
    root_keys_response,
)

ISSUER_ID = "issuer"


class GoogleCallbackVerificationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = ecv2_root_keypair()
        self.intermediate = ecv2_intermediate_keypair()

    def _build_valid_payload(self, message_overrides=None, intermediate_expiration_ms=None):
        return build_ecv2_callback_payload(
            root_private_pem=self.root["private"],
            intermediate_private_pem=self.intermediate["private"],
            intermediate_public_base64=self.intermediate["public_base64"],
            issuer_id=ISSUER_ID,
            message={"eventType": "save", "objectId": "issuer.ticket-1", **(message_overrides or {})},
            intermediate_expiration_ms=intermediate_expiration_ms,
        )

    def _fake_root_keys(self, mock_get, root_public_base64=None):
        mock_get.return_value.json.return_value = root_keys_response(
            root_public_base64 or self.root["public_base64"]
        )
        mock_get.return_value.ok = True

    def test_build_signed_string_uses_little_endian_length_prefixes(self):
        signed = build_signed_string(["ab", "cdef"])
        self.assertEqual(signed, b"\x02\x00\x00\x00ab\x04\x00\x00\x00cdef")

    def test_remote_apple_image_does_not_require_local_files(self):
        image = AppleImage.make_remote("https://example.com/logo.png")
        self.assertTrue(image.is_remote)

    def test_verify_and_decode_accepts_correctly_signed_payload(self):
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            claims = verify_and_decode(self._build_valid_payload(), ISSUER_ID)

        self.assertEqual(claims["eventType"], "save")
        self.assertEqual(claims["objectId"], "issuer.ticket-1")

    def test_google_callback_rejects_signed_payload_with_unsupported_protocol_version(self):
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            payload = self._build_valid_payload()
            payload["protocolVersion"] = "ECv1"
            response = Client().post(
                "/passkit/v1/google/callbacks",
                data=payload,
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 403)

    def test_verify_and_decode_rejects_tampered_signed_message(self):
        payload = self._build_valid_payload()
        payload["signedMessage"] = '{"eventType":"save","objectId":"tampered"}'

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(payload, ISSUER_ID)

        self.assertIn("Message signature failed verification", str(context.exception))

    def test_verify_and_decode_rejects_expired_intermediate_signing_key(self):
        expired_ms = int(round((time.time() - 60) * 1000))
        payload = self._build_valid_payload(intermediate_expiration_ms=expired_ms)

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(payload, ISSUER_ID)

        self.assertIn("Intermediate signing key has expired", str(context.exception))

    def test_verify_and_decode_rejects_wrong_issuer_id(self):
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(self._build_valid_payload(), "9999999999999999999")

        self.assertIn("Message signature failed verification", str(context.exception))

    def test_verify_and_decode_rejects_missing_intermediate_signing_key(self):
        payload = self._build_valid_payload()
        del payload["intermediateSigningKey"]

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(payload, ISSUER_ID)

        self.assertIn("Missing intermediateSigningKey", str(context.exception))

    def test_verify_and_decode_caches_root_keys_after_first_verification(self):
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            verify_and_decode(self._build_valid_payload(), ISSUER_ID)
            verify_and_decode(self._build_valid_payload({"objectId": "issuer.ticket-2"}), ISSUER_ID)

        self.assertEqual(mock_get.call_count, 1)
        self.assertIsNotNone(cache.get(ROOT_KEYS_CACHE_KEY))

    def test_verify_and_decode_does_not_refetch_when_cached_keys_fail_verification(self):
        stale = ecv2_stale_root_keypair()
        cache.set(ROOT_KEYS_CACHE_KEY, root_keys_response(stale["public_base64"])["keys"], 3600)

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            with self.assertRaises(GoogleCallbackVerificationError):
                verify_and_decode(self._build_valid_payload(), ISSUER_ID)

        mock_get.assert_not_called()

    def test_verify_and_decode_keeps_cached_keys_when_forged_payload_arrives(self):
        cache.set(ROOT_KEYS_CACHE_KEY, root_keys_response(self.root["public_base64"])["keys"], 3600)
        payload = self._build_valid_payload()
        payload["signedMessage"] = '{"eventType":"save","objectId":"forged"}'

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            with self.assertRaises(GoogleCallbackVerificationError):
                verify_and_decode(payload, ISSUER_ID)

        mock_get.assert_not_called()
        self.assertIsNotNone(cache.get(ROOT_KEYS_CACHE_KEY))

    def test_verify_and_decode_raises_when_root_keys_cannot_be_fetched(self):
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            mock_get.return_value.ok = False
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(self._build_valid_payload(), ISSUER_ID)

        self.assertIn("Failed to fetch Google root keys", str(context.exception))

    def test_verify_and_decode_skips_expired_root_keys(self):
        expired_ms = int(round(time.time() * 1000) - 1000)
        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = root_keys_response(
                self.root["public_base64"],
                root_expiration_ms=expired_ms,
            )
            with self.assertRaises(GoogleCallbackVerificationError) as context:
                verify_and_decode(self._build_valid_payload(), ISSUER_ID)

        self.assertIn("No usable Google root keys available", str(context.exception))

    def test_google_callback_rejects_unsupported_protocol_version(self):
        client = Client()
        response = client.post(
            "/passkit/v1/google/callbacks",
            data={"protocolVersion": "legacy"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_google_callback_accepts_verified_ecv2_payload_end_to_end(self):
        MobilePass.objects.create(
            type=PassType.EVENT_TICKET,
            platform=Platform.GOOGLE,
            builder_name="event_ticket",
            content={"googleObjectId": "issuer.ticket-1"},
            images={},
        )

        with patch("django_mobile_pass.google.callback_verification.requests.get") as mock_get:
            self._fake_root_keys(mock_get)
            client = Client()
            response = client.post(
                "/passkit/v1/google/callbacks",
                data=self._build_valid_payload(),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 204)

    @patch("django_mobile_pass.google.callback_verification.fetch_root_keys_from_google")
    def test_verify_and_decode_requires_usable_root_keys(self, fetch_keys):
        fetch_keys.return_value = [{"protocolVersion": "legacy"}]
        with self.assertRaises(GoogleCallbackVerificationError):
            verify_and_decode({"protocolVersion": PROTOCOL_VERSION}, ISSUER_ID)

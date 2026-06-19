from unittest.mock import patch

from django.test import TestCase

from django_mobile_pass.apple.entities import AppleImage
from django_mobile_pass.apple.pkpass import _image_bytes, build_pkpass
from django_mobile_pass.settings import AppleSettings


class RemoteAppleImageTests(TestCase):
    @patch("requests.get")
    def test_image_bytes_fetches_remote_images(self, requests_get):
        class FakeResponse:
            content = b"png-bytes"
            ok = True

            def raise_for_status(self):
                return None

        requests_get.return_value = FakeResponse()

        image = AppleImage.make_remote("https://example.com/logo.png")
        self.assertEqual(_image_bytes(image, image.x1_path), b"png-bytes")
        requests_get.assert_called_once_with("https://example.com/logo.png", timeout=30)

    @patch("django_mobile_pass.apple.pkpass.sign_manifest", return_value=b"signature")
    @patch("requests.get")
    def test_build_pkpass_includes_remote_image_files(self, requests_get, _sign_manifest):
        class FakeResponse:
            content = b"png-bytes"
            ok = True

            def raise_for_status(self):
                return None

        requests_get.return_value = FakeResponse()

        images = {"logo": AppleImage.make_remote("https://example.com/logo.png")}
        archive = build_pkpass({"description": "Test"}, images, AppleSettings())

        self.assertIn(b"logo.png", archive)
        requests_get.assert_called_once_with("https://example.com/logo.png", timeout=30)

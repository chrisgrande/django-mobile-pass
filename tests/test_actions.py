from unittest.mock import MagicMock, patch

from django.test import TestCase

from django_mobile_pass.actions import NotifyAppleOfPassUpdateAction
from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.exceptions import AppleWalletRequestFailed
from django_mobile_pass.models import AppleMobilePassDevice, AppleMobilePassRegistration


class NotifyAppleOfPassUpdateActionTests(TestCase):
    def setUp(self):
        self.mobile_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save()
        )
        self.action = NotifyAppleOfPassUpdateAction()

    def _create_registration(self, device_id: str, push_token: str) -> AppleMobilePassRegistration:
        device = AppleMobilePassDevice.objects.create(id=device_id, push_token=push_token)
        return AppleMobilePassRegistration.objects.create(
            device=device,
            pass_type_id="pass.example.test",
            mobile_pass=self.mobile_pass,
        )

    @staticmethod
    def _apns_client(client_cls, response):
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = response
        return client

    @staticmethod
    def _apns_response(status_code=200, is_success=True, payload=None):
        return MagicMock(status_code=status_code, is_success=is_success, json=lambda: payload or {})

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_sends_push_notification_to_apple_over_http2(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        registration = self._create_registration("device-1", "push-token-1")
        client = self._apns_client(client_cls, self._apns_response())

        self.action.execute(self.mobile_pass)

        client_cls.assert_called_once_with(
            http2=True,
            cert=certificate_file.return_value.name,
            timeout=30,
        )
        client.post.assert_called_once_with(
            registration.apple_update_url(),
            headers={"apns-topic": registration.pass_type_id},
            json={},
        )

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_sends_empty_json_body(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        self._create_registration("device-1", "push-token-1")
        client = self._apns_client(client_cls, self._apns_response())

        self.action.execute(self.mobile_pass)

        self.assertEqual(client.post.call_args.kwargs["json"], {})

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_sends_pass_type_id_as_apns_topic(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        registration = self._create_registration("device-1", "push-token-1")
        client = self._apns_client(client_cls, self._apns_response())

        self.action.execute(self.mobile_pass)

        self.assertEqual(client.post.call_args.kwargs["headers"]["apns-topic"], registration.pass_type_id)

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_notifies_every_registration(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        self._create_registration("device-1", "push-token-1")
        self._create_registration("device-2", "push-token-2")
        self._create_registration("device-3", "push-token-3")
        client = self._apns_client(client_cls, self._apns_response())

        self.action.execute(self.mobile_pass)

        self.assertEqual(client.post.call_count, 3)

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_deletes_registration_when_apple_returns_410(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        self._create_registration("device-1", "push-token-1")
        self._apns_client(client_cls, self._apns_response(status_code=410, is_success=False))

        self.action.execute(self.mobile_pass)

        self.assertEqual(AppleMobilePassRegistration.objects.count(), 0)

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_raises_apple_wallet_request_failed_on_other_errors(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        self._create_registration("device-1", "push-token-1")
        self._apns_client(
            client_cls,
            self._apns_response(status_code=400, is_success=False, payload={"reason": "BadDeviceToken"}),
        )

        with self.assertRaises(AppleWalletRequestFailed):
            self.action.execute(self.mobile_pass)

    @patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
    @patch("httpx.Client")
    def test_exception_carries_status_and_endpoint(self, client_cls, certificate_file):
        certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
        self._create_registration("device-1", "push-token-1")
        self._apns_client(
            client_cls,
            self._apns_response(status_code=429, is_success=False, payload={"reason": "TooManyRequests"}),
        )

        with self.assertRaises(AppleWalletRequestFailed) as context:
            self.action.execute(self.mobile_pass)

        self.assertEqual(context.exception.status, 429)
        self.assertIn("https://example.com/push-token-1", str(context.exception))

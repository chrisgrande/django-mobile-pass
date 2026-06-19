from unittest.mock import patch

from django.test import Client, TestCase

from django_mobile_pass.apple.builders import EventTicketPassBuilder, GenericPassBuilder
from django_mobile_pass.enums import PassType, Platform
from django_mobile_pass.models import AppleMobilePassRegistration
from django_mobile_pass.models import MobilePass


class AppleBuilderTests(TestCase):
    def test_event_ticket_serializes_back_fields_but_generic_does_not(self):
        event_payload = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .add_back_field("terms", "No refunds")
            .data()
        )
        generic_payload = (
            GenericPassBuilder.make()
            .set_description("Generic")
            .add_field("member", "Ada")
            .add_back_field("terms", "No refunds")
            .data()
        )

        self.assertEqual(event_payload["eventTicket"]["backFields"][0]["key"], "terms")
        self.assertNotIn("backFields", generic_payload["generic"])


class ApplePasskitRouteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.mobile_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save()
        )
        self.registration_url = (
            f"/passkit/v1/devices/device-1/registrations/pass.example.test/{self.mobile_pass.pk}"
        )
        self.auth = {"HTTP_AUTHORIZATION": "ApplePass 1234567890123456"}

    def test_register_list_and_unregister_device_use_same_passkit_path(self):
        register_response = self.client.post(
            self.registration_url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(AppleMobilePassRegistration.objects.count(), 1)

        list_response = self.client.get("/passkit/v1/devices/device-1/registrations/pass.example.test", **self.auth)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["serialNumbers"], [str(self.mobile_pass.pk)])

        unregister_response = self.client.delete(self.registration_url, **self.auth)
        self.assertEqual(unregister_response.status_code, 204)
        self.assertEqual(AppleMobilePassRegistration.objects.count(), 0)

    def test_register_rejects_missing_applepass_authorization(self):
        response = self.client.post(
            self.registration_url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_register_rejects_empty_push_token(self):
        response = self.client.post(
            self.registration_url,
            data={"pushToken": ""},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 400)

    def test_associated_serials_requires_applepass_authorization(self):
        response = self.client.get("/passkit/v1/devices/device-1/registrations/pass.example.test")

        self.assertEqual(response.status_code, 403)

    def test_pass_type_mismatch_is_not_downloadable_via_update_endpoint(self):
        response = self.client.get(
            f"/passkit/v1/passes/pass.other/{self.mobile_pass.pk}",
            **self.auth,
        )

        self.assertEqual(response.status_code, 404)

    def test_passkit_registration_rejects_google_pass_serial(self):
        google_pass = MobilePass.objects.create(
            type=PassType.EVENT_TICKET,
            platform=Platform.GOOGLE,
            builder_name="event_ticket",
            content={"googleObjectId": "issuer.ticket-1"},
            images={},
        )

        response = self.client.post(
            f"/passkit/v1/devices/device-1/registrations/pass.example.test/{google_pass.pk}",
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 404)

    def test_signed_download_rejects_bad_signature_before_generating_pass(self):
        response = self.client.get(
            f"/passkit/v1/apple/{self.mobile_pass.pk}/download?signature=bad"
        )

        self.assertEqual(response.status_code, 403)

    def test_log_endpoint_rejects_oversized_payload(self):
        response = self.client.post(
            "/passkit/v1/log",
            data=b"x" * 70000,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 413)

    def test_mobile_pass_reports_whether_it_was_updated_after_a_timestamp(self):
        self.assertTrue(self.mobile_pass.was_updated_after(None))
        self.assertFalse(self.mobile_pass.was_updated_after(self.mobile_pass.updated_at))

    def test_register_existing_device_returns_200(self):
        self.client.post(
            self.registration_url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )
        response = self.client.post(
            self.registration_url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)

    def test_check_for_updates_returns_pkpass(self):
        with patch("django_mobile_pass.apple.builders.build_pkpass", return_value=b"PKPASS"):
            response = self.client.get(
                f"/passkit/v1/passes/pass.example.test/{self.mobile_pass.pk}",
                **self.auth,
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.apple.pkpass")
        self.assertIn("Last-Modified", response)

    def test_check_for_updates_honors_if_modified_since(self):
        url = f"/passkit/v1/passes/pass.example.test/{self.mobile_pass.pk}"
        with patch("django_mobile_pass.apple.builders.build_pkpass", return_value=b"PKPASS"):
            response = self.client.get(
                url,
                HTTP_IF_MODIFIED_SINCE="Wed, 01 Jan 2099 00:00:00 GMT",
                **self.auth,
            )
        self.assertEqual(response.status_code, 304)

    def test_associated_serials_filters_by_passes_updated_since(self):
        self.client.post(
            self.registration_url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )
        response = self.client.get(
            "/passkit/v1/devices/device-1/registrations/pass.example.test?passesUpdatedSince=2099-01-01T00:00:00Z",
            **self.auth,
        )
        self.assertEqual(response.status_code, 204)

    def test_signed_download_returns_pkpass_for_valid_signature(self):
        from django_mobile_pass.utils import sign_value

        signature = sign_value(str(self.mobile_pass.pk))
        with patch("django_mobile_pass.apple.builders.build_pkpass", return_value=b"PKPASS"):
            response = self.client.get(
                f"/passkit/v1/apple/{self.mobile_pass.pk}/download?signature={signature}"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"PKPASS")

    def test_signed_download_returns_404_for_missing_pass(self):
        from uuid import uuid4

        from django_mobile_pass.utils import sign_value

        missing_id = uuid4()
        signature = sign_value(str(missing_id))
        response = self.client.get(f"/passkit/v1/apple/{missing_id}/download?signature={signature}")
        self.assertEqual(response.status_code, 404)

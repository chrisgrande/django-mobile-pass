from unittest.mock import patch

from django.test import TestCase

from django_mobile_pass.actions import HandleGoogleCallbackAction, NotifyGoogleOfPassUpdateAction
from django_mobile_pass.enums import BarcodeType, PassType, Platform
from django_mobile_pass.google.builders import EventTicketPassBuilder, EventTicketPassClass
from django_mobile_pass.models import GoogleMobilePassEvent, MobilePass


class GoogleBuilderTests(TestCase):
    @patch("django_mobile_pass.google.builders.GoogleWalletClient.insert_object", return_value={})
    def test_google_object_save_creates_mobile_pass_record(self, insert_object):
        mobile_pass = (
            EventTicketPassBuilder.make()
            .set_class("concert")
            .set_object_suffix("ticket-1")
            .set_attendee_name("Ada Lovelace")
            .set_barcode(BarcodeType.QR, "TICKET-1")
            .save()
        )

        self.assertEqual(mobile_pass.platform, Platform.GOOGLE)
        self.assertEqual(mobile_pass.content["googleObjectId"], "issuer.ticket-1")
        self.assertEqual(mobile_pass.content["googleClassId"], "issuer.concert")
        self.assertEqual(mobile_pass.content["googleObjectPayload"]["barcode"]["type"], "QR_CODE")
        insert_object.assert_called_once()

    def test_google_class_payload_contains_class_id(self):
        pass_class = EventTicketPassClass.make("concert").set_event_name("Launch")
        payload = pass_class.compile_data()

        self.assertEqual(pass_class.get_event_name(), "Launch")
        self.assertEqual(payload["eventName"]["defaultValue"]["value"], "Launch")


class GoogleCallbackTests(TestCase):
    def test_google_callback_action_records_save_and_remove_events(self):
        mobile_pass = MobilePass.objects.create(
            type=PassType.EVENT_TICKET,
            platform=Platform.GOOGLE,
            builder_name="event_ticket",
            content={"googleObjectId": "issuer.ticket-1"},
            images={},
        )

        HandleGoogleCallbackAction().execute({"objectId": "issuer.ticket-1", "eventType": "save"})
        self.assertTrue(mobile_pass.is_currently_saved_to_google_wallet())

        HandleGoogleCallbackAction().execute({"objectId": "issuer.ticket-1", "eventType": "del"})
        self.assertEqual(GoogleMobilePassEvent.objects.count(), 2)
        mobile_pass.refresh_from_db()
        self.assertFalse(mobile_pass.is_currently_saved_to_google_wallet())

    def test_notify_google_patches_stored_object_payload(self):
        mobile_pass = MobilePass.objects.create(
            type=PassType.EVENT_TICKET,
            platform=Platform.GOOGLE,
            builder_name="event_ticket",
            content={
                "googleClassType": "eventTicketClass",
                "googleObjectId": "issuer.ticket-1",
                "googleObjectPayload": {"state": "ACTIVE"},
            },
            images={},
        )

        with patch("django_mobile_pass.actions.GoogleWalletClient.patch_object", return_value={}) as patch_object:
            NotifyGoogleOfPassUpdateAction().execute(mobile_pass)

        patch_object.assert_called_once_with("eventTicketObject", "issuer.ticket-1", {"state": "ACTIVE"})

from unittest.mock import patch

from django.test import TestCase

from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.enums import PassType, Platform
from django_mobile_pass.models import MobilePass
from tests.models import Customer


class HasMobilePassesTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(email="ada@example.test")

    def _google_pass(self) -> MobilePass:
        return MobilePass.objects.create(
            type=PassType.EVENT_TICKET,
            platform=Platform.GOOGLE,
            builder_name="event_ticket",
            content={"googleObjectId": "issuer.ticket-1"},
            images={},
        )

    def test_generic_relation_is_contributed_to_concrete_models(self):
        private_fields = [field.name for field in Customer._meta.private_fields]
        self.assertIn("mobile_passes", private_fields)

    def test_add_mobile_pass_attaches_and_filters_by_platform(self):
        apple_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save()
        )
        google_pass = self._google_pass()

        self.customer.add_mobile_pass(apple_pass)
        self.customer.add_mobile_pass(google_pass)

        self.assertEqual(self.customer.mobile_passes.count(), 2)
        self.assertEqual(list(self.customer.apple_passes()), [apple_pass])
        self.assertEqual(list(self.customer.google_passes()), [google_pass])
        self.assertEqual(self.customer.first_apple_pass(), apple_pass)
        self.assertEqual(self.customer.first_google_pass(), google_pass)
        self.assertEqual(self.customer.first_mobile_pass(pass_type=PassType.EVENT_TICKET, platform=Platform.APPLE), apple_pass)

    def test_first_pass_helpers_return_none_when_nothing_attached(self):
        self.assertIsNone(self.customer.first_apple_pass())
        self.assertIsNone(self.customer.first_google_pass())

    def test_apple_builder_save_accepts_content_object(self):
        mobile_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save(content_object=self.customer)
        )

        self.assertEqual(mobile_pass.content_object, self.customer)
        self.assertEqual(self.customer.first_apple_pass(), mobile_pass)

    def test_google_builder_save_accepts_content_object(self):
        from django_mobile_pass.google.builders import EventTicketPassBuilder as GoogleEventTicketPassBuilder

        with patch("django_mobile_pass.google.builders.GoogleWalletClient.insert_object", return_value={}):
            mobile_pass = (
                GoogleEventTicketPassBuilder.make()
                .set_class("concert")
                .set_object_suffix("ticket-1")
                .save(content_object=self.customer)
            )

        self.assertEqual(mobile_pass.content_object, self.customer)
        self.assertEqual(self.customer.first_google_pass(), mobile_pass)

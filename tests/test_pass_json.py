from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from django.test import SimpleTestCase, TestCase, override_settings

from django_mobile_pass.apple.builders import EventTicketPassBuilder
from django_mobile_pass.apple.entities import FieldContent
from django_mobile_pass.enums import DataDetectorType, DateType, TimeStyleType
from django_mobile_pass.exceptions import InvalidPass
from django_mobile_pass.utils import ensure_w3c_datetime, isoformat
from django_mobile_pass.validation.apple import EventTicketApplePassValidator


class IsoformatTests(SimpleTestCase):
    def test_naive_datetime_is_treated_as_utc_with_z_suffix(self):
        self.assertEqual(isoformat(datetime(2026, 8, 1, 19, 0)), "2026-08-01T19:00:00Z")

    def test_aware_utc_datetime_uses_z_suffix(self):
        value = datetime(2026, 8, 1, 19, 0, tzinfo=timezone.utc)
        self.assertEqual(isoformat(value), "2026-08-01T19:00:00Z")

    def test_offset_timezone_is_preserved(self):
        value = datetime(2026, 8, 1, 19, 0, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(isoformat(value), "2026-08-01T19:00:00-05:00")

    def test_microseconds_are_stripped(self):
        value = datetime(2026, 8, 1, 19, 0, 0, 123456, tzinfo=timezone.utc)
        self.assertEqual(isoformat(value), "2026-08-01T19:00:00Z")

    def test_ensure_w3c_datetime_adds_timezone_to_naive_iso_string(self):
        self.assertEqual(ensure_w3c_datetime("2026-08-01T19:00:00"), "2026-08-01T19:00:00Z")

    def test_ensure_w3c_datetime_expands_bare_dates(self):
        self.assertEqual(ensure_w3c_datetime("2026-08-01"), "2026-08-01T00:00:00Z")

    def test_ensure_w3c_datetime_leaves_plain_text_alone(self):
        self.assertEqual(ensure_w3c_datetime("Main Stage"), "Main Stage")


class PassJsonValidityTests(TestCase):
    def test_relevant_date_includes_timezone(self):
        payload = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .set_relevant_date(datetime(2026, 8, 1, 19, 0))
            .data()
        )

        self.assertEqual(payload["relevantDate"], "2026-08-01T19:00:00Z")
        EventTicketApplePassValidator().validate(payload)

    def test_date_styled_field_normalizes_naive_value_and_pairs_styles(self):
        payload = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .add_header_field(
                "date",
                "2026-08-01T19:00:00",
                date_style=DateType.MEDIUM,
                time_style=TimeStyleType.SHORT,
            )
            .data()
        )

        field = payload["eventTicket"]["headerFields"][0]
        self.assertEqual(field["value"], "2026-08-01T19:00:00Z")
        self.assertEqual(field["dateStyle"], DateType.MEDIUM.value)
        self.assertEqual(field["timeStyle"], TimeStyleType.SHORT.value)
        EventTicketApplePassValidator().validate(payload)

    def test_date_style_alone_defaults_time_style_none(self):
        field = FieldContent(key="date", value="2026-08-01T19:00:00").using_date_type(DateType.SHORT)
        serialized = field.to_dict()

        self.assertEqual(serialized["dateStyle"], DateType.SHORT.value)
        self.assertEqual(serialized["timeStyle"], TimeStyleType.NONE.value)
        self.assertEqual(serialized["value"], "2026-08-01T19:00:00Z")

    def test_data_detector_types_is_an_array(self):
        field = FieldContent(key="phone", value="555-0100").as_data_type(DataDetectorType.PHONE_NUMBER)
        serialized = field.to_dict()

        self.assertEqual(serialized["dataDetectorTypes"], [DataDetectorType.PHONE_NUMBER.value])

        hydrated = FieldContent.from_dict(serialized)
        self.assertEqual(hydrated.data_detector_type, DataDetectorType.PHONE_NUMBER)

    def test_authentication_token_omitted_without_webservice_url(self):
        mobile_pass_settings = {
            "public_url": "https://wallet.example.test",
            "push_updates_on_save": False,
            "apple": {
                "organization_name": "Example Org",
                "type_identifier": "pass.example.test",
                "team_identifier": "TEAM12345",
                "webservice_secret": "1234567890123456",
                "webservice_host": None,
            },
            "google": {
                "issuer_id": "issuer",
                "origins": ["https://wallet.example.test"],
            },
        }

        with override_settings(MOBILE_PASS=mobile_pass_settings, APP_URL="http://localhost"):
            payload = (
                EventTicketPassBuilder.make()
                .set_description("Event")
                .add_field("event", "Launch")
                .data()
            )

        self.assertNotIn("webServiceURL", payload)
        self.assertNotIn("authenticationToken", payload)

    def test_expire_writes_w3c_expiration_date(self):
        mobile_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save()
        )

        mobile_pass.expire()
        expiration = mobile_pass.content["expirationDate"]
        self.assertTrue(expiration.endswith("Z") or "+" in expiration or expiration.count("-") >= 3)
        self.assertNotIn(".", expiration.split("T", 1)[1].rstrip("Z"))
        EventTicketApplePassValidator().validate(mobile_pass.content)

    def test_validator_rejects_relevant_date_without_timezone(self):
        payload = {
            "description": "Event",
            "formatVersion": 1,
            "organizationName": "Example",
            "passTypeIdentifier": "pass.example.test",
            "serialNumber": "ABC",
            "teamIdentifier": "TEAM12345",
            "relevantDate": "2026-08-01T19:00:00",
            "eventTicket": {"primaryFields": [{"key": "event", "value": "Launch"}]},
        }

        with self.assertRaises(InvalidPass) as ctx:
            EventTicketApplePassValidator().validate(payload)
        self.assertIn("relevantDate", str(ctx.exception))


class PkPassArchiveTests(SimpleTestCase):
    @patch("django_mobile_pass.apple.pkpass.sign_manifest", return_value=b"signature")
    def test_pkpass_files_are_stored_uncompressed(self, _sign):
        from django_mobile_pass.apple.pkpass import build_pkpass
        from django_mobile_pass.settings import AppleSettings

        settings = AppleSettings(
            organization_name="Example",
            type_identifier="pass.example.test",
            team_identifier="TEAM12345",
            certificate=b"unused",
            certificate_password="",
            webservice_secret="1234567890123456",
            webservice_host="https://wallet.example.test",
        )

        archive_bytes = build_pkpass(
            {
                "formatVersion": 1,
                "description": "Event",
                "organizationName": "Example",
                "passTypeIdentifier": "pass.example.test",
                "serialNumber": "1",
                "teamIdentifier": "TEAM12345",
            },
            {},
            settings,
        )

        with ZipFile(BytesIO(archive_bytes)) as archive:
            for info in archive.infolist():
                self.assertEqual(info.compress_type, 0, f"{info.filename} should be ZIP_STORED")

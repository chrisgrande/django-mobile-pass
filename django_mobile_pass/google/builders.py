from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from django.apps import apps

from django_mobile_pass.apple.entities import Barcode
from django_mobile_pass.enums import BarcodeType, PassType, Platform
from django_mobile_pass.exceptions import GoogleWalletRequestFailed, InvalidPass
from django_mobile_pass.google.auth import GoogleCredentials
from django_mobile_pass.google.client import GoogleWalletClient
from django_mobile_pass.google.entities import GoogleImage, LocalizedString
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.utils import build_wifi_uri, filter_empty, isoformat, new_suffix
from django_mobile_pass.validation.google import (
    BoardingClassValidator,
    BoardingObjectValidator,
    EventTicketClassValidator,
    EventTicketObjectValidator,
    GenericClassValidator,
    GenericObjectValidator,
    GooglePassClassValidator,
    GooglePassObjectValidator,
    LoyaltyClassValidator,
    LoyaltyObjectValidator,
    OfferClassValidator,
    OfferObjectValidator,
)

if TYPE_CHECKING:
    from django_mobile_pass.models import MobilePass


class GooglePassBuilder:
    type: PassType
    class_resource: str
    object_resource: str

    def __init__(self):
        self.class_suffix: str | None = None
        self.object_suffix: str | None = None
        self.barcode: Barcode | None = None
        self.state = "ACTIVE"

    @classmethod
    def make(cls) -> "GooglePassBuilder":
        return cls()

    @classmethod
    def name(cls) -> str:
        base = cls.__name__.removesuffix("PassBuilder")
        return re.sub(r"(?<!^)(?=[A-Z])", "_", base).lower()

    @classmethod
    def platform(cls) -> Platform:
        return Platform.GOOGLE

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        raise NotImplementedError(f"{cls.__name__} must implement validator_class().")

    def set_class(self, suffix: str) -> "GooglePassBuilder":
        self.class_suffix = suffix
        return self

    def set_object_suffix(self, suffix: str) -> "GooglePassBuilder":
        self.object_suffix = suffix
        return self

    def set_barcode(self, format: BarcodeType, message: str, alt_text: str | None = None) -> "GooglePassBuilder":
        barcode = Barcode(format=format, message=message)
        if alt_text is not None:
            barcode.with_alt_text(alt_text)
        self.barcode = barcode
        return self

    def set_wifi_barcode(
        self, ssid: str, password: str | None = None, hidden: bool = False, alt_text: str | None = None
    ) -> "GooglePassBuilder":
        return self.set_barcode(BarcodeType.QR, build_wifi_uri(ssid, password, hidden), alt_text or ssid)

    def object_id(self) -> str:
        self.object_suffix = self.object_suffix or new_suffix()
        return f"{GoogleCredentials.issuer_id()}.{self.object_suffix}"

    def class_id(self) -> str:
        if not self.class_suffix:
            raise InvalidPass("Call set_class() before saving a Google pass.")
        return f"{GoogleCredentials.issuer_id()}.{self.class_suffix}"

    def save(self) -> "MobilePass":
        payload = self.compile_google_object_payload()
        self.validate_payload(payload)
        GoogleWalletClient().insert_object(self.object_resource, self.object_id(), payload)

        model_class = self._mobile_pass_model()
        return model_class.objects.create(
            type=self.type,
            platform=Platform.GOOGLE,
            builder_name=self.name(),
            content={
                "googleClassType": self.class_resource,
                "googleObjectId": self.object_id(),
                "googleClassId": self.class_id(),
                "googleObjectPayload": payload,
            },
            images={},
        )

    def compile_google_object_payload(self) -> dict:
        return filter_empty(
            {
                "id": self.object_id(),
                "classId": self.class_id(),
                "state": self.state,
                "barcode": self.compile_barcode(),
            }
            | self.compile_data()
        )

    def compile_barcode(self) -> dict | None:
        if not self.barcode:
            return None
        return filter_empty(
            {
                "type": self.translate_barcode_type(self.barcode.format),
                "value": self.barcode.message,
                "alternateText": self.barcode.alt_text,
            }
        )

    @staticmethod
    def translate_barcode_type(value: BarcodeType) -> str:
        mapping = {
            BarcodeType.QR: "QR_CODE",
            BarcodeType.PDF417: "PDF_417",
            BarcodeType.AZTEC: "AZTEC",
            BarcodeType.CODE128: "CODE_128",
        }
        return mapping[value]

    def compile_data(self) -> dict:
        raise NotImplementedError

    def validate_payload(self, payload: dict) -> None:
        self.validator_class()().validate(payload)

    @staticmethod
    def _mobile_pass_model():
        app_label, model_name = get_mobile_pass_settings().model.split(".")
        return apps.get_model(app_label, model_name)


class GooglePassClass:
    resource_name: str

    def __init__(self, suffix: str):
        self.suffix = suffix
        self.review_status = "UNDER_REVIEW"
        self.issuer_name: str | None = None
        self.background_color: str | None = None

    @classmethod
    def make(cls, suffix: str) -> "GooglePassClass":
        return cls(suffix)

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        raise NotImplementedError(f"{cls.__name__} must implement validator_class().")

    def set_issuer_name(self, issuer_name: str) -> "GooglePassClass":
        self.issuer_name = issuer_name
        return self

    def set_background_color(self, hex_value: str) -> "GooglePassClass":
        self.background_color = hex_value
        return self

    def id(self) -> str:
        return f"{GoogleCredentials.issuer_id()}.{self.suffix}"

    def save(self) -> "GooglePassClass":
        payload = self.compile_data() | {"id": self.id()}
        self.validate_payload(payload)
        GoogleWalletClient().insert_class(self.resource_name, self.id(), payload)
        return self

    def retire(self) -> "GooglePassClass":
        GoogleWalletClient().patch_class(self.resource_name, self.id(), {"reviewStatus": "REJECTED"})
        self.review_status = "REJECTED"
        return self

    @classmethod
    def all(cls) -> list["GooglePassClass"]:
        payloads = GoogleWalletClient().list_classes(cls.resource_name)
        return [cls.hydrate(payload) for payload in payloads]

    @classmethod
    def find(cls, suffix: str) -> "GooglePassClass | None":
        try:
            payload = GoogleWalletClient().get_class(cls.resource_name, f"{GoogleCredentials.issuer_id()}.{suffix}")
        except GoogleWalletRequestFailed as exc:
            if exc.status == 404:
                return None
            raise
        return cls.hydrate(payload)

    @classmethod
    def hydrate(cls, payload: dict) -> "GooglePassClass":
        instance = cls(payload["id"].split(".", 1)[1])
        instance.apply_hydrated_payload(payload)
        return instance

    def compile_data(self) -> dict:
        raise NotImplementedError

    def apply_hydrated_payload(self, payload: dict) -> None:
        self.issuer_name = payload.get("issuerName")
        self.review_status = payload.get("reviewStatus", self.review_status)
        self.background_color = payload.get("hexBackgroundColor")

    def validate_payload(self, payload: dict) -> None:
        self.validator_class()().validate(payload)

    @staticmethod
    def hydrate_image(payload: dict, key: str) -> GoogleImage | None:
        uri = payload.get(key, {}).get("sourceUri", {}).get("uri")
        return GoogleImage.from_url(uri) if uri else None

    @staticmethod
    def hydrate_localized_string(payload: dict, key: str) -> LocalizedString | None:
        data = payload.get(key, {})
        default = data.get("defaultValue", {})
        value = default.get("value")
        if value is None:
            return None
        language = default.get("language", "en-US")
        localized = LocalizedString.of(value, language)
        for translation in data.get("translatedValues", []):
            localized.add_translation(translation["language"], translation["value"])
        return localized


class EventTicketPassBuilder(GooglePassBuilder):
    type = PassType.EVENT_TICKET
    class_resource = "eventTicketClass"
    object_resource = "eventTicketObject"

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        return EventTicketObjectValidator

    def __init__(self):
        super().__init__()
        self.attendee_name: str | None = None
        self.section: str | None = None
        self.row: str | None = None
        self.seat: str | None = None

    def set_attendee_name(self, value: str) -> "EventTicketPassBuilder":
        self.attendee_name = value
        return self

    def set_section(self, value: str) -> "EventTicketPassBuilder":
        self.section = value
        return self

    def set_row(self, value: str) -> "EventTicketPassBuilder":
        self.row = value
        return self

    def set_seat(self, value: str) -> "EventTicketPassBuilder":
        self.seat = value
        return self

    def compile_data(self) -> dict:
        seat_info = filter_empty({"section": self.section, "row": self.row, "seat": self.seat})
        return filter_empty({"ticketHolderName": self.attendee_name, "seatInfo": seat_info})


class BoardingPassBuilder(GooglePassBuilder):
    type = PassType.BOARDING_PASS
    class_resource = "flightClass"
    object_resource = "flightObject"

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        return BoardingObjectValidator

    def __init__(self):
        super().__init__()
        self.passenger_name: str | None = None
        self.seat_number: str | None = None
        self.confirmation_code: str | None = None

    def set_passenger_name(self, value: str) -> "BoardingPassBuilder":
        self.passenger_name = value
        return self

    def set_seat_number(self, value: str) -> "BoardingPassBuilder":
        self.seat_number = value
        return self

    def set_confirmation_code(self, value: str) -> "BoardingPassBuilder":
        self.confirmation_code = value
        return self

    def compile_data(self) -> dict:
        return filter_empty(
            {
                "passengerName": self.passenger_name,
                "boardingAndSeatingInfo": filter_empty({"seatNumber": self.seat_number}),
                "reservationInfo": filter_empty({"confirmationCode": self.confirmation_code}),
            }
        )


class GenericPassBuilder(GooglePassBuilder):
    type = PassType.GENERIC
    class_resource = "genericClass"
    object_resource = "genericObject"

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        return GenericObjectValidator

    def __init__(self):
        super().__init__()
        self.header: LocalizedString | None = None
        self.card_title: LocalizedString | None = None
        self.subheader: LocalizedString | None = None
        self.expiry_notification_enabled: bool | None = None

    def set_header(self, value: str, language: str = "en-US") -> "GenericPassBuilder":
        self.header = LocalizedString.of(value, language)
        return self

    def set_card_title(self, value: str, language: str = "en-US") -> "GenericPassBuilder":
        self.card_title = LocalizedString.of(value, language)
        return self

    def set_subheader(self, value: str, language: str = "en-US") -> "GenericPassBuilder":
        self.subheader = LocalizedString.of(value, language)
        return self

    def set_expiry_notification_enabled(self, enabled: bool) -> "GenericPassBuilder":
        self.expiry_notification_enabled = enabled
        return self

    def compile_data(self) -> dict:
        notifications = None
        if self.expiry_notification_enabled is not None:
            notifications = {"expiryNotification": {"enableNotification": self.expiry_notification_enabled}}
        return filter_empty(
            {
                "header": self.header.to_dict() if self.header else None,
                "cardTitle": self.card_title.to_dict() if self.card_title else None,
                "subheader": self.subheader.to_dict() if self.subheader else None,
                "notifications": notifications,
            }
        )


class LoyaltyPassBuilder(GooglePassBuilder):
    type = PassType.STORE_CARD
    class_resource = "loyaltyClass"
    object_resource = "loyaltyObject"

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        return LoyaltyObjectValidator

    def __init__(self):
        super().__init__()
        self.account_id: str | None = None
        self.account_name: str | None = None
        self.balance_micros: int | None = None
        self.balance_string: str | None = None

    def set_account_id(self, value: str) -> "LoyaltyPassBuilder":
        self.account_id = value
        return self

    def set_account_name(self, value: str) -> "LoyaltyPassBuilder":
        self.account_name = value
        return self

    def set_balance_micros(self, value: int) -> "LoyaltyPassBuilder":
        self.balance_micros = value
        return self

    def set_balance_string(self, value: str) -> "LoyaltyPassBuilder":
        self.balance_string = value
        return self

    def compile_data(self) -> dict:
        balance = filter_empty({"micros": self.balance_micros, "string": self.balance_string})
        loyalty_points = filter_empty({"balance": balance})
        return filter_empty(
            {
                "accountId": self.account_id,
                "accountName": self.account_name,
                "loyaltyPoints": loyalty_points,
            }
        )


class OfferPassBuilder(GooglePassBuilder):
    type = PassType.COUPON
    class_resource = "offerClass"
    object_resource = "offerObject"

    @classmethod
    def validator_class(cls) -> type[GooglePassObjectValidator]:
        return OfferObjectValidator

    def __init__(self):
        super().__init__()
        self.title: str | None = None
        self.redemption_code: str | None = None

    def set_title(self, value: str) -> "OfferPassBuilder":
        self.title = value
        return self

    def set_redemption_code(self, value: str) -> "OfferPassBuilder":
        self.redemption_code = value
        return self

    def compile_data(self) -> dict:
        return filter_empty({"title": self.title, "redemptionCode": self.redemption_code})


class EventTicketPassClass(GooglePassClass):
    resource_name = "eventTicketClass"

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        return EventTicketClassValidator

    def __init__(self, suffix: str):
        super().__init__(suffix)
        self.event_name: LocalizedString | None = None
        self.venue_name: LocalizedString | None = None
        self.venue_address: LocalizedString | None = None
        self.start_date: datetime | None = None
        self.logo: GoogleImage | None = None
        self.hero: GoogleImage | None = None

    def set_event_name(self, value: str, language: str = "en-US") -> "EventTicketPassClass":
        self.event_name = LocalizedString.of(value, language)
        return self

    def get_event_name(self) -> str | None:
        return self.event_name.default_value if self.event_name else None

    def set_venue_name(self, value: str, language: str = "en-US") -> "EventTicketPassClass":
        self.venue_name = LocalizedString.of(value, language)
        return self

    def set_venue_address(self, value: str, language: str = "en-US") -> "EventTicketPassClass":
        self.venue_address = LocalizedString.of(value, language)
        return self

    def set_start_date(self, value: datetime) -> "EventTicketPassClass":
        self.start_date = value
        return self

    def set_logo_url(self, url: str) -> "EventTicketPassClass":
        self.logo = GoogleImage.from_url(url)
        return self

    def set_hero_image_url(self, url: str) -> "EventTicketPassClass":
        self.hero = GoogleImage.from_url(url)
        return self

    def compile_data(self) -> dict:
        venue = filter_empty(
            {
                "name": self.venue_name.to_dict() if self.venue_name else None,
                "address": self.venue_address.to_dict() if self.venue_address else None,
            }
        )
        return filter_empty(
            {
                "issuerName": self.issuer_name,
                "eventName": self.event_name.to_dict() if self.event_name else None,
                "venue": venue,
                "dateTime": {"start": isoformat(self.start_date)} if self.start_date else None,
                "logo": self.logo.to_dict() if self.logo else None,
                "heroImage": self.hero.to_dict() if self.hero else None,
                "hexBackgroundColor": self.background_color,
                "reviewStatus": self.review_status,
            }
        )

    def apply_hydrated_payload(self, payload: dict) -> None:
        super().apply_hydrated_payload(payload)
        self.event_name = self.hydrate_localized_string(payload, "eventName")
        self.venue_name = self.hydrate_localized_string(payload.get("venue", {}), "name")
        self.venue_address = self.hydrate_localized_string(payload.get("venue", {}), "address")
        self.start_date = (
            datetime.fromisoformat(payload["dateTime"]["start"].replace("Z", "+00:00"))
            if payload.get("dateTime", {}).get("start")
            else None
        )
        self.logo = self.hydrate_image(payload, "logo")
        self.hero = self.hydrate_image(payload, "heroImage")


class BoardingPassClass(GooglePassClass):
    resource_name = "flightClass"

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        return BoardingClassValidator

    def __init__(self, suffix: str):
        super().__init__(suffix)
        self.local_scheduled_departure_datetime: datetime | None = None
        self.airline_code: str | None = None
        self.flight_number: str | None = None
        self.origin_airport_code: str | None = None
        self.destination_airport_code: str | None = None
        self.logo: GoogleImage | None = None
        self.hero: GoogleImage | None = None

    def set_local_scheduled_departure_datetime(self, value: datetime) -> "BoardingPassClass":
        self.local_scheduled_departure_datetime = value
        return self

    def set_airline_code(self, value: str) -> "BoardingPassClass":
        self.airline_code = value
        return self

    def set_flight_number(self, value: str) -> "BoardingPassClass":
        self.flight_number = value
        return self

    def get_flight_number(self) -> str | None:
        return self.flight_number

    def set_origin_airport_code(self, value: str) -> "BoardingPassClass":
        self.origin_airport_code = value
        return self

    def set_destination_airport_code(self, value: str) -> "BoardingPassClass":
        self.destination_airport_code = value
        return self

    def set_logo_url(self, url: str) -> "BoardingPassClass":
        self.logo = GoogleImage.from_url(url)
        return self

    def set_hero_image_url(self, url: str) -> "BoardingPassClass":
        self.hero = GoogleImage.from_url(url)
        return self

    def compile_data(self) -> dict:
        return filter_empty(
            {
                "issuerName": self.issuer_name,
                "localScheduledDepartureDateTime": isoformat(self.local_scheduled_departure_datetime),
                "flightHeader": filter_empty(
                    {
                        "carrier": {"airlineCode": self.airline_code} if self.airline_code else None,
                        "flightNumber": self.flight_number,
                    }
                ),
                "origin": {"airportIataCode": self.origin_airport_code} if self.origin_airport_code else None,
                "destination": {"airportIataCode": self.destination_airport_code}
                if self.destination_airport_code
                else None,
                "logo": self.logo.to_dict() if self.logo else None,
                "heroImage": self.hero.to_dict() if self.hero else None,
                "hexBackgroundColor": self.background_color,
                "reviewStatus": self.review_status,
            }
        )

    def apply_hydrated_payload(self, payload: dict) -> None:
        super().apply_hydrated_payload(payload)
        self.local_scheduled_departure_datetime = (
            datetime.fromisoformat(payload["localScheduledDepartureDateTime"].replace("Z", "+00:00"))
            if payload.get("localScheduledDepartureDateTime")
            else None
        )
        self.airline_code = payload.get("flightHeader", {}).get("carrier", {}).get("airlineCode")
        self.flight_number = payload.get("flightHeader", {}).get("flightNumber")
        self.origin_airport_code = payload.get("origin", {}).get("airportIataCode")
        self.destination_airport_code = payload.get("destination", {}).get("airportIataCode")
        self.logo = self.hydrate_image(payload, "logo")
        self.hero = self.hydrate_image(payload, "heroImage")


class GenericPassClass(GooglePassClass):
    resource_name = "genericClass"

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        return GenericClassValidator

    def __init__(self, suffix: str):
        super().__init__(suffix)
        self.card_title: LocalizedString | None = None
        self.subheader: LocalizedString | None = None
        self.header: LocalizedString | None = None
        self.logo: GoogleImage | None = None
        self.hero: GoogleImage | None = None

    def set_card_title(self, value: str, language: str = "en-US") -> "GenericPassClass":
        self.card_title = LocalizedString.of(value, language)
        return self

    def get_card_title(self) -> str | None:
        return self.card_title.default_value if self.card_title else None

    def set_subheader(self, value: str, language: str = "en-US") -> "GenericPassClass":
        self.subheader = LocalizedString.of(value, language)
        return self

    def set_header(self, value: str, language: str = "en-US") -> "GenericPassClass":
        self.header = LocalizedString.of(value, language)
        return self

    def set_logo_url(self, url: str) -> "GenericPassClass":
        self.logo = GoogleImage.from_url(url)
        return self

    def set_hero_image_url(self, url: str) -> "GenericPassClass":
        self.hero = GoogleImage.from_url(url)
        return self

    def compile_data(self) -> dict:
        return filter_empty(
            {
                "issuerName": self.issuer_name,
                "cardTitle": self.card_title.to_dict() if self.card_title else None,
                "subheader": self.subheader.to_dict() if self.subheader else None,
                "header": self.header.to_dict() if self.header else None,
                "hexBackgroundColor": self.background_color,
                "logo": self.logo.to_dict() if self.logo else None,
                "heroImage": self.hero.to_dict() if self.hero else None,
                "reviewStatus": self.review_status,
            }
        )

    def apply_hydrated_payload(self, payload: dict) -> None:
        super().apply_hydrated_payload(payload)
        self.card_title = self.hydrate_localized_string(payload, "cardTitle")
        self.subheader = self.hydrate_localized_string(payload, "subheader")
        self.header = self.hydrate_localized_string(payload, "header")
        self.logo = self.hydrate_image(payload, "logo")
        self.hero = self.hydrate_image(payload, "heroImage")


class LoyaltyPassClass(GooglePassClass):
    resource_name = "loyaltyClass"

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        return LoyaltyClassValidator

    def __init__(self, suffix: str):
        super().__init__(suffix)
        self.program_name: str | None = None
        self.program_logo: GoogleImage | None = None
        self.rewards_tier: str | None = None
        self.rewards_tier_label: str | None = None
        self.account_name_label: str | None = None
        self.account_id_label: str | None = None

    def set_program_name(self, value: str) -> "LoyaltyPassClass":
        self.program_name = value
        return self

    def get_program_name(self) -> str | None:
        return self.program_name

    def set_program_logo_url(self, url: str) -> "LoyaltyPassClass":
        self.program_logo = GoogleImage.from_url(url)
        return self

    def set_rewards_tier(self, value: str) -> "LoyaltyPassClass":
        self.rewards_tier = value
        return self

    def set_rewards_tier_label(self, value: str) -> "LoyaltyPassClass":
        self.rewards_tier_label = value
        return self

    def set_account_name_label(self, value: str) -> "LoyaltyPassClass":
        self.account_name_label = value
        return self

    def set_account_id_label(self, value: str) -> "LoyaltyPassClass":
        self.account_id_label = value
        return self

    def compile_data(self) -> dict:
        return filter_empty(
            {
                "issuerName": self.issuer_name,
                "programName": self.program_name,
                "programLogo": self.program_logo.to_dict() if self.program_logo else None,
                "rewardsTier": self.rewards_tier,
                "rewardsTierLabel": self.rewards_tier_label,
                "accountNameLabel": self.account_name_label,
                "accountIdLabel": self.account_id_label,
                "hexBackgroundColor": self.background_color,
                "reviewStatus": self.review_status,
            }
        )

    def apply_hydrated_payload(self, payload: dict) -> None:
        super().apply_hydrated_payload(payload)
        self.program_name = payload.get("programName")
        self.program_logo = self.hydrate_image(payload, "programLogo")
        self.rewards_tier = payload.get("rewardsTier")
        self.rewards_tier_label = payload.get("rewardsTierLabel")
        self.account_name_label = payload.get("accountNameLabel")
        self.account_id_label = payload.get("accountIdLabel")


class OfferPassClass(GooglePassClass):
    resource_name = "offerClass"

    @classmethod
    def validator_class(cls) -> type[GooglePassClassValidator]:
        return OfferClassValidator

    def __init__(self, suffix: str):
        super().__init__(suffix)
        self.title: str | None = None
        self.redemption_channel: str | None = None
        self.provider: str | None = None
        self.details: str | None = None
        self.fine_print: str | None = None
        self.logo: GoogleImage | None = None

    def set_title(self, value: str) -> "OfferPassClass":
        self.title = value
        return self

    def get_title(self) -> str | None:
        return self.title

    def set_redemption_channel(self, value: str) -> "OfferPassClass":
        self.redemption_channel = value
        return self

    def set_provider(self, value: str) -> "OfferPassClass":
        self.provider = value
        return self

    def set_details(self, value: str) -> "OfferPassClass":
        self.details = value
        return self

    def set_fine_print(self, value: str) -> "OfferPassClass":
        self.fine_print = value
        return self

    def set_logo_url(self, url: str) -> "OfferPassClass":
        self.logo = GoogleImage.from_url(url)
        return self

    def compile_data(self) -> dict:
        return filter_empty(
            {
                "issuerName": self.issuer_name,
                "title": self.title,
                "redemptionChannel": self.redemption_channel,
                "provider": self.provider,
                "details": self.details,
                "finePrint": self.fine_print,
                "logo": self.logo.to_dict() if self.logo else None,
                "hexBackgroundColor": self.background_color,
                "reviewStatus": self.review_status,
            }
        )

    def apply_hydrated_payload(self, payload: dict) -> None:
        super().apply_hydrated_payload(payload)
        self.title = payload.get("title")
        self.redemption_channel = payload.get("redemptionChannel")
        self.provider = payload.get("provider")
        self.details = payload.get("details")
        self.fine_print = payload.get("finePrint")
        self.logo = self.hydrate_image(payload, "logo")

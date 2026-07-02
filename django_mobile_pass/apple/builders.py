from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from django.apps import apps
from django.conf import settings as django_settings

from django_mobile_pass.apple.entities import (
    AppleImage,
    Barcode,
    Color,
    FieldContent,
    Location,
    NfcPayload,
    PersonName,
    Price,
    Seat,
    WifiNetwork,
)
from django_mobile_pass.apple.pkpass import build_pkpass
from django_mobile_pass.enums import BarcodeType, DateType, FieldType, PassType, Platform, TimeStyleType, TransitType
from django_mobile_pass.exceptions import InvalidConfig, InvalidPass
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.utils import build_wifi_uri, filter_empty, headline, isoformat, new_suffix
from django_mobile_pass.validation.apple import (
    ApplePassValidator,
    BoardingApplePassValidator,
    CouponApplePassValidator,
    EventTicketApplePassValidator,
    GenericApplePassValidator,
    StoreCardApplePassValidator,
)

if TYPE_CHECKING:
    from django_mobile_pass.models import MobilePass


class ApplePassBuilder:
    type: PassType
    include_back_fields = False

    def __init__(self, payload: dict | None = None, images: dict | None = None, model: "MobilePass | None" = None):
        self.model = model
        self._payload = payload or {}
        self.images: dict[str, AppleImage] = {}
        self.serial_number: str | None = None
        self.organization_name: str | None = None
        self.description: str | None = None
        self.background_color: Color | None = None
        self.foreground_color: Color | None = None
        self.label_color: Color | None = None
        self.download_name: str | None = getattr(model, "download_name", None)
        self.barcode: Barcode | None = None
        self.relevant_date: datetime | None = None
        self.locations: list[Location] = []
        self.max_distance: int | None = None
        self.nfc: NfcPayload | None = None
        self.total_price: Price | None = None
        self.wifi_details: list[WifiNetwork] = []
        self.primary_fields: dict[str, FieldContent] = {}
        self.secondary_fields: dict[str, FieldContent] = {}
        self.auxiliary_fields: dict[str, FieldContent] = {}
        self.header_fields: dict[str, FieldContent] = {}
        self.back_fields: dict[str, FieldContent] = {}

        self._hydrate_images(images or {})
        if payload:
            self._uncompile_content(payload)

    @classmethod
    def make(cls) -> "ApplePassBuilder":
        return cls()

    @classmethod
    def hydrate(cls, model: "MobilePass") -> "ApplePassBuilder":
        return cls(model.content, model.images, model=model)

    @classmethod
    def name(cls) -> str:
        base = cls.__name__.removesuffix("PassBuilder")
        return re.sub(r"(?<!^)(?=[A-Z])", "_", base).lower()

    @classmethod
    def platform(cls) -> Platform:
        return Platform.APPLE

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        raise NotImplementedError(f"{cls.__name__} must implement validator_class().")

    def set_download_name(self, download_name: str) -> "ApplePassBuilder":
        self.download_name = download_name
        return self

    def set_logo_image(self, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "ApplePassBuilder":
        self.images["logo"] = AppleImage(x1_path, x2_path, x3_path)
        return self

    def set_icon_image(self, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "ApplePassBuilder":
        self.images["icon"] = AppleImage(x1_path, x2_path, x3_path)
        return self

    def set_strip_image(self, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "ApplePassBuilder":
        self.images["strip"] = AppleImage(x1_path, x2_path, x3_path)
        return self

    def set_thumbnail_image(self, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "ApplePassBuilder":
        self.images["thumbnail"] = AppleImage(x1_path, x2_path, x3_path)
        return self

    def set_remote_logo_image(self, x1_url: str, x2_url: str | None = None, x3_url: str | None = None) -> "ApplePassBuilder":
        self.images["logo"] = AppleImage.make_remote(x1_url, x2_url, x3_url)
        return self

    def set_remote_icon_image(self, x1_url: str, x2_url: str | None = None, x3_url: str | None = None) -> "ApplePassBuilder":
        self.images["icon"] = AppleImage.make_remote(x1_url, x2_url, x3_url)
        return self

    def set_remote_strip_image(self, x1_url: str, x2_url: str | None = None, x3_url: str | None = None) -> "ApplePassBuilder":
        self.images["strip"] = AppleImage.make_remote(x1_url, x2_url, x3_url)
        return self

    def set_remote_thumbnail_image(self, x1_url: str, x2_url: str | None = None, x3_url: str | None = None) -> "ApplePassBuilder":
        self.images["thumbnail"] = AppleImage.make_remote(x1_url, x2_url, x3_url)
        return self

    def add_header_field(
        self,
        key: str,
        value: str,
        label: str | None = None,
        change_message: str | None = None,
        date_style: DateType | None = None,
        time_style: TimeStyleType | None = None,
        show_date_as_relative: bool | None = None,
    ) -> "ApplePassBuilder":
        return self.add_field(key, value, FieldType.HEADER, label, change_message, date_style, time_style, show_date_as_relative)

    def add_secondary_field(
        self,
        key: str,
        value: str,
        label: str | None = None,
        change_message: str | None = None,
        date_style: DateType | None = None,
        time_style: TimeStyleType | None = None,
        show_date_as_relative: bool | None = None,
    ) -> "ApplePassBuilder":
        return self.add_field(
            key, value, FieldType.SECONDARY, label, change_message, date_style, time_style, show_date_as_relative
        )

    def add_auxiliary_field(
        self,
        key: str,
        value: str,
        label: str | None = None,
        change_message: str | None = None,
        date_style: DateType | None = None,
        time_style: TimeStyleType | None = None,
        show_date_as_relative: bool | None = None,
    ) -> "ApplePassBuilder":
        return self.add_field(
            key, value, FieldType.AUXILIARY, label, change_message, date_style, time_style, show_date_as_relative
        )

    def add_back_field(
        self,
        key: str,
        value: str,
        label: str | None = None,
        change_message: str | None = None,
        date_style: DateType | None = None,
        time_style: TimeStyleType | None = None,
        show_date_as_relative: bool | None = None,
    ) -> "ApplePassBuilder":
        return self.add_field(key, value, FieldType.BACK, label, change_message, date_style, time_style, show_date_as_relative)

    def add_field(
        self,
        key: str,
        value: str,
        field_type: FieldType = FieldType.PRIMARY,
        label: str | None = None,
        change_message: str | None = None,
        date_style: DateType | None = None,
        time_style: TimeStyleType | None = None,
        show_date_as_relative: bool | None = None,
    ) -> "ApplePassBuilder":
        field = FieldContent(key=key).with_value(value).with_label(label or headline(key))
        if change_message is not None:
            field.show_message_when_changed(change_message)
        if date_style is not None:
            field.using_date_type(date_style)
        if time_style is not None:
            field.using_time_type(time_style)
        if show_date_as_relative:
            field.show_date_as_relative()

        self._field_bucket(field_type)[key] = field
        return self

    def update_field(
        self, key: str, value: str, change_message: str | None = None, label: str | None = None
    ) -> "ApplePassBuilder":
        for bucket in self._all_field_buckets():
            if key not in bucket:
                continue
            bucket[key].with_value(value)
            if change_message is not None:
                bucket[key].show_message_when_changed(change_message)
            if label is not None:
                bucket[key].with_label(label)
        return self

    def set_serial_number(self, serial_number: str) -> "ApplePassBuilder":
        self.serial_number = serial_number
        return self

    def set_organization_name(self, organization_name: str) -> "ApplePassBuilder":
        self.organization_name = organization_name
        return self

    def set_description(self, description: str) -> "ApplePassBuilder":
        self.description = description
        return self

    def set_background_color(self, hex_value: str) -> "ApplePassBuilder":
        self.background_color = Color.from_hex(hex_value)
        return self

    def set_foreground_color(self, hex_value: str) -> "ApplePassBuilder":
        self.foreground_color = Color.from_hex(hex_value)
        return self

    def set_label_color(self, hex_value: str) -> "ApplePassBuilder":
        self.label_color = Color.from_hex(hex_value)
        return self

    def set_total_price(self, total_price: Price) -> "ApplePassBuilder":
        self.total_price = total_price
        return self

    def add_wifi_network(self, ssid: str, password: str) -> "ApplePassBuilder":
        self.wifi_details.append(WifiNetwork(ssid=ssid, password=password))
        return self

    def set_barcode(self, format: BarcodeType, message: str, alt_text: str | None = None) -> "ApplePassBuilder":
        barcode = Barcode(format=format, message=message)
        if alt_text is not None:
            barcode.with_alt_text(alt_text)
        self.barcode = barcode
        return self

    def set_wifi_barcode(
        self, ssid: str, password: str | None = None, hidden: bool = False, alt_text: str | None = None
    ) -> "ApplePassBuilder":
        return self.set_barcode(BarcodeType.QR, build_wifi_uri(ssid, password, hidden), alt_text or ssid)

    def set_relevant_date(self, value: datetime) -> "ApplePassBuilder":
        self.relevant_date = value
        return self

    def add_location(
        self, latitude: float, longitude: float, altitude: float | None = None, relevant_text: str | None = None
    ) -> "ApplePassBuilder":
        self.locations.append(Location(latitude=latitude, longitude=longitude, altitude=altitude, relevant_text=relevant_text))
        return self

    def set_max_distance(self, meters: int) -> "ApplePassBuilder":
        self.max_distance = meters
        return self

    def set_nfc(
        self, message: str, encryption_public_key: str, requires_authentication: bool = False
    ) -> "ApplePassBuilder":
        self.nfc = NfcPayload(message=message, encryption_public_key=encryption_public_key, requires_authentication=requires_authentication)
        return self

    def data(self) -> dict:
        config = get_mobile_pass_settings().apple
        if not self.organization_name and config.organization_name:
            self.organization_name = config.organization_name
        if not self.serial_number:
            self.serial_number = new_suffix()

        payload = self._compile_data()
        self._validate_payload(payload)
        return payload

    def generate(self) -> bytes:
        return build_pkpass(self.data(), self.images, get_mobile_pass_settings().apple)

    def save(self, content_object=None) -> "MobilePass":
        model_class = self._mobile_pass_model()

        # Apple Wallet calls the PassKit web service with the serialNumber from
        # pass.json, so the default serial must resolve back to the stored row.
        if self.model is None and not self.serial_number:
            self.serial_number = str(uuid4())

        payload = self.data()
        image_payload = {name: image.to_dict() for name, image in self.images.items()}

        if self.model:
            self.model.content = payload
            self.model.images = image_payload
            self.model.download_name = self.download_name
            self.model.platform = Platform.APPLE
            self.model.builder_name = self.name()
            self.model.type = self.type
            update_fields = ["content", "images", "download_name", "platform", "builder_name", "type", "updated_at"]
            if content_object is not None:
                self.model.content_object = content_object
                update_fields += ["content_type", "object_id"]
            self.model.save(update_fields=update_fields)
            return self.model

        create_kwargs = {
            "type": self.type,
            "platform": Platform.APPLE,
            "builder_name": self.name(),
            "content": payload,
            "images": image_payload,
            "download_name": self.download_name,
        }
        if content_object is not None:
            create_kwargs["content_object"] = content_object
        try:
            create_kwargs["id"] = UUID(str(self.serial_number))
        except ValueError:
            pass

        self.model = model_class.objects.create(**create_kwargs)
        return self.model

    def _compile_data(self) -> dict:
        config = get_mobile_pass_settings().apple
        barcode = self.barcode.to_dict() if self.barcode else None
        compiled = filter_empty(
            {
                "formatVersion": 1,
                "organizationName": self.organization_name,
                "passTypeIdentifier": config.type_identifier,
                "serialNumber": self.serial_number,
                "authenticationToken": config.webservice_secret,
                "webServiceURL": self._webservice_url(),
                "teamIdentifier": config.team_identifier,
                "description": self.description,
                "semantics": self._compile_semantics(),
                "backgroundColor": str(self.background_color) if self.background_color else None,
                "foregroundColor": str(self.foreground_color) if self.foreground_color else None,
                "labelColor": str(self.label_color) if self.label_color else None,
                "barcode": barcode,
                "barcodes": [barcode] if barcode else None,
                "relevantDate": isoformat(self.relevant_date),
                "locations": [location.to_dict() for location in self.locations] or None,
                "maxDistance": self.max_distance,
                "nfc": self.nfc.to_dict() if self.nfc else None,
                "userInfo": {"passType": self.type.value},
            }
            | self._compile_type_payload()
        )
        if not self._payload:
            return compiled

        merged = dict(self._payload)
        merged.update(compiled)
        pass_section = self.type.value
        if pass_section in compiled and isinstance(compiled.get(pass_section), dict):
            merged[pass_section] = {
                **(merged.get(pass_section) or {}),
                **compiled[pass_section],
            }
        return merged

    def _compile_type_payload(self) -> dict:
        return {
            self.type.value: filter_empty(
                {
                    "primaryFields": self._field_list(self.primary_fields),
                    "secondaryFields": self._field_list(self.secondary_fields),
                    "headerFields": self._field_list(self.header_fields),
                    "auxiliaryFields": self._field_list(self.auxiliary_fields),
                    "backFields": self._field_list(self.back_fields) if self.include_back_fields else None,
                }
            )
        }

    def _compile_semantics(self) -> dict | None:
        semantics = filter_empty(
            {
                "totalPrice": self.total_price.to_dict() if self.total_price else None,
                "wifiAccess": [wifi.to_dict() for wifi in self.wifi_details] or None,
            }
        )
        return semantics or None

    def _validate_payload(self, payload: dict) -> None:
        self.validator_class()().validate(payload)
        pass_payload = payload.get(self.type.value)
        if not isinstance(pass_payload, dict):
            raise InvalidPass(f"Apple payload must include a {self.type.value} section.")

    def _hydrate_images(self, images: dict) -> None:
        for name, payload in images.items():
            self.images[name] = AppleImage.from_dict(payload) if isinstance(payload, dict) else payload

    def _uncompile_content(self, payload: dict) -> None:
        self.organization_name = payload.get("organizationName")
        self.serial_number = payload.get("serialNumber")
        self.description = payload.get("description")
        self.background_color = Color.from_rgb_string(payload.get("backgroundColor"))
        self.foreground_color = Color.from_rgb_string(payload.get("foregroundColor"))
        self.label_color = Color.from_rgb_string(payload.get("labelColor"))
        self.barcode = Barcode.from_dict(payload["barcode"]) if payload.get("barcode") else None
        self.relevant_date = self._parse_datetime(payload.get("relevantDate"))
        self.locations = [Location.from_dict(location) for location in payload.get("locations", [])]
        self.max_distance = payload.get("maxDistance")
        self.nfc = NfcPayload.from_dict(payload["nfc"]) if payload.get("nfc") else None
        semantics = payload.get("semantics", {})
        self.total_price = Price.from_dict(semantics["totalPrice"]) if semantics.get("totalPrice") else None
        self.wifi_details = [WifiNetwork.from_dict(value) for value in semantics.get("wifiAccess", [])]

        pass_payload = payload.get(self.type.value, {})
        for field_type in FieldType:
            bucket = self._field_bucket(field_type)
            bucket.clear()
            for field in pass_payload.get(field_type.value, []):
                hydrated = FieldContent.from_dict(field)
                bucket[hydrated.key] = hydrated

    def _field_list(self, fields: dict[str, FieldContent]) -> list[dict] | None:
        values = [field.to_dict() for field in fields.values()]
        return values or None

    def _field_bucket(self, field_type: FieldType) -> dict[str, FieldContent]:
        mapping = {
            FieldType.HEADER: self.header_fields,
            FieldType.PRIMARY: self.primary_fields,
            FieldType.SECONDARY: self.secondary_fields,
            FieldType.AUXILIARY: self.auxiliary_fields,
            FieldType.BACK: self.back_fields,
        }
        return mapping[field_type]

    def _all_field_buckets(self) -> list[dict[str, FieldContent]]:
        return [self.header_fields, self.primary_fields, self.secondary_fields, self.auxiliary_fields, self.back_fields]

    def _webservice_url(self) -> str | None:
        host = self._resolve_webservice_host()
        return f"{host.rstrip('/')}/passkit" if host else None

    def _resolve_webservice_host(self) -> str | None:
        configured = get_mobile_pass_settings().apple.webservice_host
        if configured:
            if not configured.startswith("https://"):
                raise InvalidConfig("MOBILE_PASS.apple.webservice_host must be an https URL.")
            return configured

        app_url = getattr(django_settings, "APP_URL", None)
        if isinstance(app_url, str) and app_url.startswith("https://"):
            return app_url
        return None

    @staticmethod
    def _mobile_pass_model():
        app_label, model_name = get_mobile_pass_settings().model.split(".")
        return apps.get_model(app_label, model_name)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class EventTicketPassBuilder(ApplePassBuilder):
    type = PassType.EVENT_TICKET
    include_back_fields = True

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        return EventTicketApplePassValidator


class GenericPassBuilder(ApplePassBuilder):
    type = PassType.GENERIC

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        return GenericApplePassValidator


class CouponPassBuilder(ApplePassBuilder):
    type = PassType.COUPON

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        return CouponApplePassValidator


class StoreCardPassBuilder(ApplePassBuilder):
    type = PassType.STORE_CARD

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        return StoreCardApplePassValidator


class BoardingPassBuilder(ApplePassBuilder):
    type = PassType.BOARDING_PASS
    include_back_fields = True

    @classmethod
    def validator_class(cls) -> type[ApplePassValidator]:
        return BoardingApplePassValidator

    def __init__(self, payload: dict | None = None, images: dict | None = None, model: "MobilePass | None" = None):
        self.transit_type: TransitType | None = None
        self.current_arrival_date: datetime | None = None
        self.current_boarding_date: datetime | None = None
        self.current_departure_date: datetime | None = None
        self.original_arrival_date: datetime | None = None
        self.original_boarding_date: datetime | None = None
        self.original_departure_date: datetime | None = None
        self.confirmation_number: str | None = None
        self.boarding_group: str | None = None
        self.boarding_sequence_number: str | None = None
        self.departure_location: Location | None = None
        self.departure_location_description: str | None = None
        self.destination_location: Location | None = None
        self.destination_location_description: str | None = None
        self.duration_in_seconds: int | None = None
        self.membership_program_name: str | None = None
        self.membership_program_number: str | None = None
        self.passenger_name: PersonName | None = None
        self.priority_status: str | None = None
        self.seats: list[Seat] = []
        self.security_screening: str | None = None
        self.silence_requested: bool | None = None
        self.transit_provider: str | None = None
        self.transit_status: str | None = None
        self.transit_status_reason: str | None = None
        self.vehicle_name: str | None = None
        self.vehicle_number: str | None = None
        self.vehicle_type: str | None = None
        super().__init__(payload=payload, images=images, model=model)

    def set_boarding_group(self, value: str) -> "BoardingPassBuilder":
        self.boarding_group = value
        return self

    def set_boarding_sequence_number(self, value: str) -> "BoardingPassBuilder":
        self.boarding_sequence_number = value
        return self

    def set_confirmation_number(self, value: str) -> "BoardingPassBuilder":
        self.confirmation_number = value
        return self

    def set_current_arrival_date(self, value: datetime) -> "BoardingPassBuilder":
        self.current_arrival_date = value
        return self

    def set_current_boarding_date(self, value: datetime) -> "BoardingPassBuilder":
        self.current_boarding_date = value
        return self

    def set_current_departure_date(self, value: datetime) -> "BoardingPassBuilder":
        self.current_departure_date = value
        return self

    def set_departure_location(self, value: Location) -> "BoardingPassBuilder":
        self.departure_location = value
        return self

    def set_departure_location_description(self, value: str) -> "BoardingPassBuilder":
        self.departure_location_description = value
        return self

    def set_destination_location(self, value: Location) -> "BoardingPassBuilder":
        self.destination_location = value
        return self

    def set_destination_location_description(self, value: str) -> "BoardingPassBuilder":
        self.destination_location_description = value
        return self

    def set_duration(self, seconds: int) -> "BoardingPassBuilder":
        self.duration_in_seconds = seconds
        return self

    def set_membership_program_name(self, value: str) -> "BoardingPassBuilder":
        self.membership_program_name = value
        return self

    def set_membership_program_number(self, value: str) -> "BoardingPassBuilder":
        self.membership_program_number = value
        return self

    def set_original_arrival_date(self, value: datetime) -> "BoardingPassBuilder":
        self.original_arrival_date = value
        return self

    def set_original_boarding_date(self, value: datetime) -> "BoardingPassBuilder":
        self.original_boarding_date = value
        return self

    def set_original_departure_date(self, value: datetime) -> "BoardingPassBuilder":
        self.original_departure_date = value
        return self

    def set_passenger_name(self, value: PersonName) -> "BoardingPassBuilder":
        self.passenger_name = value
        return self

    def set_priority_status(self, value: str) -> "BoardingPassBuilder":
        self.priority_status = value
        return self

    def set_seats(self, *seats: Seat) -> "BoardingPassBuilder":
        self.seats = list(seats)
        return self

    def set_security_screening(self, value: str) -> "BoardingPassBuilder":
        self.security_screening = value
        return self

    def set_silence_requested(self, value: bool) -> "BoardingPassBuilder":
        self.silence_requested = value
        return self

    def set_transit_provider(self, value: str) -> "BoardingPassBuilder":
        self.transit_provider = value
        return self

    def set_transit_status(self, value: str) -> "BoardingPassBuilder":
        self.transit_status = value
        return self

    def set_transit_status_reason(self, value: str) -> "BoardingPassBuilder":
        self.transit_status_reason = value
        return self

    def set_vehicle_name(self, value: str) -> "BoardingPassBuilder":
        self.vehicle_name = value
        return self

    def set_vehicle_number(self, value: str) -> "BoardingPassBuilder":
        self.vehicle_number = value
        return self

    def set_vehicle_type(self, value: str) -> "BoardingPassBuilder":
        self.vehicle_type = value
        return self

    def set_footer_image(self, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "BoardingPassBuilder":
        self.images["footer"] = AppleImage(x1_path, x2_path, x3_path)
        return self

    def _compile_semantics(self) -> dict | None:
        semantics = super()._compile_semantics() or {}
        semantics.update(
            filter_empty(
                {
                    "boardingGroup": self.boarding_group,
                    "boardingSequenceNumber": self.boarding_sequence_number,
                    "confirmationNumber": self.confirmation_number,
                    "currentArrivalDate": isoformat(self.current_arrival_date),
                    "currentBoardingDate": isoformat(self.current_boarding_date),
                    "currentDepartureDate": isoformat(self.current_departure_date),
                    "departureLocation": self.departure_location.to_dict() if self.departure_location else None,
                    "departureLocationDescription": self.departure_location_description,
                    "destinationLocation": self.destination_location.to_dict() if self.destination_location else None,
                    "destinationLocationDescription": self.destination_location_description,
                    "duration": self.duration_in_seconds,
                    "membershipProgramName": self.membership_program_name,
                    "membershipProgramNumber": self.membership_program_number,
                    "originalArrivalDate": isoformat(self.original_arrival_date),
                    "originalBoardingDate": isoformat(self.original_boarding_date),
                    "originalDepartureDate": isoformat(self.original_departure_date),
                    "passengerName": self.passenger_name.to_dict() if self.passenger_name else None,
                    "priorityStatus": self.priority_status,
                    "seats": [seat.to_dict() for seat in self.seats] or None,
                    "securityScreening": self.security_screening,
                    "silenceRequested": self.silence_requested,
                    "transitProvider": self.transit_provider,
                    "transitStatus": self.transit_status,
                    "transitStatusReason": self.transit_status_reason,
                    "vehicleName": self.vehicle_name,
                    "vehicleNumber": self.vehicle_number,
                    "vehicleType": self.vehicle_type,
                }
            )
        )
        return semantics or None

    def _compile_type_payload(self) -> dict:
        payload = super()._compile_type_payload()[self.type.value]
        payload["transitType"] = self.transit_type.value if self.transit_type else None
        return {self.type.value: filter_empty(payload)}

    def _uncompile_content(self, payload: dict) -> None:
        super()._uncompile_content(payload)
        section = payload.get(self.type.value, {})
        self.transit_type = TransitType(section["transitType"]) if section.get("transitType") else None
        semantics = payload.get("semantics", {})
        self.boarding_group = semantics.get("boardingGroup")
        self.boarding_sequence_number = semantics.get("boardingSequenceNumber")
        self.confirmation_number = semantics.get("confirmationNumber")
        self.current_arrival_date = self._parse_datetime(semantics.get("currentArrivalDate"))
        self.current_boarding_date = self._parse_datetime(semantics.get("currentBoardingDate"))
        self.current_departure_date = self._parse_datetime(semantics.get("currentDepartureDate"))
        self.departure_location = Location.from_dict(semantics["departureLocation"]) if semantics.get("departureLocation") else None
        self.departure_location_description = semantics.get("departureLocationDescription")
        self.destination_location = Location.from_dict(semantics["destinationLocation"]) if semantics.get("destinationLocation") else None
        self.destination_location_description = semantics.get("destinationLocationDescription")
        self.duration_in_seconds = semantics.get("duration")
        self.membership_program_name = semantics.get("membershipProgramName")
        self.membership_program_number = semantics.get("membershipProgramNumber")
        self.original_arrival_date = self._parse_datetime(semantics.get("originalArrivalDate"))
        self.original_boarding_date = self._parse_datetime(semantics.get("originalBoardingDate"))
        self.original_departure_date = self._parse_datetime(semantics.get("originalDepartureDate"))
        self.passenger_name = PersonName.from_dict(semantics["passengerName"]) if semantics.get("passengerName") else None
        self.priority_status = semantics.get("priorityStatus")
        self.seats = [Seat.from_dict(seat) for seat in semantics.get("seats", [])]
        self.security_screening = semantics.get("securityScreening")
        self.silence_requested = semantics.get("silenceRequested")
        self.transit_provider = semantics.get("transitProvider")
        self.transit_status = semantics.get("transitStatus")
        self.transit_status_reason = semantics.get("transitStatusReason")
        self.vehicle_name = semantics.get("vehicleName")
        self.vehicle_number = semantics.get("vehicleNumber")
        self.vehicle_type = semantics.get("vehicleType")


class AirlinePassBuilder(BoardingPassBuilder):
    def __init__(self, payload: dict | None = None, images: dict | None = None, model: "MobilePass | None" = None):
        self.airline_code: str | None = None
        self.flight_code: str | None = None
        self.flight_number: str | None = None
        self.departure_gate: str | None = None
        self.departure_terminal: str | None = None
        self.departure_airport_code: str | None = None
        self.departure_airport_name: str | None = None
        self.destination_airport_name: str | None = None
        self.destination_airport_code: str | None = None
        self.destination_gate: str | None = None
        self.destination_terminal: str | None = None
        super().__init__(payload=payload, images=images, model=model)
        self.transit_type = self.transit_type or TransitType.AIR

    def set_airline_code(self, value: str) -> "AirlinePassBuilder":
        self.airline_code = value
        return self

    def set_departure_airport_code(self, value: str) -> "AirlinePassBuilder":
        self.departure_airport_code = value
        return self

    def set_departure_airport_name(self, value: str) -> "AirlinePassBuilder":
        self.departure_airport_name = value
        return self

    def set_departure_gate(self, value: str) -> "AirlinePassBuilder":
        self.departure_gate = value
        return self

    def set_departure_terminal(self, value: str) -> "AirlinePassBuilder":
        self.departure_terminal = value
        return self

    def set_destination_airport_name(self, value: str) -> "AirlinePassBuilder":
        self.destination_airport_name = value
        return self

    def set_destination_airport_code(self, value: str) -> "AirlinePassBuilder":
        self.destination_airport_code = value
        return self

    def set_destination_gate(self, value: str) -> "AirlinePassBuilder":
        self.destination_gate = value
        return self

    def set_destination_terminal(self, value: str) -> "AirlinePassBuilder":
        self.destination_terminal = value
        return self

    def set_flight_code(self, value: str) -> "AirlinePassBuilder":
        self.flight_code = value
        return self

    def set_flight_number(self, value: str) -> "AirlinePassBuilder":
        self.flight_number = value
        return self

    def _compile_semantics(self) -> dict | None:
        semantics = super()._compile_semantics() or {}
        semantics.update(
            filter_empty(
                {
                    "airlineCode": self.airline_code,
                    "flightCode": self.flight_code,
                    "flightNumber": self.flight_number,
                    "departureGate": self.departure_gate,
                    "departureTerminal": self.departure_terminal,
                    "departureAirportCode": self.departure_airport_code,
                    "departureAirportName": self.departure_airport_name,
                    "destinationAirportName": self.destination_airport_name,
                    "destinationAirportCode": self.destination_airport_code,
                    "destinationGate": self.destination_gate,
                    "destinationTerminal": self.destination_terminal,
                }
            )
        )
        return semantics or None

    def _uncompile_content(self, payload: dict) -> None:
        super()._uncompile_content(payload)
        semantics = payload.get("semantics", {})
        self.airline_code = semantics.get("airlineCode")
        self.flight_code = semantics.get("flightCode")
        self.flight_number = semantics.get("flightNumber")
        self.departure_gate = semantics.get("departureGate")
        self.departure_terminal = semantics.get("departureTerminal")
        self.departure_airport_code = semantics.get("departureAirportCode")
        self.departure_airport_name = semantics.get("departureAirportName")
        self.destination_airport_name = semantics.get("destinationAirportName")
        self.destination_airport_code = semantics.get("destinationAirportCode")
        self.destination_gate = semantics.get("destinationGate")
        self.destination_terminal = semantics.get("destinationTerminal")

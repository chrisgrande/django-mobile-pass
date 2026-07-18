from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django_mobile_pass.enums import (
    BarcodeType,
    DataDetectorType,
    DateType,
    NumberStyleType,
    TextAlignmentType,
    TimeStyleType,
)
from django_mobile_pass.exceptions import ImageNotFound
from django_mobile_pass.utils import ensure_w3c_datetime, filter_empty


@dataclass(slots=True)
class Color:
    red: int
    green: int
    blue: int

    @classmethod
    def from_hex(cls, value: str) -> "Color":
        value = value.lstrip("#")
        return cls(int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))

    @classmethod
    def from_rgb_string(cls, value: str | None) -> "Color | None":
        if not value:
            return None
        red, green, blue = value.removeprefix("rgb(").removesuffix(")").split(",")
        return cls(int(red.strip()), int(green.strip()), int(blue.strip()))

    def __str__(self) -> str:
        return f"rgb({self.red}, {self.green}, {self.blue})"


@dataclass(slots=True)
class Barcode:
    format: BarcodeType
    message: str
    message_encoding: str = "iso-8859-1"
    alt_text: str | None = None

    def with_alt_text(self, value: str) -> "Barcode":
        self.alt_text = value
        return self

    @classmethod
    def from_dict(cls, values: dict) -> "Barcode":
        return cls(
            format=BarcodeType(values["format"]),
            message=str(values["message"]),
            message_encoding=str(values.get("messageEncoding", "iso-8859-1")),
            alt_text=values.get("altText"),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "format": self.format.value,
                "message": self.message,
                "messageEncoding": self.message_encoding,
                "altText": self.alt_text,
            }
        )


@dataclass(slots=True)
class AppleImage:
    x1_path: str
    x2_path: str | None = None
    x3_path: str | None = None
    is_remote: bool = False

    def __post_init__(self) -> None:
        if self.is_remote:
            return
        for path in (self.x1_path, self.x2_path, self.x3_path):
            if path and not Path(path).exists():
                raise ImageNotFound(f"Image not found at {path}")

    @classmethod
    def make(cls, x1_path: str, x2_path: str | None = None, x3_path: str | None = None) -> "AppleImage":
        return cls(x1_path, x2_path, x3_path)

    @classmethod
    def make_remote(cls, x1_url: str, x2_url: str | None = None, x3_url: str | None = None) -> "AppleImage":
        return cls(x1_url, x2_url, x3_url, is_remote=True)

    @classmethod
    def from_dict(cls, values: dict) -> "AppleImage":
        x1_path = values.get("x1_path") or values.get("x1Path")
        if not x1_path:
            raise KeyError("Apple image payload requires x1_path or x1Path.")
        return cls(
            x1_path=x1_path,
            x2_path=values.get("x2_path") or values.get("x2Path"),
            x3_path=values.get("x3_path") or values.get("x3Path"),
            is_remote=bool(values.get("is_remote", values.get("isRemote", False))),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "x1_path": self.x1_path,
                "x2_path": self.x2_path,
                "x3_path": self.x3_path,
                "is_remote": self.is_remote or None,
            }
        )


@dataclass(slots=True)
class FieldContent:
    key: str
    value: str | None = None
    label: str | None = None
    attributed_value: str | None = None
    number_style: NumberStyleType | None = None
    change_message: str | None = None
    currency_code: str | None = None
    date_style: DateType | None = None
    time_style: TimeStyleType | None = None
    data_detector_type: DataDetectorType | None = None
    ignores_timezone: bool | None = None
    is_relative: bool | None = None
    text_alignment: TextAlignmentType | None = None

    def with_value(self, value: str) -> "FieldContent":
        self.value = value
        return self

    def with_label(self, label: str) -> "FieldContent":
        self.label = label
        return self

    def with_attributed_value(self, value: str) -> "FieldContent":
        self.attributed_value = value
        return self

    def using_number_style(self, style: NumberStyleType) -> "FieldContent":
        self.number_style = style
        return self

    def using_date_type(self, style: DateType) -> "FieldContent":
        self.date_style = style
        return self

    def using_time_type(self, style: TimeStyleType) -> "FieldContent":
        self.time_style = style
        return self

    def show_message_when_changed(self, message: str) -> "FieldContent":
        self.change_message = message.replace(":value", "%@")
        return self

    def using_currency_code(self, currency_code: str) -> "FieldContent":
        self.currency_code = currency_code
        return self

    def as_data_type(self, data_type: DataDetectorType) -> "FieldContent":
        self.data_detector_type = data_type
        return self

    def ignore_timezone(self) -> "FieldContent":
        self.ignores_timezone = True
        return self

    def show_date_as_relative(self) -> "FieldContent":
        self.is_relative = True
        return self

    @classmethod
    def from_dict(cls, values: dict) -> "FieldContent":
        raw_detectors = values.get("dataDetectorTypes")
        if isinstance(raw_detectors, list):
            data_detector_type = DataDetectorType(raw_detectors[0]) if raw_detectors else None
        elif raw_detectors:
            data_detector_type = DataDetectorType(raw_detectors)
        else:
            data_detector_type = None

        return cls(
            key=str(values["key"]),
            value=values.get("value"),
            label=values.get("label"),
            attributed_value=values.get("attributedValue"),
            number_style=NumberStyleType(values["numberStyle"]) if values.get("numberStyle") else None,
            change_message=values.get("changeMessage"),
            currency_code=values.get("currencyCode"),
            date_style=DateType(values["dateStyle"]) if values.get("dateStyle") else None,
            time_style=TimeStyleType(values["timeStyle"]) if values.get("timeStyle") else None,
            data_detector_type=data_detector_type,
            ignores_timezone=values.get("ignoresTimezone"),
            is_relative=values.get("isRelative"),
            text_alignment=TextAlignmentType(values["textAlignment"]) if values.get("textAlignment") else None,
        )

    def to_dict(self) -> dict:
        date_style = self.date_style
        time_style = self.time_style
        value = self.value

        # PassKit requires both styles when formatting a date, and the value
        # must be a W3C datetime with a timezone designator.
        if date_style is not None or time_style is not None:
            if date_style is None:
                date_style = DateType.NONE
            if time_style is None:
                time_style = TimeStyleType.NONE
            if value is not None:
                value = ensure_w3c_datetime(value)

        return filter_empty(
            {
                "key": self.key,
                "label": self.label,
                "value": value,
                "attributedValue": self.attributed_value,
                "changeMessage": self.change_message,
                "currencyCode": self.currency_code,
                "dataDetectorTypes": [self.data_detector_type.value] if self.data_detector_type else None,
                "dateStyle": date_style.value if date_style else None,
                "ignoresTimezone": self.ignores_timezone,
                "isRelative": self.is_relative,
                "numberStyle": self.number_style.value if self.number_style else None,
                "textAlignment": self.text_alignment.value if self.text_alignment else None,
                "timeStyle": time_style.value if time_style else None,
            }
        )


@dataclass(slots=True)
class Location:
    latitude: float
    longitude: float
    altitude: float | None = None
    relevant_text: str | None = None

    @classmethod
    def from_dict(cls, values: dict) -> "Location":
        return cls(
            latitude=float(values["latitude"]),
            longitude=float(values["longitude"]),
            altitude=float(values["altitude"]) if values.get("altitude") is not None else None,
            relevant_text=values.get("relevantText"),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "altitude": self.altitude,
                "relevantText": self.relevant_text,
            }
        )


@dataclass(slots=True)
class Price:
    amount: str | None = None
    currency_code: str | None = None

    @classmethod
    def from_dict(cls, values: dict) -> "Price":
        return cls(amount=values.get("amount"), currency_code=values.get("currencyCode"))

    def to_dict(self) -> dict:
        return filter_empty({"amount": self.amount, "currencyCode": self.currency_code})


@dataclass(slots=True)
class WifiNetwork:
    ssid: str
    password: str

    @classmethod
    def from_dict(cls, values: dict) -> "WifiNetwork":
        return cls(ssid=str(values["ssid"]), password=str(values["password"]))

    def to_dict(self) -> dict:
        return {"ssid": self.ssid, "password": self.password}


@dataclass(slots=True)
class NfcPayload:
    message: str
    encryption_public_key: str
    requires_authentication: bool = False

    @classmethod
    def from_dict(cls, values: dict) -> "NfcPayload":
        return cls(
            message=str(values["message"]),
            encryption_public_key=str(values["encryptionPublicKey"]),
            requires_authentication=bool(values.get("requiresAuthentication", False)),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "message": self.message,
                "encryptionPublicKey": self.encryption_public_key,
                "requiresAuthentication": True if self.requires_authentication else None,
            }
        )


@dataclass(slots=True)
class PersonName:
    family_name: str | None = None
    given_name: str | None = None
    middle_name: str | None = None
    name_prefix: str | None = None
    name_suffix: str | None = None
    nickname: str | None = None
    phonetic_representation: str | None = None

    @classmethod
    def from_dict(cls, values: dict) -> "PersonName":
        return cls(
            family_name=values.get("familyName"),
            given_name=values.get("givenName"),
            middle_name=values.get("middleName"),
            name_prefix=values.get("namePrefix"),
            name_suffix=values.get("nameSuffix"),
            nickname=values.get("nickname"),
            phonetic_representation=values.get("phoneticRepresentation"),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "familyName": self.family_name,
                "givenName": self.given_name,
                "middleName": self.middle_name,
                "namePrefix": self.name_prefix,
                "nameSuffix": self.name_suffix,
                "nickname": self.nickname,
                "phoneticRepresentation": self.phonetic_representation,
            }
        )


@dataclass(slots=True)
class Seat:
    description: str | None = None
    identifier: str | None = None
    number: str | None = None
    row: str | None = None
    section: str | None = None
    type: str | None = None

    @classmethod
    def from_dict(cls, values: dict) -> "Seat":
        return cls(
            description=values.get("description"),
            identifier=values.get("identifier"),
            number=values.get("number"),
            row=values.get("row"),
            section=values.get("section"),
            type=values.get("type"),
        )

    def to_dict(self) -> dict:
        return filter_empty(
            {
                "description": self.description,
                "identifier": self.identifier,
                "number": self.number,
                "row": self.row,
                "section": self.section,
                "type": self.type,
            }
        )

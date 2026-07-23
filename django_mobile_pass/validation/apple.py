from __future__ import annotations

import re

from django_mobile_pass.enums import PassType, TransitType
from django_mobile_pass.exceptions import InvalidPass
from django_mobile_pass.validation.engine import validate_payload

_W3C_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"
    r"(?::\d{2}(?:\.\d+)?)?"
    r"(?:Z|[+-]\d{2}:?\d{2})$"
)


class ApplePassValidator:
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "description": ["required", "string"],
            "formatVersion": ["required", "integer", ("in", {1})],
            "organizationName": ["required", "string"],
            "passTypeIdentifier": ["required", "string"],
            "serialNumber": ["required", "string"],
            "webServiceURL": ["nullable", "string"],
            "authenticationToken": ["nullable", "string", ("min", 16)],
            "teamIdentifier": ["required", "string"],
            "logoText": ["nullable", "string"],
            "barcode": [],
            "barcodes": [],
            "featuredActions": [],
            "relevantDate": [],
            "locations": [],
            "maxDistance": [],
            "nfc": [],
            "semantics": [],
            "primaryFields": [],
            "foregroundColor": [],
            "backgroundColor": [],
            "labelColor": [],
            "iconImagePath": [],
            "icon@2xImagePath": [],
            "icon@3xImagePath": [],
            "logoImagePath": [],
            "logo@2xImagePath": [],
            "logo@3xImagePath": [],
        }

    def validate(self, payload: dict) -> dict:
        validated = validate_payload(payload, self.rules())
        self._validate_webservice_pair(validated)
        self._validate_w3c_datetimes(validated)
        self._validate_date_fields(validated)
        return validated

    @staticmethod
    def _validate_webservice_pair(payload: dict) -> None:
        has_url = bool(payload.get("webServiceURL"))
        has_token = bool(payload.get("authenticationToken"))
        if has_url != has_token:
            raise InvalidPass(
                "webServiceURL and authenticationToken must both be set or both be omitted."
            )

    @staticmethod
    def _validate_w3c_datetimes(payload: dict) -> None:
        for key in ("relevantDate", "expirationDate"):
            value = payload.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not _W3C_DATETIME_RE.match(value):
                raise InvalidPass(
                    f"{key} must be a W3C datetime with a timezone "
                    f"(e.g. 2026-08-01T19:00:00Z), got {value!r}."
                )

    @staticmethod
    def _validate_date_fields(payload: dict) -> None:
        for pass_type in PassType:
            section = payload.get(pass_type.value)
            if not isinstance(section, dict):
                continue
            for field_group in (
                "headerFields",
                "primaryFields",
                "secondaryFields",
                "auxiliaryFields",
                "backFields",
                "footerFields",
            ):
                for field in section.get(field_group) or []:
                    if not isinstance(field, dict):
                        continue
                    if not field.get("dateStyle") and not field.get("timeStyle"):
                        continue
                    value = field.get("value")
                    if value is None:
                        continue
                    if not isinstance(value, str) or not _W3C_DATETIME_RE.match(value):
                        raise InvalidPass(
                            f"Field {field.get('key')!r} uses dateStyle/timeStyle but "
                            f"value {value!r} is not a W3C datetime with a timezone."
                        )
                    if not field.get("dateStyle") or not field.get("timeStyle"):
                        raise InvalidPass(
                            f"Field {field.get('key')!r} must include both dateStyle and "
                            f"timeStyle when formatting a date."
                        )


def _pass_type_field_rules(pass_type_key: str) -> dict[str, list[str | tuple]]:
    return {
        f"{pass_type_key}.headerFields": ["nullable", "array"],
        f"{pass_type_key}.primaryFields": ["nullable", "array"],
        f"{pass_type_key}.secondaryFields": ["nullable", "array"],
        f"{pass_type_key}.auxiliaryFields": ["nullable", "array"],
        f"{pass_type_key}.backFields": ["nullable", "array"],
        f"{pass_type_key}.footerFields": ["nullable", "array"],
    }


class EventTicketApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("eventTicket")}


class GenericApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("generic")}


class PosterGenericApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            **_pass_type_field_rules("posterGeneric"),
            **_pass_type_field_rules("generic"),
        }


class CouponApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("coupon")}


class StoreCardApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("storeCard")}


class BoardingApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        transit_values = {choice.value for choice in TransitType}
        return {
            **super().rules(),
            **_pass_type_field_rules("boardingPass"),
            "boardingPass.transitType": ["required", ("in", transit_values)],
        }

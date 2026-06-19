from __future__ import annotations

from django_mobile_pass.enums import TransitType
from django_mobile_pass.validation.engine import validate_payload


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
        return validate_payload(payload, self.rules())


def _pass_type_field_rules(pass_type_key: str) -> dict[str, list[str | tuple]]:
    return {
        f"{pass_type_key}.headerFields": ["nullable", "array"],
        f"{pass_type_key}.primaryFields": ["nullable", "array"],
        f"{pass_type_key}.secondaryFields": ["nullable", "array"],
        f"{pass_type_key}.auxiliaryFields": ["nullable", "array"],
        f"{pass_type_key}.backFields": ["nullable", "array"],
    }


class EventTicketApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("eventTicket")}


class GenericApplePassValidator(ApplePassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {**super().rules(), **_pass_type_field_rules("generic")}


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

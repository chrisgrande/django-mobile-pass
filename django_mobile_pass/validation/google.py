from __future__ import annotations

from django_mobile_pass.validation.engine import validate_payload


class GooglePassClassValidator:
    def rules(self) -> dict[str, list[str | tuple]]:
        return {"id": ["required", "string"]}

    def validate(self, payload: dict) -> dict:
        return validate_payload(payload, self.rules())


class GooglePassObjectValidator:
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "classId": ["required", "string"],
        }

    def validate(self, payload: dict) -> dict:
        return validate_payload(payload, self.rules())


class GenericClassValidator(GooglePassClassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "issuerName": ["nullable", "string"],
            "cardTitle": ["nullable", "array"],
            "cardTitle.defaultValue.value": ["nullable", "string"],
            "subheader": ["nullable", "array"],
            "subheader.defaultValue.value": ["nullable", "string"],
            "header": ["nullable", "array"],
            "header.defaultValue.value": ["nullable", "string"],
            "hexBackgroundColor": ["nullable", "string"],
            "logo": ["nullable", "array"],
            "heroImage": ["nullable", "array"],
            "reviewStatus": ["nullable", "string"],
        }


class GenericObjectValidator(GooglePassObjectValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            "state": ["nullable", "string"],
            "header": ["nullable", "array"],
            "cardTitle": ["nullable", "array"],
            "subheader": ["nullable", "array"],
            "notifications": ["nullable", "array"],
            "barcode": ["nullable", "array"],
        }


class EventTicketClassValidator(GooglePassClassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "issuerName": ["nullable", "string"],
            "eventName": ["required", "array"],
            "eventName.defaultValue.value": ["required", "string"],
            "venue": ["nullable", "array"],
            "venue.name": ["nullable", "array"],
            "venue.address": ["nullable", "array"],
            "dateTime": ["nullable", "array"],
            "logo": ["nullable", "array"],
            "heroImage": ["nullable", "array"],
            "hexBackgroundColor": ["nullable", "string"],
            "reviewStatus": ["nullable", "string"],
        }


class EventTicketObjectValidator(GooglePassObjectValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            "state": ["nullable", "string"],
            "ticketHolderName": ["nullable", "string"],
            "seatInfo": ["nullable", "array"],
            "barcode": ["nullable", "array"],
        }


class BoardingClassValidator(GooglePassClassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "issuerName": ["nullable", "string"],
            "localScheduledDepartureDateTime": ["nullable", "string"],
            "flightHeader": ["nullable", "array"],
            "flightHeader.carrier": ["nullable", "array"],
            "flightHeader.carrier.airlineCode": ["nullable", "string"],
            "flightHeader.flightNumber": ["nullable", "string"],
            "origin": ["nullable", "array"],
            "origin.airportIataCode": ["nullable", "string"],
            "destination": ["nullable", "array"],
            "destination.airportIataCode": ["nullable", "string"],
            "logo": ["nullable", "array"],
            "heroImage": ["nullable", "array"],
            "hexBackgroundColor": ["nullable", "string"],
            "reviewStatus": ["nullable", "string"],
        }


class BoardingObjectValidator(GooglePassObjectValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            "state": ["nullable", "string"],
            "passengerName": ["nullable", "string"],
            "boardingAndSeatingInfo": ["nullable", "array"],
            "reservationInfo": ["nullable", "array"],
            "barcode": ["nullable", "array"],
        }


class LoyaltyClassValidator(GooglePassClassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "issuerName": ["nullable", "string"],
            "programName": ["required", "string"],
            "programLogo": ["nullable", "array"],
            "rewardsTier": ["nullable", "string"],
            "rewardsTierLabel": ["nullable", "string"],
            "accountNameLabel": ["nullable", "string"],
            "accountIdLabel": ["nullable", "string"],
            "hexBackgroundColor": ["nullable", "string"],
            "reviewStatus": ["nullable", "string"],
        }


class LoyaltyObjectValidator(GooglePassObjectValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            "state": ["nullable", "string"],
            "accountId": ["nullable", "string"],
            "accountName": ["nullable", "string"],
            "loyaltyPoints": ["nullable", "array"],
            "barcode": ["nullable", "array"],
        }


class OfferClassValidator(GooglePassClassValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            "id": ["required", "string"],
            "issuerName": ["nullable", "string"],
            "title": ["required", "string"],
            "redemptionChannel": ["nullable", "string"],
            "provider": ["nullable", "string"],
            "details": ["nullable", "string"],
            "finePrint": ["nullable", "string"],
            "logo": ["nullable", "array"],
            "hexBackgroundColor": ["nullable", "string"],
            "reviewStatus": ["nullable", "string"],
        }


class OfferObjectValidator(GooglePassObjectValidator):
    def rules(self) -> dict[str, list[str | tuple]]:
        return {
            **super().rules(),
            "state": ["nullable", "string"],
            "title": ["nullable", "string"],
            "redemptionCode": ["nullable", "string"],
            "barcode": ["nullable", "array"],
        }

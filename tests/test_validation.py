import pytest

from django_mobile_pass.enums import TransitType
from django_mobile_pass.exceptions import InvalidPass
from django_mobile_pass.validation.apple import BoardingApplePassValidator, EventTicketApplePassValidator
from django_mobile_pass.validation.google import EventTicketClassValidator, LoyaltyClassValidator


def test_apple_event_ticket_validator_requires_core_fields():
    with pytest.raises(InvalidPass, match="description is required"):
        EventTicketApplePassValidator().validate({})


def test_apple_boarding_validator_requires_transit_type():
    payload = {
        "description": "Flight",
        "formatVersion": 1,
        "organizationName": "Airline",
        "passTypeIdentifier": "pass.com.example.boarding",
        "serialNumber": "ABC123",
        "teamIdentifier": "TEAM1234",
        "boardingPass": {"headerFields": []},
    }
    with pytest.raises(InvalidPass, match="boardingPass.transitType is required"):
        BoardingApplePassValidator().validate(payload)

    payload["boardingPass"]["transitType"] = TransitType.AIR.value
    BoardingApplePassValidator().validate(payload)


def test_google_event_ticket_class_requires_event_name():
    with pytest.raises(InvalidPass, match="eventName is required"):
        EventTicketClassValidator().validate({"id": "issuer.class"})

    EventTicketClassValidator().validate(
        {
            "id": "issuer.class",
            "eventName": {"defaultValue": {"value": "Main Stage"}},
        }
    )


def test_google_loyalty_class_requires_program_name():
    with pytest.raises(InvalidPass, match="programName is required"):
        LoyaltyClassValidator().validate({"id": "issuer.loyalty"})

    LoyaltyClassValidator().validate({"id": "issuer.loyalty", "programName": "Rewards"})

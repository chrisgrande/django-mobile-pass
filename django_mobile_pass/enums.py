from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class BarcodeType(StrEnum):
    QR = "PKBarcodeFormatQR"
    PDF417 = "PKBarcodeFormatPDF417"
    AZTEC = "PKBarcodeFormatAztec"
    CODE128 = "PKBarcodeFormatCode128"


class DataDetectorType(StrEnum):
    PHONE_NUMBER = "PKDataDetectorTypePhoneNumber"
    LINK = "PKDataDetectorTypeLink"
    ADDRESS = "PKDataDetectorTypeAddress"
    CALENDAR_EVENT = "PKDataDetectorTypeCalendarEvent"


class DateType(StrEnum):
    NONE = "PKDateStyleNone"
    SHORT = "PKDateStyleShort"
    MEDIUM = "PKDateStyleMedium"
    LONG = "PKDateStyleLong"
    FULL = "PKDateStyleFull"


class EventType(StrEnum):
    GENERIC = "PKEventTypeGeneric"
    LIVE_PERFORMANCE = "PKEventTypeLivePerformance"
    MOVIE = "PKEventTypeMovie"
    SPORTS = "PKEventTypeSports"
    CONFERENCE = "PKEventTypeConference"
    CONVENTION = "PKEventTypeConvention"
    WORKSHOP = "PKEventTypeWorkshop"
    SOCIAL_GATHERING = "PKEventTypeSocialGathering"


class FieldType(StrEnum):
    HEADER = "headerFields"
    PRIMARY = "primaryFields"
    SECONDARY = "secondaryFields"
    AUXILIARY = "auxiliaryFields"
    BACK = "backFields"


class NumberStyleType(StrEnum):
    DECIMAL = "PKNumberStyleDecimal"
    PERCENT = "PKNumberStylePercent"
    SCIENTIFIC = "PKNumberStyleScientific"
    SPELL_OUT = "PKNumberStyleSpellOut"


class PassType(StrEnum):
    BOARDING_PASS = "boardingPass"
    COUPON = "coupon"
    EVENT_TICKET = "eventTicket"
    STORE_CARD = "storeCard"
    GENERIC = "generic"


class Platform(StrEnum):
    APPLE = "apple"
    GOOGLE = "google"


class TextAlignmentType(StrEnum):
    LEFT = "PKTextAlignmentLeft"
    CENTER = "PKTextAlignmentCenter"
    RIGHT = "PKTextAlignmentRight"
    NATURAL = "PKTextAlignmentNatural"


class TimeStyleType(StrEnum):
    NONE = "PKDateStyleNone"
    SHORT = "PKDateStyleShort"
    MEDIUM = "PKDateStyleMedium"
    LONG = "PKDateStyleLong"
    FULL = "PKDateStyleFull"


class TransitType(StrEnum):
    AIR = "PKTransitTypeAir"
    BOAT = "PKTransitTypeBoat"
    BUS = "PKTransitTypeBus"
    GENERIC = "PKTransitTypeGeneric"
    TRAIN = "PKTransitTypeTrain"

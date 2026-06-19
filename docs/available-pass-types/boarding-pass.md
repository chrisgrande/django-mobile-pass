---
title: Boarding pass
weight: 43
---

# Boarding pass

Use Apple `BoardingPassBuilder` or `AirlinePassBuilder`, or Google `BoardingPassClass` plus `BoardingPassBuilder`.

## Apple airline boarding pass

`AirlinePassBuilder` defaults `transitType` to air and supports airline semantics:

```python
from django_mobile_pass.apple.builders import AirlinePassBuilder
from django_mobile_pass.apple.entities import PersonName, Seat

mobile_pass = (
    AirlinePassBuilder.make()
    .set_description("Flight EX123")
    .set_passenger_name(PersonName(given_name="Ada", family_name="Lovelace"))
    .set_seats([Seat(number="12A")])
    .set_airline_code("EX")
    .set_flight_code("EX123")
    .set_departure_airport_code("SFO")
    .set_destination_airport_code("JFK")
    .save()
)
```

## Apple non-air boarding passes

`BoardingPassBuilder` requires `transitType`. Subclass and set the class attribute before building:

```python
from django_mobile_pass.apple.builders import BoardingPassBuilder
from django_mobile_pass.enums import TransitType

class TrainBoardingPassBuilder(BoardingPassBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transit_type = TransitType.TRAIN
```

## Google boarding pass

```python
from django_mobile_pass.google.builders import BoardingPassClass, BoardingPassBuilder

(
    BoardingPassClass.make("sfo-jfk")
    .set_issuer_name("Example Air")
    .set_origin_airport_code("SFO")
    .set_destination_airport_code("JFK")
    .save()
)

mobile_pass = (
    BoardingPassBuilder.make()
    .set_class("sfo-jfk")
    .set_passenger_name("Ada Lovelace")
    .set_seat_number("12A")
    .save()
)
```

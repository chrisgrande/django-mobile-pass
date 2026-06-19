---
title: Testing your passes
weight: 56
---

# Testing your passes

Use Django's test client for PassKit routes, mock outbound HTTP for Google and APNs, and inspect compiled payloads before signing.

## PassKit route tests

```python
from django.test import Client, TestCase

from django_mobile_pass.apple.builders import EventTicketPassBuilder

class PasskitTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.mobile_pass = (
            EventTicketPassBuilder.make()
            .set_description("Event")
            .add_field("event", "Launch")
            .save()
        )
        self.auth = {"HTTP_AUTHORIZATION": "ApplePass your-webservice-secret"}

    def test_device_registration(self):
        url = f"/passkit/v1/devices/device-1/registrations/pass.example.test/{self.mobile_pass.pk}"
        response = self.client.post(
            url,
            data={"pushToken": "push-token-1"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 201)
```

Routes use the `MobilePass` UUID as `pass_serial`, not the `serialNumber` in `pass.json`.

## Asserting compiled payloads

Test builder output without a signing certificate:

```python
payload = (
    EventTicketPassBuilder.make()
    .set_description("Event")
    .add_field("event", "Launch")
    .data()
)

self.assertEqual(payload["eventTicket"]["primaryFields"][0]["key"], "event")
```

## Inspecting .pkpass archives

```python
from io import BytesIO

from django_mobile_pass.apple.reader import PkPassReader

archive = mobile_pass.generate()
reader = PkPassReader(BytesIO(archive))
pass_json = reader.pass_data()

self.assertEqual(pass_json["description"], "Event")
```

## Mocking Google Wallet API calls

```python
from unittest.mock import patch

@patch("django_mobile_pass.google.client.GoogleWalletClient.insert_object")
def test_google_pass_save(mock_insert):
    mock_insert.return_value = {}
    # ... builder.save() assertions
```

## Mocking APNs update notifications

```python
from unittest.mock import MagicMock, patch

from django_mobile_pass.actions import NotifyAppleOfPassUpdateAction

@patch.object(NotifyAppleOfPassUpdateAction, "_certificate_file")
@patch("requests.post")
def test_push_update(post, certificate_file):
    certificate_file.return_value = MagicMock(name="/tmp/cert.pem")
    post.return_value = MagicMock(ok=True, status_code=200, json=lambda: {})
    NotifyAppleOfPassUpdateAction().execute(mobile_pass)
```

## ECv2 callback verification

The test suite includes ECv2 fixtures in `tests/fixtures/google_ecv2.py` with bundled P-256 keypairs. Use `build_ecv2_callback_payload()` to exercise real signature verification without calling Google's live key endpoint.

```python
from tests.fixtures.google_ecv2 import build_ecv2_callback_payload, ecv2_root_keypair, ecv2_intermediate_keypair

root = ecv2_root_keypair()
intermediate = ecv2_intermediate_keypair()
payload = build_ecv2_callback_payload(
    root_private_pem=root["private"],
    intermediate_private_pem=intermediate["private"],
    intermediate_public_base64=intermediate["public_base64"],
    issuer_id="your-issuer-id",
    message={"eventType": "save", "objectId": "issuer.ticket-1"},
)
```

Run the suite with `python -m pytest tests/`.

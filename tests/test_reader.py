import json
from io import BytesIO
from zipfile import ZipFile

from django.test import SimpleTestCase

from django_mobile_pass.apple.reader import PkPassReader


class PkPassReaderTests(SimpleTestCase):
    def test_reader_inspects_pkpass_zip_contents(self):
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("pass.json", json.dumps({"description": "Test", "nested": {"value": 1}}))
            archive.writestr("manifest.json", json.dumps({"pass.json": "hash"}))
            archive.writestr("signature", b"signature")

        reader = PkPassReader.from_bytes(buffer.getvalue())

        self.assertTrue(reader.contains_file("pass.json"))
        self.assertEqual(reader.pass_property("description"), "Test")
        self.assertEqual(reader.pass_property("nested.value"), 1)
        self.assertEqual(reader.manifest_property("pass.json"), "hash")

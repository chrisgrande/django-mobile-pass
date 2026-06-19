from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile


class PkPassReader:
    def __init__(self, content: bytes):
        self._content = content

    @classmethod
    def from_file(cls, path: str | Path) -> "PkPassReader":
        return cls(Path(path).read_bytes())

    @classmethod
    def from_bytes(cls, content: bytes) -> "PkPassReader":
        return cls(content)

    def containing_files(self) -> list[str]:
        with self._zip() as archive:
            return archive.namelist()

    def contains_file(self, file_name: str) -> bool:
        return file_name in self.containing_files()

    def manifest_properties(self, key: str | None = None):
        return self._json_properties("manifest.json", key)

    def manifest_property(self, key: str):
        return self.manifest_properties(key)

    def pass_properties(self, key: str | None = None):
        return self._json_properties("pass.json", key)

    def pass_property(self, key: str):
        return self.pass_properties(key)

    def to_dict(self) -> dict:
        return {
            "files": self.containing_files(),
            "manifest": self.manifest_properties(),
            "pass": self.pass_properties(),
        }

    def _zip(self) -> ZipFile:
        return ZipFile(BytesIO(self._content))

    def _json_properties(self, file_name: str, key: str | None = None):
        with self._zip() as archive:
            properties = json.loads(archive.read(file_name))

        if key is None:
            return properties

        if key in properties:
            return properties[key]

        value = properties
        for segment in key.split("."):
            if not isinstance(value, dict) or segment not in value:
                return None
            value = value[segment]
        return value

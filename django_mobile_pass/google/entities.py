from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LocalizedString:
    default_value: str
    default_language: str = "en-US"
    translations: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def of(cls, value: str, language: str = "en-US") -> "LocalizedString":
        return cls(default_value=value, default_language=language)

    def add_translation(self, language: str, value: str) -> "LocalizedString":
        self.translations.append({"language": language, "value": value})
        return self

    def to_dict(self) -> dict:
        payload = {
            "defaultValue": {
                "language": self.default_language,
                "value": self.default_value,
            }
        }
        if self.translations:
            payload["translatedValues"] = self.translations
        return payload


@dataclass(slots=True)
class GoogleImage:
    url: str | None = None
    local_path: str | None = None

    @classmethod
    def from_url(cls, url: str) -> "GoogleImage":
        return cls(url=url)

    @classmethod
    def from_local_path(cls, path: str) -> "GoogleImage":
        return cls(local_path=path)

    def public_url(self) -> str:
        if self.url:
            return self.url
        raise RuntimeError(
            "GoogleImage.public_url() requires a public URL. Host local files separately before creating class payloads."
        )

    def to_dict(self) -> dict:
        return {"sourceUri": {"uri": self.public_url()}}


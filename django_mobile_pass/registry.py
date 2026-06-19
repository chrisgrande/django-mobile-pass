from __future__ import annotations

import inspect

from django.apps import apps
from django.utils.module_loading import import_string

from django_mobile_pass.apple.builders import ApplePassBuilder
from django_mobile_pass.enums import Platform
from django_mobile_pass.exceptions import InvalidConfig
from django_mobile_pass.google.builders import GooglePassBuilder
from django_mobile_pass.settings import get_mobile_pass_settings


def default_builders() -> dict[str, dict[str, str]]:
    return {
        "apple": {
            "airline": "django_mobile_pass.apple.builders.AirlinePassBuilder",
            "boarding": "django_mobile_pass.apple.builders.BoardingPassBuilder",
            "coupon": "django_mobile_pass.apple.builders.CouponPassBuilder",
            "event_ticket": "django_mobile_pass.apple.builders.EventTicketPassBuilder",
            "generic": "django_mobile_pass.apple.builders.GenericPassBuilder",
            "store_card": "django_mobile_pass.apple.builders.StoreCardPassBuilder",
        },
        "google": {
            "boarding": "django_mobile_pass.google.builders.BoardingPassBuilder",
            "event_ticket": "django_mobile_pass.google.builders.EventTicketPassBuilder",
            "generic": "django_mobile_pass.google.builders.GenericPassBuilder",
            "loyalty": "django_mobile_pass.google.builders.LoyaltyPassBuilder",
            "offer": "django_mobile_pass.google.builders.OfferPassBuilder",
        },
    }


def _ensure_subclass(candidate: type, base: type, *, kind: str, name: str) -> type:
    if not inspect.isclass(candidate) or not issubclass(candidate, base):
        raise InvalidConfig(
            f"The `{name}` {kind} must be a subclass of `{base.__module__}.{base.__name__}`. "
            f"Got `{candidate.__module__}.{candidate.__name__}`."
        )
    return candidate


def get_model_class(setting_name: str, default_dotted_path: str, base_model) -> type:
    dotted_path = getattr(get_mobile_pass_settings(), setting_name, default_dotted_path)
    app_label, model_name = dotted_path.rsplit(".", 1)
    model_class = apps.get_model(app_label, model_name)
    return _ensure_subclass(model_class, base_model, kind="model", name=setting_name)


def get_builder_class(name: str, platform: Platform | str):
    platform_value = platform.value if isinstance(platform, Platform) else str(platform)
    configured = (get_mobile_pass_settings().builders or {}).get(platform_value, {})
    dotted_path = configured.get(name) or default_builders().get(platform_value, {}).get(name)
    if not dotted_path:
        raise LookupError(f"No {platform_value} pass builder named {name!r} is registered.")

    builder_class = import_string(dotted_path)
    base_class = ApplePassBuilder if platform_value == Platform.APPLE.value else GooglePassBuilder
    return _ensure_subclass(builder_class, base_class, kind="pass builder", name=name)


def get_action_class(name: str, default_dotted_path: str, *, base_class: type | None = None):
    dotted_path = (get_mobile_pass_settings().actions or {}).get(name, default_dotted_path)
    action_class = import_string(dotted_path)
    if base_class is not None:
        return _ensure_subclass(action_class, base_class, kind="action", name=name)
    return action_class

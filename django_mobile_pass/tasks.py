from __future__ import annotations

from django_mobile_pass.exceptions import InvalidConfig
from django_mobile_pass.registry import get_action_class
from django_mobile_pass.settings import get_mobile_pass_settings

CELERY_TASK_NAME = "django_mobile_pass.push_pass_update"


def _resolve_action_name(mobile_pass) -> str:
    if mobile_pass.platform == "apple":
        return "notify_apple_of_pass_update"
    if mobile_pass.platform == "google":
        return "notify_google_of_pass_update"
    raise ValueError(f"Unsupported platform for pass update: {mobile_pass.platform!r}")


def _default_action_path(action_name: str) -> str:
    defaults = {
        "notify_apple_of_pass_update": "django_mobile_pass.actions.NotifyAppleOfPassUpdateAction",
        "notify_google_of_pass_update": "django_mobile_pass.actions.NotifyGoogleOfPassUpdateAction",
    }
    return defaults[action_name]


def execute_pass_update(mobile_pass_id, action_name: str) -> None:
    from django_mobile_pass.actions import mobile_pass_model

    mobile_pass = mobile_pass_model().objects.get(pk=mobile_pass_id)
    action_class = get_action_class(action_name, _default_action_path(action_name))
    action_class().execute(mobile_pass)


def push_pass_update_task(mobile_pass_id: str, action_name: str) -> None:
    execute_pass_update(mobile_pass_id, action_name)


def dispatch_pass_update(mobile_pass) -> None:
    if not get_mobile_pass_settings().push_updates_on_save:
        return

    action_name = _resolve_action_name(mobile_pass)
    queue = get_mobile_pass_settings().queue
    mobile_pass_id = str(mobile_pass.pk)

    if not queue.backend:
        execute_pass_update(mobile_pass_id, action_name)
        return

    if queue.backend == "celery":
        try:
            from celery import current_app
        except ImportError as exc:
            raise InvalidConfig(
                "MOBILE_PASS['queue']['backend'] is 'celery' but Celery is not installed."
            ) from exc

        current_app.send_task(
            CELERY_TASK_NAME,
            args=[mobile_pass_id, action_name],
            queue=queue.name or None,
        )
        return

    from django.utils.module_loading import import_string

    dispatcher = import_string(queue.backend)
    dispatcher(mobile_pass_id, action_name)

from unittest.mock import MagicMock, patch

import pytest

from django_mobile_pass.enums import Platform, PassType
from django_mobile_pass.models import MobilePass
from django_mobile_pass.tasks import dispatch_pass_update, execute_pass_update


@pytest.mark.django_db
def test_execute_pass_update_runs_apple_action(settings):
    settings.MOBILE_PASS = {
        "apple": {"webservice_secret": "x" * 16},
        "google": {},
    }
    mobile_pass = MobilePass.objects.create(
        type=PassType.EVENT_TICKET,
        platform=Platform.APPLE,
        builder_name="event_ticket",
        content={"passTypeIdentifier": "pass.com.example"},
        images={},
    )

    with patch("django_mobile_pass.actions.NotifyAppleOfPassUpdateAction.execute") as execute:
        execute_pass_update(str(mobile_pass.pk), "notify_apple_of_pass_update")
        execute.assert_called_once()


@pytest.mark.django_db
def test_dispatch_pass_update_sync_by_default(settings):
    settings.MOBILE_PASS = {
        "push_updates_on_save": True,
        "apple": {"webservice_secret": "x" * 16},
        "google": {},
    }
    mobile_pass = MobilePass.objects.create(
        type=PassType.EVENT_TICKET,
        platform=Platform.APPLE,
        builder_name="event_ticket",
        content={},
        images={},
    )

    with patch("django_mobile_pass.tasks.execute_pass_update") as execute:
        dispatch_pass_update(mobile_pass)
        execute.assert_called_once_with(str(mobile_pass.pk), "notify_apple_of_pass_update")


@pytest.mark.django_db
def test_dispatch_pass_update_custom_backend(settings):
    settings.MOBILE_PASS = {
        "push_updates_on_save": True,
        "queue": {"backend": "myapp.tasks.custom_dispatch"},
        "apple": {},
        "google": {},
    }
    mobile_pass = MobilePass.objects.create(
        type=PassType.COUPON,
        platform=Platform.GOOGLE,
        builder_name="offer",
        content={"googleClassType": "offerClass", "googleObjectId": "id"},
        images={},
    )
    dispatcher = MagicMock()

    with patch("django.utils.module_loading.import_string", return_value=dispatcher):
        dispatch_pass_update(mobile_pass)

    dispatcher.assert_called_once_with(str(mobile_pass.pk), "notify_google_of_pass_update")

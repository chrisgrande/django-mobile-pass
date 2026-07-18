from unittest.mock import patch

import pytest

from django_mobile_pass.enums import PassType, Platform
from django_mobile_pass.models import MobilePass


def _make_pass():
    return MobilePass.objects.create(
        type=PassType.EVENT_TICKET,
        platform=Platform.APPLE,
        builder_name="event_ticket",
        content={"passTypeIdentifier": "pass.example.test"},
        images={},
    )


def _enable_push_updates(settings):
    settings.MOBILE_PASS = {**settings.MOBILE_PASS, "push_updates_on_save": True}


@pytest.mark.django_db
def test_update_dispatch_waits_for_commit(settings, django_capture_on_commit_callbacks):
    _enable_push_updates(settings)
    mobile_pass = _make_pass()

    with patch("django_mobile_pass.receivers.dispatch_pass_update") as dispatch:
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            mobile_pass.content = {**mobile_pass.content, "changed": True}
            mobile_pass.save()
            dispatch.assert_not_called()

    assert len(callbacks) == 1
    dispatch.assert_called_once_with(mobile_pass)


@pytest.mark.django_db
def test_create_does_not_schedule_dispatch(settings, django_capture_on_commit_callbacks):
    _enable_push_updates(settings)

    with patch("django_mobile_pass.receivers.dispatch_pass_update") as dispatch:
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            _make_pass()

    assert callbacks == []
    dispatch.assert_not_called()


@pytest.mark.django_db
def test_disabled_push_updates_does_not_schedule_dispatch(settings, django_capture_on_commit_callbacks):
    settings.MOBILE_PASS = {**settings.MOBILE_PASS, "push_updates_on_save": False}
    mobile_pass = _make_pass()

    with patch("django_mobile_pass.receivers.dispatch_pass_update") as dispatch:
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            mobile_pass.save()

    assert callbacks == []
    dispatch.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_rolled_back_update_never_dispatches(settings):
    from django.db import transaction

    _enable_push_updates(settings)
    mobile_pass = _make_pass()

    class Boom(Exception):
        pass

    with patch("django_mobile_pass.receivers.dispatch_pass_update") as dispatch:
        with pytest.raises(Boom):
            with transaction.atomic():
                mobile_pass.content = {**mobile_pass.content, "changed": True}
                mobile_pass.save()
                raise Boom()

    dispatch.assert_not_called()

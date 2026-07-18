from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_mobile_pass.models import MobilePass
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.tasks import dispatch_pass_update


@receiver(post_save, sender=MobilePass)
def push_pass_update_on_save(sender, instance: MobilePass, created: bool, **kwargs) -> None:
    if created or not get_mobile_pass_settings().push_updates_on_save:
        return
    # post_save fires before any surrounding transaction commits. Dispatching
    # immediately lets devices (or a queue worker) read the pass before the new
    # content is visible -- or notifies them about a change that rolls back.
    # Defer until the data is committed; outside a transaction this runs at once.
    transaction.on_commit(lambda: dispatch_pass_update(instance), using=kwargs.get("using"))

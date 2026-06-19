from django.db.models.signals import post_save
from django.dispatch import receiver

from django_mobile_pass.models import MobilePass
from django_mobile_pass.settings import get_mobile_pass_settings
from django_mobile_pass.tasks import dispatch_pass_update


@receiver(post_save, sender=MobilePass)
def push_pass_update_on_save(sender, instance: MobilePass, created: bool, **kwargs) -> None:
    if created or not get_mobile_pass_settings().push_updates_on_save:
        return
    dispatch_pass_update(instance)


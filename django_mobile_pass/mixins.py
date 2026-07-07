from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from django_mobile_pass.enums import PassType, Platform


class HasMobilePasses(models.Model):
    """Abstract model mixin exposing the reverse relation to attached passes.

    Inherit it directly (``class Order(HasMobilePasses)``) or alongside other
    bases with the mixin first (``class Order(HasMobilePasses, models.Model)``).
    It must be an abstract model — Django only wires up ``GenericRelation``
    fields declared on model classes.
    """

    mobile_passes = GenericRelation(
        "django_mobile_pass.MobilePass",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    class Meta:
        abstract = True

    def add_mobile_pass(self, mobile_pass):
        mobile_pass.attach_to(self)

    def apple_passes(self):
        return self.mobile_passes.filter(platform=Platform.APPLE)

    def google_passes(self):
        return self.mobile_passes.filter(platform=Platform.GOOGLE)

    def first_mobile_pass(
        self,
        pass_type: PassType | None = None,
        platform: Platform | None = None,
        filter_callback=None,
    ):
        queryset = self.mobile_passes.all()
        if pass_type:
            queryset = queryset.filter(type=pass_type)
        if platform:
            queryset = queryset.filter(platform=platform)
        if filter_callback:
            queryset = filter_callback(queryset)
        return queryset.first()

    def first_apple_pass(self, pass_type: PassType | None = None):
        return self.first_mobile_pass(pass_type=pass_type, platform=Platform.APPLE)

    def first_google_pass(self, pass_type: PassType | None = None):
        return self.first_mobile_pass(pass_type=pass_type, platform=Platform.GOOGLE)


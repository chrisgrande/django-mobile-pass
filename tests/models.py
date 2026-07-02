from django.db import models

from django_mobile_pass.mixins import HasMobilePasses


class Customer(HasMobilePasses, models.Model):
    email = models.EmailField()

    class Meta:
        app_label = "tests"

from django.apps import AppConfig


class DjangoMobilePassConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_mobile_pass"
    verbose_name = "Django Mobile Pass"

    def ready(self) -> None:
        from django_mobile_pass import receivers  # noqa: F401

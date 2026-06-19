from django.urls import path

from django_mobile_pass import views

app_name = "django_mobile_pass"

urlpatterns = [
    path(
        "passkit/v1/devices/<str:device_id>/registrations/<str:pass_type_id>/<uuid:pass_serial>",
        views.device_registration,
        name="register-device",
    ),
    path(
        "passkit/v1/passes/<str:pass_type_id>/<uuid:pass_serial>",
        views.check_for_updates,
        name="check-for-updates",
    ),
    path(
        "passkit/v1/devices/<str:device_id>/registrations/<str:pass_type_id>",
        views.associated_serials,
        name="associated-serials",
    ),
    path("passkit/v1/log", views.mobile_pass_logs, name="logs"),
    path("passkit/v1/apple/<uuid:mobile_pass_id>/download", views.download_apple_pass, name="apple-download"),
    path("passkit/v1/google/callbacks", views.google_callback, name="google-callback"),
]

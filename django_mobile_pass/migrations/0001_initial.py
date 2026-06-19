from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="MobilePass",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("type", models.CharField(max_length=32)),
                ("platform", models.CharField(max_length=16)),
                ("builder_name", models.CharField(max_length=64)),
                ("content", models.JSONField(default=dict)),
                ("images", models.JSONField(default=dict)),
                ("download_name", models.CharField(blank=True, max_length=255, null=True)),
                ("object_id", models.CharField(blank=True, max_length=255, null=True)),
                ("expired_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="AppleMobilePassDevice",
            fields=[
                ("id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("push_token", models.CharField(max_length=512)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "apple_mobile_pass_devices"},
        ),
        migrations.CreateModel(
            name="GoogleMobilePassEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=32)),
                ("received_at", models.DateTimeField()),
                ("raw_payload", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "mobile_pass",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="google_events",
                        to="django_mobile_pass.mobilepass",
                    ),
                ),
            ],
            options={"db_table": "mobile_pass_google_events"},
        ),
        migrations.CreateModel(
            name="AppleMobilePassRegistration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("pass_type_id", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="registrations",
                        to="django_mobile_pass.applemobilepassdevice",
                    ),
                ),
                (
                    "mobile_pass",
                    models.ForeignKey(
                        db_column="pass_serial",
                        on_delete=models.deletion.CASCADE,
                        related_name="apple_registrations",
                        to="django_mobile_pass.mobilepass",
                    ),
                ),
            ],
            options={"db_table": "apple_mobile_pass_registrations"},
        ),
        migrations.AddIndex(
            model_name="googlemobilepassevent",
            index=models.Index(fields=["mobile_pass", "event_type"], name="django_mobi_mobile__8f9460_idx"),
        ),
        migrations.AddIndex(
            model_name="googlemobilepassevent",
            index=models.Index(fields=["received_at"], name="django_mobi_receive_0315fd_idx"),
        ),
        migrations.AddIndex(
            model_name="applemobilepassregistration",
            index=models.Index(fields=["device", "mobile_pass"], name="django_mobi_device__f0201c_idx"),
        ),
        migrations.AddIndex(
            model_name="applemobilepassregistration",
            index=models.Index(fields=["device", "pass_type_id"], name="django_mobi_device__7df3b0_idx"),
        ),
        migrations.AddConstraint(
            model_name="applemobilepassregistration",
            constraint=models.UniqueConstraint(
                fields=("device", "pass_type_id", "mobile_pass"),
                name="uniq_apple_pass_registration",
            ),
        ),
    ]

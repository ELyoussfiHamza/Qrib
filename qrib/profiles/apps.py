"""Profiles app configuration."""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Configuration for worker and customer profiles."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

"""AI agent app configuration."""

from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    """Configuration for backend AI agent workflows."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_agent"

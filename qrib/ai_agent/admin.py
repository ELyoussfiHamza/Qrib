"""Admin configuration for agent sessions."""

from django.contrib import admin

from .models import AgentSession


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    """Admin for backend agent sessions."""

    list_display = ("user", "role", "language", "updated_at")
    list_filter = ("role", "language")
    search_fields = ("user__phone_number", "user__full_name")
    readonly_fields = ("messages", "created_at", "updated_at")

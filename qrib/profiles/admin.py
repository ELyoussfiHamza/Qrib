"""Admin configuration for profiles."""

from django.contrib import admin

from .models import WorkerProfile


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    """Admin for worker profile drafts and completed profiles."""

    list_display = (
        "user",
        "full_name",
        "location_city",
        "location_permission_granted",
        "completed_at",
    )
    list_filter = ("location_permission_granted", "completed_at")
    search_fields = ("user__phone_number", "full_name", "location_city")
    readonly_fields = ("created_at", "updated_at", "completed_at")

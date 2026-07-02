"""Admin configuration for authentication models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin for phone-number based users."""

    model = User
    list_display = (
        "phone_number",
        "full_name",
        "profile_completed",
        "is_staff",
        "is_active",
    )
    list_filter = ("profile_completed", "is_staff", "is_active")
    ordering = ("phone_number",)
    search_fields = ("phone_number", "full_name")
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Profile", {"fields": ("full_name", "profile_completed")}),
        ("OTP", {"fields": ("otp_expires_at", "otp_verified_at")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = (
        "otp_expires_at",
        "otp_verified_at",
        "date_joined",
        "last_login",
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

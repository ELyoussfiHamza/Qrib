"""Profile models."""

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class WorkerProfile(models.Model):
    """Draft and completed profile data for a worker."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="worker_profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    location_permission_granted = models.BooleanField(default=False)
    location_lat = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        validators=(MinValueValidator(-90), MaxValueValidator(90)),
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=(MinValueValidator(-180), MaxValueValidator(180)),
    )
    location_city = models.CharField(max_length=80, blank=True)
    skills_description = models.TextField(blank=True)
    evidence_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "worker profile"
        verbose_name_plural = "worker profiles"

    def __str__(self):
        return f"Worker profile for {self.user_id}"

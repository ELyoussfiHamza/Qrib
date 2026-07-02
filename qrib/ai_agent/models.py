"""Models for backend agent sessions."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AgentSession(models.Model):
    """Stores lightweight conversation state for an authenticated user."""

    ROLE_UNKNOWN = "unknown"
    ROLE_WORKER = "worker"
    ROLE_CUSTOMER = "customer"

    ROLE_CHOICES = (
        (ROLE_UNKNOWN, "Unknown"),
        (ROLE_WORKER, "Worker"),
        (ROLE_CUSTOMER, "Customer"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_session",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_UNKNOWN,
    )
    language = models.CharField(max_length=16, default="en")
    messages = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "agent session"
        verbose_name_plural = "agent sessions"

    def __str__(self):
        return f"Agent session for {self.user_id}"

    def append_message(self, role, content):
        """Adds one message to the stored transcript."""
        self.messages.append({
            "role": role,
            "content": content,
            "created_at": timezone.now().isoformat(),
        })
        self.messages = self.messages[-20:]

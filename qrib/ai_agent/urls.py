"""URL routes for the backend AI agent."""

from django.urls import path

from . import views


urlpatterns = [
    path("state/", views.AgentStateView.as_view(), name="agent_state"),
    path("start/", views.AgentStartView.as_view(), name="agent_start"),
    path("message/", views.AgentMessageView.as_view(), name="agent_message"),
]

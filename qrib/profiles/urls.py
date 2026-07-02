"""URL routes for profile APIs."""

from django.urls import path

from . import views


urlpatterns = [
    path("me/", views.ProfileMeView.as_view(), name="profile_me"),
    path(
        "worker-draft/",
        views.WorkerDraftView.as_view(),
        name="worker_draft",
    ),
    path(
        "worker-complete/",
        views.WorkerCompleteView.as_view(),
        name="worker_complete",
    ),
]

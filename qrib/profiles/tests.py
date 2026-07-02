"""Tests for worker profile APIs."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import WorkerProfile


class WorkerProfileApiTests(APITestCase):
    """Covers profile draft updates and completion validation."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone_number="+212600000200"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_profile_me_creates_draft_and_reports_missing_fields(self):
        response = self.client.get("/profiles/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(WorkerProfile.objects.filter(user=self.user).exists())
        self.assertFalse(response.data["status"]["can_complete"])
        self.assertEqual(
            response.data["status"]["missing_required_fields"],
            ["full_name", "location", "skills_description"],
        )

    def test_worker_draft_updates_partial_profile(self):
        response = self.client.patch(
            "/profiles/worker-draft/",
            {
                "full_name": "Hamza Ait",
                "skills_description": "I repair water leaks and install sinks.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["worker_profile"]["full_name"],
            "Hamza Ait",
        )
        self.assertFalse(response.data["status"]["can_complete"])
        self.assertEqual(
            response.data["status"]["missing_required_fields"],
            ["location"],
        )

    def test_worker_complete_rejects_implausible_name(self):
        response = self.client.post(
            "/profiles/worker-complete/",
            {"full_name": "Casablanca"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Full name does not look", str(response.data["full_name"]))

    def test_worker_complete_rejects_missing_required_fields(self):
        response = self.client.post(
            "/profiles/worker-complete/",
            {"full_name": "Hamza Ait"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Worker profile is incomplete.")
        self.assertEqual(
            response.data["status"]["missing_required_fields"],
            ["location", "skills_description"],
        )

    def test_worker_complete_saves_valid_profile_and_marks_user_completed(self):
        response = self.client.post(
            "/profiles/worker-complete/",
            {
                "full_name": "Hamza Ait",
                "location_permission_granted": True,
                "location_lat": "33.573100",
                "location_lng": "-7.589800",
                "location_city": "Casablanca",
                "skills_description": (
                    "I repair water leaks and install bathroom fixtures."
                ),
                "evidence_notes": "Photos can be added later.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["status"]["profile_completed"])
        self.assertTrue(response.data["status"]["can_complete"])
        self.assertEqual(response.data["redirect_to"], "/worker/home")

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_completed)
        self.assertEqual(self.user.full_name, "Hamza Ait")

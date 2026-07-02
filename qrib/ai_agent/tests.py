"""Tests for the backend profile agent."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ai_agent.models import AgentSession
from profiles.models import WorkerProfile


class FakeAgentClient:
    """Fake OpenAI client returning queued decisions."""

    decisions = []

    def create_decision(self, state):
        return self.decisions.pop(0)


class FailingAgentClient:
    """Fake client for configuration/runtime errors."""

    def create_decision(self, state):
        raise RuntimeError("OPENAI_API_KEY is not configured.")


class AgentApiTests(APITestCase):
    """Covers agent orchestration without calling OpenAI."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            phone_number="+212600000300"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        FakeAgentClient.decisions = []

    def test_agent_state_creates_session_and_profile(self):
        response = self.client.get("/agent/state/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["agent"]["role"], "unknown")
        self.assertEqual(
            response.data["profile"]["status"]["missing_required_fields"],
            ["full_name", "location", "skills_description"],
        )

    def test_agent_start_asks_role_question_without_openai_call(self):
        response = self.client.post("/agent/start/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["assistant_message"],
            "Are you looking for a worker, or are you a worker?",
        )
        self.assertEqual(response.data["agent"]["role"], "unknown")
        self.assertFalse(response.data["completed"])

    @patch("ai_agent.services.OpenAIProfileAgentClient", return_value=FakeAgentClient())
    def test_agent_detects_worker_and_requests_location(self, _client_class):
        FakeAgentClient.decisions = [{
            "assistant_message": "Can I use your location for your work area?",
            "detected_role": "worker",
            "draft_updates": {"full_name": "Hamza Ait"},
            "frontend_actions": [{
                "type": "request_location_permission",
                "reason": "Location is required for worker area.",
            }],
            "ready_to_complete": False,
        }]

        response = self.client.post(
            "/agent/message/",
            {"message": "I am a worker. My name is Hamza Ait."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["agent"]["role"], "worker")
        self.assertEqual(
            response.data["profile"]["worker_profile"]["full_name"],
            "Hamza Ait",
        )
        self.assertEqual(
            response.data["frontend_actions"][0]["type"],
            "request_location_permission",
        )

    @patch("ai_agent.services.OpenAIProfileAgentClient", return_value=FakeAgentClient())
    def test_agent_applies_location_event_and_completes_valid_profile(
        self,
        _client_class,
    ):
        WorkerProfile.objects.create(
            user=self.user,
            full_name="Hamza Ait",
            skills_description="I repair water leaks and install sinks.",
        )
        FakeAgentClient.decisions = [{
            "assistant_message": "Done. Your worker profile is ready.",
            "detected_role": "worker",
            "draft_updates": {},
            "frontend_actions": [],
            "ready_to_complete": True,
        }]

        response = self.client.post(
            "/agent/message/",
            {
                "message": "yes",
                "events": [{
                    "type": "location_granted",
                    "payload": {
                        "lat": "33.573100",
                        "lng": "-7.589800",
                        "city": "Casablanca",
                    },
                }],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["completed"])
        self.assertEqual(response.data["redirect_to"], "/worker/home")

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_completed)

    @patch("ai_agent.services.OpenAIProfileAgentClient", return_value=FakeAgentClient())
    def test_agent_cannot_complete_incomplete_profile(self, _client_class):
        FakeAgentClient.decisions = [{
            "assistant_message": "I will save it now.",
            "detected_role": "worker",
            "draft_updates": {"full_name": "Hamza Ait"},
            "frontend_actions": [],
            "ready_to_complete": True,
        }]

        response = self.client.post(
            "/agent/message/",
            {"message": "save it"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["completed"])
        self.assertIn("location", response.data["backend_validation_errors"])
        self.assertIn(
            "skills_description",
            response.data["backend_validation_errors"],
        )

    @patch("ai_agent.services.OpenAIProfileAgentClient", return_value=FakeAgentClient())
    def test_agent_handles_customer_role_without_worker_completion(
        self,
        _client_class,
    ):
        FakeAgentClient.decisions = [{
            "assistant_message": "Customer hiring flow is coming soon.",
            "detected_role": "customer",
            "draft_updates": {},
            "frontend_actions": [],
            "ready_to_complete": False,
        }]

        response = self.client.post(
            "/agent/message/",
            {"message": "I need to find a plumber."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["agent"]["role"], "customer")
        self.assertFalse(response.data["completed"])

    def test_agent_start_resumes_next_missing_worker_field(self):
        AgentSession.objects.create(user=self.user, role=AgentSession.ROLE_WORKER)
        WorkerProfile.objects.create(
            user=self.user,
            full_name="Hamza Ait",
            location_permission_granted=True,
            location_lat="33.573100",
            location_lng="-7.589800",
            location_city="Casablanca",
        )

        response = self.client.post("/agent/start/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["assistant_message"],
            "Tell me what kind of work you know how to do.",
        )

    @patch(
        "ai_agent.services.OpenAIProfileAgentClient",
        return_value=FailingAgentClient(),
    )
    def test_agent_returns_503_when_openai_is_not_configured(self, _client_class):
        response = self.client.post(
            "/agent/message/",
            {"message": "hello"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertIn("OPENAI_API_KEY", response.data["detail"])

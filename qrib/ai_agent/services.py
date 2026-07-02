"""Agent orchestration and safe execution of model decisions."""

from profiles.serializers import WorkerDraftSerializer
from profiles.serializers import serialize_worker_profile_response
from profiles.services import complete_worker_profile
from profiles.services import get_worker_profile

from .models import AgentSession
from .openai_client import OpenAIProfileAgentClient


ALLOWED_DRAFT_UPDATE_FIELDS = {
    "full_name",
    "location_permission_granted",
    "location_lat",
    "location_lng",
    "location_city",
    "skills_description",
    "evidence_notes",
}


def get_agent_session(user):
    """Returns the user's agent session, creating it when needed."""
    session, _ = AgentSession.objects.get_or_create(user=user)
    return session


class ProfileAgentService:
    """Runs the profile agent and applies safe backend-side effects."""

    def __init__(self, agent_client=None):
        self.agent_client = agent_client or OpenAIProfileAgentClient()

    def get_state(self, user):
        """Returns the current state visible to the agent/frontend."""
        session = get_agent_session(user)
        worker_profile = get_worker_profile(user)
        return self._state(user, session, worker_profile)

    def start(self, user):
        """Starts or resumes onboarding without requiring a user message."""
        session = get_agent_session(user)
        worker_profile = get_worker_profile(user)
        assistant_message = self._start_message(user, session, worker_profile)

        if not session.messages:
            session.append_message("assistant", assistant_message)
            session.save(update_fields=("messages", "updated_at"))

        return self._response_payload(
            user=user,
            session=session,
            worker_profile=worker_profile,
            assistant_message=assistant_message,
        )

    def handle_turn(self, user, message="", events=None, input_type="text"):
        """Handles one frontend turn and returns the agent response payload."""
        events = events or []
        session = get_agent_session(user)
        worker_profile = get_worker_profile(user)

        event_actions = self._apply_events(worker_profile, events)
        if message:
            session.append_message("user", message)

        state = self._state(
            user,
            session,
            worker_profile,
            last_user_message=message,
            input_type=input_type,
            frontend_events=events,
        )
        decision = self.agent_client.create_decision(state)
        result = self._apply_decision(user, session, worker_profile, decision)

        frontend_actions = event_actions + result["frontend_actions"]
        assistant_message = result["assistant_message"]
        session.append_message("assistant", assistant_message)
        session.save(update_fields=("role", "messages", "updated_at"))

        return self._response_payload(
            user=user,
            session=session,
            worker_profile=worker_profile,
            assistant_message=assistant_message,
            frontend_actions=frontend_actions,
            ready_to_complete=result["ready_to_complete"],
            completed=result["completed"],
            redirect_to=result["redirect_to"],
            backend_validation_errors=result["backend_validation_errors"],
        )

    def _apply_events(self, worker_profile, events):
        frontend_actions = []
        for event in events:
            event_type = event["type"]
            payload = event.get("payload") or {}
            if event_type == "location_granted":
                serializer = WorkerDraftSerializer(
                    worker_profile,
                    data={
                        "location_permission_granted": True,
                        "location_lat": payload.get("lat"),
                        "location_lng": payload.get("lng"),
                        "location_city": payload.get("city", ""),
                    },
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            elif event_type == "location_denied":
                worker_profile.location_permission_granted = False
                worker_profile.save(update_fields=(
                    "location_permission_granted",
                    "updated_at",
                ))
            elif event_type == "media_upload_added":
                frontend_actions.append({
                    "type": "media_upload_recorded",
                    "reason": "Media upload was received by the app.",
                })
        return frontend_actions

    def _apply_decision(self, user, session, worker_profile, decision):
        detected_role = decision.get("detected_role")
        if detected_role in {
            AgentSession.ROLE_WORKER,
            AgentSession.ROLE_CUSTOMER,
            AgentSession.ROLE_UNKNOWN,
        }:
            session.role = detected_role

        backend_validation_errors = {}
        draft_updates = self._clean_draft_updates(
            decision.get("draft_updates") or {}
        )
        if draft_updates:
            serializer = WorkerDraftSerializer(
                worker_profile,
                data=draft_updates,
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
            else:
                backend_validation_errors = serializer.errors

        completed = False
        redirect_to = ""
        if decision.get("ready_to_complete") and not backend_validation_errors:
            completion = complete_worker_profile(user, worker_profile)
            completed = completion.completed
            redirect_to = completion.redirect_to
            if not completion.completed:
                backend_validation_errors = completion.status.validation_errors

        return {
            "assistant_message": decision["assistant_message"],
            "frontend_actions": self._clean_frontend_actions(
                decision.get("frontend_actions") or []
            ),
            "ready_to_complete": bool(decision.get("ready_to_complete")),
            "completed": completed,
            "redirect_to": redirect_to,
            "backend_validation_errors": backend_validation_errors,
        }

    def _clean_draft_updates(self, draft_updates):
        return {
            key: value
            for key, value in draft_updates.items()
            if key in ALLOWED_DRAFT_UPDATE_FIELDS and value not in ("", None)
        }

    def _clean_frontend_actions(self, frontend_actions):
        allowed_types = {
            "request_location_permission",
            "request_media_upload",
            "none",
            "media_upload_recorded",
        }
        clean_actions = []
        for action in frontend_actions:
            action_type = action.get("type")
            if action_type not in allowed_types or action_type == "none":
                continue
            clean_actions.append({
                "type": action_type,
                "reason": action.get("reason", ""),
            })
        return clean_actions

    def _start_message(self, user, session, worker_profile):
        profile_response = serialize_worker_profile_response(user, worker_profile)
        missing_fields = profile_response["status"]["missing_required_fields"]

        if user.profile_completed:
            return "Your profile is complete."
        if session.role == AgentSession.ROLE_UNKNOWN:
            return "Are you looking for a worker, or are you a worker?"
        if session.role == AgentSession.ROLE_CUSTOMER:
            return "The customer hiring flow is coming soon."
        if "full_name" in missing_fields:
            return "What should I call you?"
        if "location" in missing_fields:
            return "Can I use your location to estimate your work area?"
        if "skills_description" in missing_fields:
            return "Tell me what kind of work you know how to do."
        return "I have the required details. Should I create your worker profile?"

    def _response_payload(
        self,
        user,
        session,
        worker_profile,
        assistant_message,
        frontend_actions=None,
        ready_to_complete=False,
        completed=False,
        redirect_to="",
        backend_validation_errors=None,
    ):
        worker_profile.refresh_from_db()
        return {
            "assistant_message": assistant_message,
            "frontend_actions": frontend_actions or [],
            "agent": {
                "role": session.role,
                "language": session.language,
            },
            "profile": serialize_worker_profile_response(user, worker_profile),
            "ready_to_complete": ready_to_complete,
            "completed": completed,
            "redirect_to": redirect_to,
            "backend_validation_errors": backend_validation_errors or {},
        }

    def _state(
        self,
        user,
        session,
        worker_profile,
        last_user_message="",
        input_type="text",
        frontend_events=None,
    ):
        profile_response = serialize_worker_profile_response(user, worker_profile)
        return {
            "agent": {
                "role": session.role,
                "language": session.language,
                "recent_messages": session.messages[-8:],
            },
            "input": {
                "last_user_message": last_user_message,
                "input_type": input_type,
                "frontend_events": frontend_events or [],
            },
            "profile": profile_response,
            "instructions_for_next_step": {
                "ask_role_if_unknown": session.role == AgentSession.ROLE_UNKNOWN,
                "ask_one_question_at_a_time": True,
                "backend_will_validate_before_saving": True,
            },
        }

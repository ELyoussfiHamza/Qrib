"""API views for the backend AI agent."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AgentMessageSerializer
from .services import ProfileAgentService


class AgentStateView(APIView):
    """Returns the current state used by the backend agent."""

    permission_classes = (IsAuthenticated,)
    service_class = ProfileAgentService

    def get(self, request):
        service = self.service_class()
        return Response(service.get_state(request.user))


class AgentStartView(APIView):
    """Starts or resumes the agent conversation."""

    permission_classes = (IsAuthenticated,)
    service_class = ProfileAgentService

    def post(self, request):
        service = self.service_class()
        return Response(service.start(request.user))


class AgentMessageView(APIView):
    """Sends one user message or frontend event batch to the agent."""

    permission_classes = (IsAuthenticated,)
    service_class = ProfileAgentService

    def post(self, request):
        serializer = AgentMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = self.service_class()
        try:
            payload = service.handle_turn(
                request.user,
                message=serializer.validated_data.get("message", ""),
                events=serializer.validated_data.get("events", []),
                input_type=serializer.validated_data.get("input_type", "text"),
            )
        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(payload)

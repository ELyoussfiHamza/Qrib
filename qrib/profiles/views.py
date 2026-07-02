"""API views for profile draft and completion."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import WorkerDraftSerializer
from .serializers import serialize_worker_profile_response
from .services import complete_worker_profile
from .services import get_worker_profile


class ProfileMeView(APIView):
    """Returns the authenticated user's profile and completion status."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        worker_profile = get_worker_profile(request.user)
        return Response(
            serialize_worker_profile_response(request.user, worker_profile)
        )


class WorkerDraftView(APIView):
    """Updates the authenticated user's worker profile draft."""

    permission_classes = (IsAuthenticated,)

    def patch(self, request):
        worker_profile = get_worker_profile(request.user)
        serializer = WorkerDraftSerializer(
            worker_profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serialize_worker_profile_response(request.user, worker_profile)
        )


class WorkerCompleteView(APIView):
    """Completes the worker profile after all required fields validate."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        worker_profile = get_worker_profile(request.user)
        if request.data:
            serializer = WorkerDraftSerializer(
                worker_profile,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        result = complete_worker_profile(request.user, worker_profile)
        if not result.completed:
            return Response(
                {
                    "detail": "Worker profile is incomplete.",
                    **serialize_worker_profile_response(
                        request.user,
                        worker_profile,
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            **serialize_worker_profile_response(request.user, worker_profile),
            "redirect_to": result.redirect_to,
        })

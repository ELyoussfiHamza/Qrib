"""API views for authentication."""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RequestOtpSerializer
from .serializers import UserSerializer
from .serializers import VerifyOtpSerializer


def _generate_otp_code():
    """Generates a numeric OTP code."""
    digits = settings.QRIB_OTP_CODE_LENGTH
    lower_bound = 10 ** (digits - 1)
    upper_bound = 10 ** digits
    return str(secrets.randbelow(upper_bound - lower_bound) + lower_bound)


def _issue_tokens(user):
    """Issues SimpleJWT refresh and access tokens for a verified user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class RequestOtpView(APIView):
    """Creates or refreshes an OTP challenge for a phone number."""

    authentication_classes = []
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "request_otp"

    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        user, _ = get_user_model().objects.get_or_create(
            phone_number=phone_number)

        otp_code = _generate_otp_code()
        expires_at = timezone.now() + settings.QRIB_OTP_TTL
        user.set_otp_code(otp_code, expires_at)
        user.save(update_fields=("otp_code_hash", "otp_expires_at"))

        response = {
            "detail": "OTP code generated.",
            "phone_number": phone_number,
            "expires_at": expires_at,
        }
        if settings.QRIB_RETURN_OTP_IN_RESPONSE:
            response["otp"] = otp_code
        return Response(response, status=status.HTTP_200_OK)


class VerifyOtpView(APIView):
    """Verifies an OTP challenge and issues JWT tokens."""

    authentication_classes = []
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "verify_otp"

    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]
        user = get_user_model().objects.filter(phone_number=phone_number).first()

        if not user or not user.is_active or not user.verify_otp_code(code):
            return Response(
                {"detail": "Invalid or expired OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.mark_otp_verified()
        user.save(update_fields=("otp_verified_at", "otp_code_hash",
                                 "otp_expires_at"))

        return Response({
            **_issue_tokens(user),
            "user": UserSerializer(user).data,
        })


class MeView(APIView):
    """Returns the authenticated user's profile state."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user).data)


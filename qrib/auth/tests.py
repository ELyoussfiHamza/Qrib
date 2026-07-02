"""Tests for phone OTP authentication."""

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


@override_settings(QRIB_RETURN_OTP_IN_RESPONSE=True)
class PhoneOtpAuthTests(APITestCase):
    """Covers OTP generation, verification, and profile-state retrieval."""

    def test_verify_otp_creates_tokens_and_returns_profile_state(self):
        phone_number = "+212600000000"

        request_response = self.client.post(
            "/auth/request-otp/",
            {"phone_number": phone_number},
            format="json",
        )

        self.assertEqual(request_response.status_code, status.HTTP_200_OK)
        otp_code = request_response.data["otp"]
        user = get_user_model().objects.get(phone_number=phone_number)
        self.assertFalse(user.profile_completed)
        self.assertNotEqual(user.otp_code_hash, otp_code)

        verify_response = self.client.post(
            "/auth/verify-otp/",
            {"phone_number": phone_number, "code": otp_code},
            format="json",
        )

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", verify_response.data)
        self.assertIn("refresh", verify_response.data)
        self.assertEqual(verify_response.data["user"]["phone_number"],
                         phone_number)
        self.assertFalse(verify_response.data["user"]["profile_completed"])

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {verify_response.data['access']}")
        me_response = self.client.get("/auth/me/")

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["phone_number"], phone_number)

    def test_refresh_token_returns_new_access_token(self):
        phone_number = "+212600000002"

        request_response = self.client.post(
            "/auth/request-otp/",
            {"phone_number": phone_number},
            format="json",
        )
        verify_response = self.client.post(
            "/auth/verify-otp/",
            {
                "phone_number": phone_number,
                "code": request_response.data["otp"],
            },
            format="json",
        )

        refresh_response = self.client.post(
            "/auth/token/refresh/",
            {"refresh": verify_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_verify_otp_rejects_invalid_code(self):
        phone_number = "+212600000001"

        self.client.post(
            "/auth/request-otp/",
            {"phone_number": phone_number},
            format="json",
        )
        verify_response = self.client.post(
            "/auth/verify-otp/",
            {"phone_number": phone_number, "code": "000000"},
            format="json",
        )

        self.assertEqual(verify_response.status_code,
                         status.HTTP_400_BAD_REQUEST)

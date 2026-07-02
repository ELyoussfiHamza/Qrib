"""Serializers for phone OTP authentication."""

import re

from django.contrib.auth import get_user_model
from rest_framework import serializers


PHONE_NUMBER_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")


class RequestOtpSerializer(serializers.Serializer):
    """Validates OTP request payloads."""

    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        phone_number = value.strip().replace(" ", "")
        if not PHONE_NUMBER_PATTERN.fullmatch(phone_number):
            raise serializers.ValidationError(
                "Enter a valid phone number in international format.")
        return phone_number


class VerifyOtpSerializer(RequestOtpSerializer):
    """Validates OTP verification payloads."""

    code = serializers.CharField(min_length=4, max_length=8, trim_whitespace=True)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain digits only.")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializes the authenticated user state needed by clients."""

    class Meta:
        model = get_user_model()
        fields = ("id", "phone_number", "full_name", "profile_completed")

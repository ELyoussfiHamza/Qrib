"""Serializers for profile APIs."""

from rest_framework import serializers

from .models import WorkerProfile
from .services import build_worker_profile_status
from .services import normalize_space
from .services import validate_full_name


class WorkerProfileSerializer(serializers.ModelSerializer):
    """Serializes worker profile draft and completed data."""

    class Meta:
        model = WorkerProfile
        fields = (
            "full_name",
            "location_permission_granted",
            "location_lat",
            "location_lng",
            "location_city",
            "skills_description",
            "evidence_notes",
            "completed_at",
        )
        read_only_fields = ("completed_at",)


class WorkerDraftSerializer(serializers.ModelSerializer):
    """Validates partial worker profile draft updates."""

    class Meta:
        model = WorkerProfile
        fields = (
            "full_name",
            "location_permission_granted",
            "location_lat",
            "location_lng",
            "location_city",
            "skills_description",
            "evidence_notes",
        )

    def validate_full_name(self, value):
        full_name = normalize_space(value)
        error = validate_full_name(full_name)
        if error:
            raise serializers.ValidationError(error)
        return full_name

    def validate_location_city(self, value):
        return normalize_space(value)

    def validate_skills_description(self, value):
        return normalize_space(value)

    def validate_evidence_notes(self, value):
        return normalize_space(value)


class WorkerProfileStatusSerializer(serializers.Serializer):
    """Serializes profile completion status."""

    profile_completed = serializers.BooleanField()
    can_complete = serializers.BooleanField()
    missing_required_fields = serializers.ListField(
        child=serializers.CharField(),
    )
    validation_errors = serializers.DictField(child=serializers.CharField())


def serialize_worker_profile_response(user, worker_profile):
    """Builds the shared response body for profile endpoints."""
    status = build_worker_profile_status(worker_profile)
    return {
        "user": {
            "id": user.id,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "profile_completed": user.profile_completed,
        },
        "worker_profile": WorkerProfileSerializer(worker_profile).data,
        "status": WorkerProfileStatusSerializer({
            "profile_completed": user.profile_completed,
            "can_complete": status.can_complete,
            "missing_required_fields": status.missing_required_fields,
            "validation_errors": status.validation_errors,
        }).data,
    }

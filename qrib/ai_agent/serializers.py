"""Serializers for agent API endpoints."""

from rest_framework import serializers


class AgentEventSerializer(serializers.Serializer):
    """Validates structured frontend events sent to the agent endpoint."""

    type = serializers.ChoiceField(
        choices=(
            "location_granted",
            "location_denied",
            "media_upload_added",
        )
    )
    payload = serializers.DictField(required=False, default=dict)


class AgentMessageSerializer(serializers.Serializer):
    """Validates one message or event batch for the backend agent."""

    message = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )
    input_type = serializers.ChoiceField(
        choices=("text", "voice_transcript"),
        default="text",
        required=False,
    )
    events = AgentEventSerializer(many=True, required=False, default=list)

    def validate(self, attrs):
        message = attrs.get("message", "")
        events = attrs.get("events", [])
        if not message and not events:
            raise serializers.ValidationError(
                "Provide a message or at least one event."
            )
        return attrs

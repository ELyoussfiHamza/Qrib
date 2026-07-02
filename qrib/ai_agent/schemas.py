"""Schemas and prompt text for the profile agent."""


AGENT_DECISION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "assistant_message",
        "detected_role",
        "draft_updates",
        "frontend_actions",
        "ready_to_complete",
    ],
    "properties": {
        "assistant_message": {
            "type": "string",
            "description": "Short message to say to the user.",
        },
        "detected_role": {
            "type": ["string", "null"],
            "enum": ["worker", "customer", "unknown", None],
        },
        "draft_updates": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "full_name",
                "location_permission_granted",
                "location_lat",
                "location_lng",
                "location_city",
                "skills_description",
                "evidence_notes",
            ],
            "properties": {
                "full_name": {"type": ["string", "null"]},
                "location_permission_granted": {"type": ["boolean", "null"]},
                "location_lat": {"type": ["string", "number", "null"]},
                "location_lng": {"type": ["string", "number", "null"]},
                "location_city": {"type": ["string", "null"]},
                "skills_description": {"type": ["string", "null"]},
                "evidence_notes": {"type": ["string", "null"]},
            },
        },
        "frontend_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "reason"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "request_location_permission",
                            "request_media_upload",
                            "none",
                        ],
                    },
                    "reason": {"type": ["string", "null"]},
                },
            },
        },
        "ready_to_complete": {
            "type": "boolean",
            "description": "True only when all required data seems present.",
        },
    },
}


SYSTEM_PROMPT = """
You are Qrib's onboarding agent.

Your job:
- First learn whether the user is a worker or looking for a worker.
- If the user is a worker, collect required worker profile fields.
- Required worker fields: full_name, location, skills_description.
- Ask one clear question at a time.
- Ask for location permission before location is collected.
- If location permission should be requested by the app, return a
  request_location_permission frontend action.
- Ask for skills as a natural story: what work they know how to do.
- Evidence notes are optional; mention photos/videos only after required fields.
- Do not mark ready_to_complete unless all required fields are present and
  plausible.
- A name should look like a person name, not a city, trade, or random number.
- If the user is looking for a worker, explain that customer flow is coming
  later and do not collect worker profile fields.

Return only the required structured JSON.
""".strip()

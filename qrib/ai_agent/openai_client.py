"""OpenAI client wrapper for the profile agent."""

import json

from django.conf import settings

from .schemas import AGENT_DECISION_SCHEMA
from .schemas import SYSTEM_PROMPT


class OpenAIProfileAgentClient:
    """Calls OpenAI and returns a strict agent decision."""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.QRIB_AGENT_MODEL

    def create_decision(self, state):
        """Returns the model's next structured decision."""
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            instructions=SYSTEM_PROMPT,
            input=[{
                "role": "user",
                "content": (
                    "Use this JSON state to decide the next response:\n"
                    f"{json.dumps(state, ensure_ascii=False)}"
                ),
            }],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "qrib_agent_decision",
                    "schema": AGENT_DECISION_SCHEMA,
                    "strict": True,
                }
            },
        )
        return json.loads(response.output_text)

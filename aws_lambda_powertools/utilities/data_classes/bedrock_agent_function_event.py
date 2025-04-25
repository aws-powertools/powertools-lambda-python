from __future__ import annotations

from typing import Any

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class BedrockAgentInfo(DictWrapper):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def id(self) -> str:  # noqa: A003
        return self["id"]

    @property
    def alias(self) -> str:
        return self["alias"]

    @property
    def version(self) -> str:
        return self["version"]


class BedrockAgentFunctionParameter(DictWrapper):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def type(self) -> str:  # noqa: A003
        return self["type"]

    @property
    def value(self) -> str:
        return self["value"]


class BedrockAgentFunctionEvent(DictWrapper):
    """
    Bedrock Agent Function input event

    Documentation:
    https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
    """

    @classmethod
    def validate_required_fields(cls, data: dict[str, Any]) -> None:
        required_fields = {
            "messageVersion": str,
            "agent": dict,
            "inputText": str,
            "sessionId": str,
            "actionGroup": str,
            "function": str,
        }

        for field, field_type in required_fields.items():
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(data[field], field_type):
                raise TypeError(f"Field {field} must be of type {field_type}")

        # Validate agent structure
        required_agent_fields = {"name", "id", "alias", "version"}
        if not all(field in data["agent"] for field in required_agent_fields):
            raise ValueError("Agent object missing required fields")

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self.validate_required_fields(data)

    @property
    def message_version(self) -> str:
        return self["messageVersion"]

    @property
    def input_text(self) -> str:
        return self["inputText"]

    @property
    def session_id(self) -> str:
        return self["sessionId"]

    @property
    def action_group(self) -> str:
        return self["actionGroup"]

    @property
    def function(self) -> str:
        return self["function"]

    @property
    def parameters(self) -> list[BedrockAgentFunctionParameter]:
        parameters = self.get("parameters") or []
        return [BedrockAgentFunctionParameter(x) for x in parameters]

    @property
    def agent(self) -> BedrockAgentInfo:
        return BedrockAgentInfo(self["agent"])

    @property
    def session_attributes(self) -> dict[str, str]:
        return self.get("sessionAttributes", {}) or {}

    @property
    def prompt_session_attributes(self) -> dict[str, str]:
        return self.get("promptSessionAttributes", {}) or {}

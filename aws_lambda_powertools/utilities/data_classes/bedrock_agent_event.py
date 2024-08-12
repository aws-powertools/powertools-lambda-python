from __future__ import annotations

from functools import cached_property
from typing import Any

from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent, DictWrapper


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


class BedrockAgentProperty(DictWrapper):
    @property
    def name(self) -> str:
        return self["name"]

    @property
    def type(self) -> str:  # noqa: A003
        return self["type"]

    @property
    def value(self) -> str:
        return self["value"]


class BedrockAgentRequestMedia(DictWrapper):
    @property
    def properties(self) -> list[BedrockAgentProperty]:
        return [BedrockAgentProperty(x) for x in self["properties"]]


class BedrockAgentRequestBody(DictWrapper):
    @property
    def content(self) -> dict[str, BedrockAgentRequestMedia]:
        return {k: BedrockAgentRequestMedia(v) for k, v in self["content"].items()}


class BedrockAgentEvent(BaseProxyEvent):
    """
    Bedrock Agent input event

    See https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html
    """

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
    def api_path(self) -> str:
        return self["apiPath"]

    @property
    def http_method(self) -> str:
        return self["httpMethod"]

    @property
    def parameters(self) -> list[BedrockAgentProperty]:
        parameters = self.get("parameters") or []
        return [BedrockAgentProperty(x) for x in parameters]

    @property
    def request_body(self) -> BedrockAgentRequestBody | None:
        return BedrockAgentRequestBody(self["requestBody"]) if self.get("requestBody") else None

    @property
    def agent(self) -> BedrockAgentInfo:
        return BedrockAgentInfo(self["agent"])

    @property
    def session_attributes(self) -> dict[str, str]:
        return self["sessionAttributes"]

    @property
    def prompt_session_attributes(self) -> dict[str, str]:
        return self["promptSessionAttributes"]

    # The following methods add compatibility with BaseProxyEvent
    @property
    def path(self) -> str:
        return self["apiPath"]

    @cached_property
    def query_string_parameters(self) -> dict[str, str]:
        # In Bedrock Agent events, query string parameters are passed as undifferentiated parameters,
        # together with the other parameters. So we just return all parameters here.
        parameters = self.get("parameters") or []
        return {x["name"]: x["value"] for x in parameters}

    @property
    def resolved_headers_field(self) -> dict[str, Any]:
        return {}

    @cached_property
    def json_body(self) -> Any:
        # In Bedrock Agent events, body parameters are encoded differently
        # @see https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html#agents-lambda-input
        if not self.request_body:
            return None

        json_body = self.request_body.content.get("application/json")
        if not json_body:
            return None

        return {x.name: x.value for x in json_body.properties}

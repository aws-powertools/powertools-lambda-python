from functools import cached_property
from typing import Any, Dict, List, Optional

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
    def properties(self) -> List[BedrockAgentProperty]:
        return [BedrockAgentProperty(x) for x in self["properties"]]


class BedrockAgentRequestBody(DictWrapper):
    @property
    def content(self) -> Dict[str, BedrockAgentRequestMedia]:
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
    def parameters(self) -> Optional[List[BedrockAgentProperty]]:
        return [BedrockAgentProperty(x) for x in self["parameters"]] if self.get("parameters") else None

    @property
    def request_body(self) -> Optional[BedrockAgentRequestBody]:
        return BedrockAgentRequestBody(self["requestBody"]) if self.get("requestBody") else None

    @property
    def agent(self) -> BedrockAgentInfo:
        return BedrockAgentInfo(self["agent"])

    @property
    def session_attributes(self) -> Dict[str, str]:
        return self["sessionAttributes"]

    @property
    def prompt_session_attributes(self) -> Dict[str, str]:
        return self["promptSessionAttributes"]

    # The following methods add compatibility with BaseProxyEvent
    @property
    def path(self) -> str:
        return self["apiPath"]

    @property
    def query_string_parameters(self) -> Optional[Dict[str, str]]:
        # In Bedrock Agent events, query string parameters are passed as undifferentiated parameters,
        # together with the other parameters. So we just return all parameters here.
        return {x["name"]: x["value"] for x in self["parameters"]} if self.get("parameters") else None

    @property
    def resolved_headers_field(self) -> Dict[str, Any]:
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

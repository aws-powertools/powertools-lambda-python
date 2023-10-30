from typing import Dict, List

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


class BedrockAgentActionGroup(DictWrapper):
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
    def parameters(self) -> List[BedrockAgentProperty]:
        return [BedrockAgentProperty(x) for x in self["parameters"]]

    @property
    def request_body(self) -> BedrockAgentRequestBody:
        return BedrockAgentRequestBody(self["requestBody"])


class BedrockAgentEvent(DictWrapper):
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
    def action_groups(self) -> List[BedrockAgentActionGroup]:
        return [BedrockAgentActionGroup(x) for x in self["actionGroups"]]

    @property
    def agent(self) -> BedrockAgentInfo:
        return BedrockAgentInfo(self["agent"])

    @property
    def session_attributes(self) -> Dict[str, str]:
        return self["sessionAttributes"]


class BedrockAgentResponseMedia(DictWrapper):
    @property
    def body(self) -> str:
        return self["body"]


class BedrockAgentResponsePayload(DictWrapper):
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
    def http_status_code(self) -> int:
        return self["httpStatusCode"]

    @property
    def response_body(self) -> Dict[str, BedrockAgentResponseMedia]:
        return {k: BedrockAgentResponseMedia(v) for k, v in self["responseBody"].items()}


class BedrockAgentResponseEvent(DictWrapper):
    """
    Bedrock Agent output event

    See: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-create.html
    """

    @property
    def message_version(self) -> str:
        return self["messageVersion"]

    @property
    def responses(self) -> List[BedrockAgentResponsePayload]:
        return [BedrockAgentResponsePayload(x) for x in self["response"]]

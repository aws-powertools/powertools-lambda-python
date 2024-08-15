from __future__ import annotations

from pydantic import BaseModel, Field


class BedrockAgentModel(BaseModel):
    name: str
    id_: str = Field(..., alias="id")
    alias: str
    version: str


class BedrockAgentPropertyModel(BaseModel):
    name: str
    type_: str = Field(..., alias="type")
    value: str


class BedrockAgentRequestMediaModel(BaseModel):
    properties: list[BedrockAgentPropertyModel]


class BedrockAgentRequestBodyModel(BaseModel):
    content: dict[str, BedrockAgentRequestMediaModel]


class BedrockAgentEventModel(BaseModel):
    message_version: str = Field(..., alias="messageVersion")
    input_text: str = Field(..., alias="inputText")
    session_id: str = Field(..., alias="sessionId")
    action_group: str = Field(..., alias="actionGroup")
    api_path: str = Field(..., alias="apiPath")
    http_method: str = Field(..., alias="httpMethod")
    session_attributes: dict[str, str] = Field({}, alias="sessionAttributes")
    prompt_session_attributes: dict[str, str] = Field({}, alias="promptSessionAttributes")
    agent: BedrockAgentModel
    parameters: list[BedrockAgentPropertyModel] | None = None
    request_body: BedrockAgentRequestBodyModel | None = Field(None, alias="requestBody")

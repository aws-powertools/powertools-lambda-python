from typing import Dict, List

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
    properties: List[BedrockAgentPropertyModel]


class BedrockAgentRequestBodyModel(BaseModel):
    content: Dict[str, BedrockAgentRequestMediaModel]


class BedrockAgentEventModel(BaseModel):
    message_version: str = Field(..., alias="messageVersion")
    input_text: str = Field(..., alias="inputText")
    session_id: str = Field(..., alias="sessionId")
    action_group: str = Field(..., alias="actionGroup")
    api_path: str = Field(..., alias="apiPath")
    http_method: str = Field(..., alias="httpMethod")
    session_attributes: Dict[str, str] = Field({}, alias="sessionAttributes")
    prompt_session_attributes: Dict[str, str] = Field({}, alias="promptSessionAttributes")
    agent: BedrockAgentModel
    parameters: List[BedrockAgentPropertyModel] | None = None
    request_body: BedrockAgentRequestBodyModel | None = Field(None, alias="requestBody")


class BedrockAgentFunctionEventModel(BaseModel):
    """Bedrock Agent Function event model

    Documentation:
    https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
    """

    message_version: str = Field(..., alias="messageVersion")
    agent: BedrockAgentModel
    input_text: str = Field(..., alias="inputText")
    session_id: str = Field(..., alias="sessionId")
    action_group: str = Field(..., alias="actionGroup")
    function: str
    parameters: List[BedrockAgentPropertyModel] | None = None
    session_attributes: Dict[str, str] = Field({}, alias="sessionAttributes")
    prompt_session_attributes: Dict[str, str] = Field({}, alias="promptSessionAttributes")

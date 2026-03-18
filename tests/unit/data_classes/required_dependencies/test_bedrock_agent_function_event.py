from __future__ import annotations

from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent
from tests.functional.utils import load_event


def test_bedrock_agent_function_event():
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    parsed_event = BedrockAgentFunctionEvent(raw_event)

    # Test basic event properties
    assert parsed_event.message_version == raw_event["messageVersion"]
    assert parsed_event.session_id == raw_event["sessionId"]
    assert parsed_event.input_text == raw_event["inputText"]
    assert parsed_event.action_group == raw_event["actionGroup"]
    assert parsed_event.function == raw_event["function"]

    # Test agent information
    agent = parsed_event.agent
    raw_agent = raw_event["agent"]
    assert agent.alias == raw_agent["alias"]
    assert agent.name == raw_agent["name"]
    assert agent.version == raw_agent["version"]
    assert agent.id == raw_agent["id"]

    # Test session attributes
    assert parsed_event.session_attributes == raw_event["sessionAttributes"]
    assert parsed_event.prompt_session_attributes == raw_event["promptSessionAttributes"]

    # Test parameters
    parameters = parsed_event.parameters
    raw_parameters = raw_event["parameters"]
    assert len(parameters) == len(raw_parameters)

    for param, raw_param in zip(parameters, raw_parameters, strict=False):
        assert param.name == raw_param["name"]
        assert param.type == raw_param["type"]
        assert param.value == raw_param["value"]


def test_bedrock_agent_function_event_minimal():
    """Test with minimal required fields"""
    minimal_event = {
        "messageVersion": "1.0",
        "agent": {
            "alias": "PROD",
            "name": "hr-assistant-function-def",
            "version": "1",
            "id": "1234abcd-56ef-78gh-90ij-klmn12345678",
        },
        "sessionId": "87654321-abcd-efgh-ijkl-mnop12345678",
        "inputText": "I want to request vacation",
        "actionGroup": "VacationsActionGroup",
        "function": "submitVacationRequest",
    }

    parsed_event = BedrockAgentFunctionEvent(minimal_event)

    assert parsed_event.session_attributes == {}
    assert parsed_event.prompt_session_attributes == {}
    assert parsed_event.parameters == []

from __future__ import annotations

import pytest

from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver, BedrockFunctionResponse
from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent
from tests.functional.utils import load_event


def test_bedrock_agent_function_with_string_response():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Returns a string")
    def test_function():
        assert isinstance(app.current_event, BedrockAgentFunctionEvent)
        return "Hello from string"

    # WHEN calling the event handler
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "test_function"
    result = app.resolve(raw_event, {})

    # THEN process event correctly with string response
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "test_function"
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == "Hello from string"
    assert "responseState" not in result["response"]["functionResponse"]


def test_bedrock_agent_function_error_handling():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Function with error handling")
    def error_function():
        return BedrockFunctionResponse(
            body="Invalid input",
            response_state="REPROMPT",
            session_attributes={"error": "true"},
        )

    @app.tool(description="Function that raises error")
    def exception_function():
        raise ValueError("Something went wrong")

    # WHEN calling with explicit error response
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "error_function"
    result = app.resolve(raw_event, {})

    # THEN include REPROMPT state and session attributes
    assert result["response"]["functionResponse"]["responseState"] == "REPROMPT"
    assert result["sessionAttributes"] == {"error": "true"}


def test_bedrock_agent_function_registration():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN registering without description or with duplicate name
    with pytest.raises(ValueError, match="Tool description is required"):

        @app.tool()
        def test_function():
            return "test"

    @app.tool(name="custom", description="First registration")
    def first_function():
        return "test"

    with pytest.raises(ValueError, match="Tool 'custom' already registered"):

        @app.tool(name="custom", description="Second registration")
        def second_function():
            return "test"


def test_bedrock_agent_function_with_optional_fields():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Function with all optional fields")
    def test_function():
        return BedrockFunctionResponse(
            body="Hello",
            session_attributes={"userId": "123"},
            prompt_session_attributes={"context": "test"},
            knowledge_bases=[
                {
                    "knowledgeBaseId": "kb1",
                    "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 5}},
                },
            ],
        )

    # WHEN calling the event handler
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "test_function"
    result = app.resolve(raw_event, {})

    # THEN include all optional fields in response
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == "Hello"
    assert result["sessionAttributes"] == {"userId": "123"}
    assert result["promptSessionAttributes"] == {"context": "test"}
    assert result["knowledgeBasesConfiguration"][0]["knowledgeBaseId"] == "kb1"


def test_bedrock_agent_function_invalid_event():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN calling with invalid event
    with pytest.raises(ValueError, match="Missing required field"):
        app.resolve({}, {})


def test_resolve_raises_value_error_on_missing_required_field():
    """Test that resolve() raises ValueError when a required field is missing from the event"""
    # GIVEN a Bedrock Agent Function resolver and an incomplete event
    resolver = BedrockAgentFunctionResolver()
    incomplete_event = {
        "messageVersion": "1.0",
        "agent": {"alias": "PROD", "name": "hr-assistant-function-def", "version": "1", "id": "1234abcd"},
        "sessionId": "123456789123458",
    }

    # WHEN calling resolve with the incomplete event
    # THEN a ValueError is raised with information about the missing field
    with pytest.raises(ValueError) as excinfo:
        resolver.resolve(incomplete_event, {})

    assert "Missing required field:" in str(excinfo.value)


def test_resolve_with_no_registered_function():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # AND a valid event but with a non-existent function
    raw_event = {
        "messageVersion": "1.0",
        "agent": {"name": "TestAgent", "id": "test-id", "alias": "test", "version": "1"},
        "actionGroup": "test_group",
        "function": "non_existent_function",
        "parameters": [],
    }

    # WHEN calling resolve with a non-existent function
    result = app.resolve(raw_event, {})

    # THEN the response should contain an error message
    assert "Error: 'non_existent_function'" in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]


def test_bedrock_function_response_state_validation():
    # GIVEN invalid and valid response states
    valid_states = [None, "FAILURE", "REPROMPT"]
    invalid_state = "INVALID"

    # WHEN creating responses with valid states
    # THEN no error should be raised
    for state in valid_states:
        try:
            BedrockFunctionResponse(body="test", response_state=state)
        except ValueError:
            pytest.fail(f"Unexpected ValueError for response_state={state}")

    # WHEN creating a response with invalid state
    # THEN ValueError should be raised with correct message
    with pytest.raises(ValueError) as exc_info:
        BedrockFunctionResponse(body="test", response_state=invalid_state)

    assert str(exc_info.value) == "responseState must be None, 'FAILURE' or 'REPROMPT'"

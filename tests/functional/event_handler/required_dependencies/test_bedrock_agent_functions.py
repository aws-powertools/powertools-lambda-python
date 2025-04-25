from __future__ import annotations

import json

import pytest

from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver, Response, content_types
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
    assert "responseState" not in result["response"]["functionResponse"]  # Success has no state


def test_bedrock_agent_function_with_error():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Function that raises error")
    def error_function():
        raise ValueError("Something went wrong")

    # WHEN calling the event handler with a function that raises an error
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "error_function"
    result = app.resolve(raw_event, {})

    # THEN process the error correctly
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "error_function"
    assert "Error: Something went wrong" in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert result["response"]["functionResponse"]["responseState"] == "FAILURE"


def test_bedrock_agent_function_not_found():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN calling the event handler with a non-existent function
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "nonexistent_function"
    result = app.resolve(raw_event, {})

    # THEN return function not found response with REPROMPT state
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "nonexistent_function"
    assert "Function not found" in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert result["response"]["functionResponse"]["responseState"] == "REPROMPT"


def test_bedrock_agent_function_with_response_object():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Returns a Response object")
    def test_function():
        return Response(
            status_code=200,
            content_type=content_types.APPLICATION_JSON,
            body={"message": "Hello from Response"},
        )

    # WHEN calling the event handler
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "test_function"
    result = app.resolve(raw_event, {})

    # THEN process event correctly with Response object
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "test_function"
    response_body = result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    assert json.loads(response_body) == {"message": "Hello from Response"}
    assert "responseState" not in result["response"]["functionResponse"]  # Success has no state


def test_bedrock_agent_function_registration():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN registering a tool without description
    # THEN raise ValueError
    with pytest.raises(ValueError, match="Tool description is required"):

        @app.tool()
        def test_function():
            return "test"

    # WHEN registering the same function twice
    # THEN raise ValueError
    @app.tool(description="First registration")
    def duplicate_function():
        return "test"

    with pytest.raises(ValueError, match="Tool 'duplicate_function' already registered"):

        @app.tool(description="Second registration")
        def duplicate_function():  # noqa: F811
            return "test"


def test_bedrock_agent_function_invalid_event():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN calling with invalid event
    # THEN raise ValueError
    with pytest.raises(ValueError, match="Missing required field"):
        app.resolve({}, {})

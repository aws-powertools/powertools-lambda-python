from __future__ import annotations

import pytest
from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver
from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent
from tests.functional.utils import load_event


def test_bedrock_agent_function():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Gets the current time")
    def get_current_time():
        assert isinstance(app.current_event, BedrockAgentFunctionEvent)
        return "2024-02-01T12:00:00Z"

    # WHEN calling the event handler
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "get_current_time"  # ensure function name matches
    result = app.resolve(raw_event, {})

    # THEN process event correctly
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "get_current_time"
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == "2024-02-01T12:00:00Z"


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


def test_bedrock_agent_function_not_found():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Test function")
    def test_function():
        return "test"

    # WHEN calling the event handler with a non-existent function
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "nonexistent_function"
    result = app.resolve(raw_event, {})

    # THEN return function not found response
    assert result["messageVersion"] == "1.0"
    assert result["response"]["actionGroup"] == raw_event["actionGroup"]
    assert result["response"]["function"] == "nonexistent_function"
    assert "Function not found" in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]


def test_bedrock_agent_function_missing_description():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN registering a tool without description
    # THEN raise ValueError
    with pytest.raises(ValueError, match="Tool description is required"):
        @app.tool()
        def test_function():
            return "test"


def test_bedrock_agent_function_duplicate_registration():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # WHEN registering the same function twice
    @app.tool(description="First registration")
    def test_function():
        return "test"

    # THEN raise ValueError on second registration
    with pytest.raises(ValueError, match="Tool 'test_function' already registered"):
        @app.tool(description="Second registration")
        def test_function():  # noqa: F811
            return "test"


def test_bedrock_agent_function_invalid_event():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Test function")
    def test_function():
        return "test"

    # WHEN calling with invalid event
    # THEN raise ValueError
    with pytest.raises(ValueError, match="Missing required field"):
        app.resolve({}, {})
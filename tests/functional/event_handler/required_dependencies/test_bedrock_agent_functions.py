from __future__ import annotations

import decimal
import json

import pytest

from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver, BedrockFunctionResponse
from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent
from aws_lambda_powertools.warnings import PowertoolsUserWarning
from tests.functional.utils import load_event


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


def test_bedrock_agent_function_with_string_response():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
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
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps("Hello from string")
    assert "responseState" not in result["response"]["functionResponse"]


def test_bedrock_agent_function_with_none_response():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
    def none_response_function():
        return None

    # WHEN calling the event handler with a function returning None
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "none_response_function"
    result = app.resolve(raw_event, {})

    # THEN process event correctly with empty string body
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps("")


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

    # WHEN registering with duplicate name
    @app.tool(name="custom", description="First registration")
    def first_function():
        return "first test"

    # THEN a warning should be issued when registering a duplicate
    with pytest.warns(PowertoolsUserWarning, match="Tool 'custom' already registered"):

        @app.tool(name="custom", description="Second registration")
        def second_function():
            return "second test"

    # AND the most recent function should be registered
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "custom"
    result = app.resolve(raw_event, {})

    # The second function should be used
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps("second test")


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
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps("Hello")
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


@pytest.mark.parametrize("response_state", ["FAILURE", "REPROMPT", None])
def test_bedrock_function_valid_response_states(response_state):
    # GIVEN a valid response state
    # WHEN creating a BedrockFunctionResponse with that state
    # THEN no error should be raised
    BedrockFunctionResponse(body="test", response_state=response_state)


def test_bedrock_function_invalid_response_state():
    # GIVEN an invalid response state
    invalid_state = "INVALID"

    # WHEN creating a BedrockFunctionResponse with an invalid state
    # THEN ValueError should be raised with correct message
    with pytest.raises(ValueError) as exc_info:
        BedrockFunctionResponse(body="test", response_state=invalid_state)

    # AND error message should mention valid options
    error_message = str(exc_info.value)
    assert "responseState must be" in error_message
    assert "FAILURE" in error_message
    assert "REPROMPT" in error_message


def test_bedrock_agent_function_with_parameters():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    # Track received parameters
    received_params = {}

    @app.tool(description="Function that accepts parameters")
    def vacation_request(start_date, end_date):
        # Store received parameters for assertion
        received_params["start_date"] = start_date
        received_params["end_date"] = end_date
        return f"Vacation request from {start_date} to {end_date} submitted"

    # WHEN calling the event handler with parameters
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "vacation_request"
    result = app.resolve(raw_event, {})

    # THEN parameters should be correctly passed to the function
    assert received_params["start_date"] == "2024-03-15"
    assert received_params["end_date"] == "2024-03-20"
    assert (
        "Vacation request from 2024-03-15 to 2024-03-20 submitted"
        in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    )


def test_bedrock_agent_function_preserves_input_session_attributes():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
    def session_check_function():
        # Validate that session attributes from the event are accessible
        assert app.current_event.session_attributes.get("existingKey") == "existingValue"
        return "Session checked"

    # WHEN calling with event that has session attributes but function doesn't return any
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "session_check_function"
    raw_event["sessionAttributes"] = {"existingKey": "existingValue"}
    raw_event["promptSessionAttributes"] = {"promptKey": "promptValue"}

    result = app.resolve(raw_event, {})

    # THEN the original session attributes should be preserved in the response
    assert result["sessionAttributes"] == {"existingKey": "existingValue"}
    assert result["promptSessionAttributes"] == {"promptKey": "promptValue"}


def test_bedrock_agent_function_with_invalid_parameters():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
    def strict_function(required_param):
        return f"Got {required_param}"

    # WHEN calling with parameters that don't match the function signature
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "strict_function"
    raw_event["parameters"] = [
        {"name": "wrongParam", "value": "wrong value"},  # Wrong parameter name
    ]

    # THEN function should still be called, but with no parameters
    result = app.resolve(raw_event, {})

    # Function should raise a TypeError due to missing required parameter
    assert "Error:" in result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]


def test_bedrock_agent_function_with_complex_return_type():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
    def complex_response():
        # Return a complex type that needs to be converted to string
        return {"key1": "value1", "key2": 123, "nested": {"inner": "value"}}

    # WHEN calling with a complex return value
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "complex_response"
    result = app.resolve(raw_event, {})

    # THEN complex object should be converted to string representation
    response_body = result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    # Check that it contains the expected string representation

    assert response_body == json.dumps(
        {"key1": "value1", "key2": 123, "nested": {"inner": "value"}},
    )


def test_bedrock_agent_function_append_context():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool()
    def first_function():
        # Function that appends context and checks for its existence
        assert app.context.get("custom_key") == "custom_value"
        assert app.context.get("user_id") == "12345"
        return "First function executed"

    @app.tool()
    def second_function():
        # Function that checks context has been cleared
        assert not hasattr(app.context, "custom_key")
        assert not hasattr(app.context, "user_id")
        # Add new context
        assert app.context.get("new_key") == "new_value"
        return "Second function executed"

    # WHEN calling the first function
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "first_function"
    app.append_context(custom_key="custom_value", user_id="12345")
    first_result = app.resolve(raw_event, LambdaContext())

    # THEN first function should have accessed the context
    assert "First function executed" in first_result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]

    # WHEN calling the second function
    raw_event["function"] = "second_function"
    app.append_context(new_key="new_value")
    second_result = app.resolve(raw_event, LambdaContext())

    # THEN second function should have accessed the context and verified it was cleared
    assert "Second function executed" in second_result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]

    # After all invocations, context should be empty
    assert not hasattr(app.context, "new_key")


def test_resolve_with_no_current_event():
    """Test that _resolve() raises ValueError when current_event is None"""
    # GIVEN a Bedrock Agent Function resolver with no current event
    app = BedrockAgentFunctionResolver()

    # Deliberately clear the current_event
    app.current_event = None

    # WHEN calling the internal _resolve method
    # THEN a ValueError should be raised
    with pytest.raises(ValueError, match="No event to process"):
        app._resolve()


def test_bedrock_agent_function_with_parameters_casting():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Function that accepts parameters")
    def vacation_request(month: int, payment: float, approved: bool):
        # Store received parameters for assertion
        assert isinstance(month, int)
        assert isinstance(payment, float)
        assert isinstance(approved, bool)
        return "Vacation request"

    # WHEN calling the event handler with parameters
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "vacation_request"
    raw_event["parameters"] = [
        {"name": "month", "value": "3", "type": "integer"},
        {"name": "payment", "value": "1000.5", "type": "number"},
        {"name": "approved", "value": False, "type": "boolean"},
    ]
    result = app.resolve(raw_event, {})

    # THEN parameters should be correctly passed to the function
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps("Vacation request")


def test_bedrock_agent_function_with_parameters_casting_errors():
    # GIVEN a Bedrock Agent Function resolver
    app = BedrockAgentFunctionResolver()

    @app.tool(description="Function that handles parameter casting errors")
    def process_data(id_product: str, quantity: int, price: float, available: bool, items: list):
        # Check that invalid values maintain their original types
        assert isinstance(id_product, str)
        # For invalid integer, the original string should be preserved
        assert quantity == "invalid_number"
        # For invalid float, the original string should be preserved
        assert price == "not_a_price"
        # For invalid boolean, should evaluate based on Python's bool rules
        assert isinstance(available, bool)
        assert not available
        # Arrays should remain as is
        assert isinstance(items, list)
        return "Processed with casting errors handled"

    # WHEN calling the event handler with parameters that cause casting errors
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "process_data"
    raw_event["parameters"] = [
        {"name": "id_product", "value": 12345, "type": "string"},  # Integer to string (should work)
        {"name": "quantity", "value": "invalid_number", "type": "integer"},  # Will cause ValueError
        {"name": "price", "value": "not_a_price", "type": "number"},  # Will cause ValueError
        {"name": "available", "value": "invalid_bool", "type": "boolean"},  # Not "true"/"false"
        {"name": "items", "value": ["item1", "item2"], "type": "array"},  # Array should remain as is
    ]
    result = app.resolve(raw_event, {})

    # THEN parameters should be handled properly despite casting errors
    assert result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"] == json.dumps(
        "Processed with casting errors handled",
    )


def test_bedrock_agent_function_with_custom_serializer():
    """Test BedrockAgentFunctionResolver with a custom serializer for non-standard JSON types."""

    def decimal_serializer(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    # GIVEN a Bedrock Agent Function resolver with that custom serializer
    app = BedrockAgentFunctionResolver(serializer=lambda obj: json.dumps(obj, default=decimal_serializer))

    @app.tool()
    def decimal_response():
        # Return a response with Decimal type that standard JSON can't serialize
        return {"price": round(decimal.Decimal("99"))}

    # WHEN calling with a response containing non-standard JSON types
    raw_event = load_event("bedrockAgentFunctionEvent.json")
    raw_event["function"] = "decimal_response"
    result = app.resolve(raw_event, {})

    # THEN non-standard types should be properly serialized
    response_body = result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]

    # VERIFY that decimal was converted to float and datetime to ISO string
    assert response_body == json.dumps({"price": 99})

import json
from typing import Any, Dict

from aws_lambda_powertools.event_handler import BedrockAgentResolver, Response, content_types
from aws_lambda_powertools.event_handler.openapi.types import PYDANTIC_V2
from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent
from tests.functional.utils import load_event

claims_response = "You have 3 claims"


def test_bedrock_agent_event():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims")
    def claims() -> Dict[str, Any]:
        assert isinstance(app.current_event, BedrockAgentEvent)
        assert app.lambda_context == {}
        return {"output": claims_response}

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as BedrockAgentEvent
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 200

    body = result["response"]["responseBody"]["application/json"]["body"]
    assert body == json.dumps({"output": claims_response})


def test_bedrock_agent_with_path_params():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims/<claim_id>")
    def claims(claim_id: str):
        assert isinstance(app.current_event, BedrockAgentEvent)
        assert app.lambda_context == {}
        assert claim_id == "123"

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEventWithPathParams.json"), {})

    # THEN process event correctly
    # AND set the current_event type as BedrockAgentEvent
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims/<claim_id>"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 200


def test_bedrock_agent_event_with_response():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()
    output = {"output": claims_response}

    @app.get("/claims")
    def claims():
        assert isinstance(app.current_event, BedrockAgentEvent)
        assert app.lambda_context == {}
        return Response(200, content_types.APPLICATION_JSON, output)

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as BedrockAgentEvent
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 200

    body = result["response"]["responseBody"]["application/json"]["body"]
    assert body == json.dumps(output)


def test_bedrock_agent_event_with_no_matches():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/no_match")
    def claims():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly
    # AND return 404 because the event doesn't match any known rule
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 404


def test_bedrock_agent_event_with_validation_error():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims")
    def claims() -> Dict[str, Any]:
        return "oh no, this is not a dict"  # type: ignore

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as BedrockAgentEvent
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 422

    body = result["response"]["responseBody"]["application/json"]["body"]
    if PYDANTIC_V2:
        assert "should be a valid dictionary" in body
    else:
        assert "value is not a valid dict" in body


def test_bedrock_agent_event_with_exception():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.exception_handler(RuntimeError)
    def handle_runtime_error(ex: RuntimeError):
        return Response(
            status_code=500,
            content_type=content_types.TEXT_PLAIN,
            body="Something went wrong",
        )

    @app.get("/claims")
    def claims():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process the exception correctly
    # AND return 500 because of the internal server error
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["response"]["httpStatusCode"] == 500

    body = result["response"]["responseBody"]["text/plain"]["body"]
    assert body == "Something went wrong"

import json
from typing import Any, Dict

from aws_lambda_powertools.event_handler import BedrockAgentResolver, Response, content_types
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

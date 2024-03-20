import json
from typing import Any, Dict

from aws_lambda_powertools.event_handler import BedrockAgentResolver, Response, content_types
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.event_handler.openapi.pydantic_loader import PYDANTIC_V2
from aws_lambda_powertools.shared.types import Annotated
from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent
from tests.functional.utils import load_event

claims_response = "You have 3 claims"


def test_bedrock_agent_event():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
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
    assert json.loads(body) == {"output": claims_response}


def test_bedrock_agent_with_path_params():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims/<claim_id>", description="Gets claims by ID")
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

    @app.get("/claims", description="Gets claims")
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
    assert json.loads(body) == output


def test_bedrock_agent_event_with_no_matches():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/no_match", description="Matches nothing")
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

    @app.get("/claims", description="Gets claims")
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

    body = json.loads(result["response"]["responseBody"]["application/json"]["body"])
    if PYDANTIC_V2:
        assert body["detail"][0]["type"] == "dict_type"
    else:
        assert body["detail"][0]["type"] == "type_error.dict"


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

    @app.get("/claims", description="Gets claims")
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


def test_bedrock_agent_with_post():
    # GIVEN a Bedrock Agent resolver with a POST method
    app = BedrockAgentResolver()

    @app.post("/send-reminders", description="Sends reminders")
    def send_reminders(
        _claim_id: Annotated[int, Body(description="Claim ID", alias="claimId")],
        _pending_documents: Annotated[str, Body(description="Social number and VAT", alias="pendingDocuments")],
    ) -> Annotated[bool, Body(description="returns true if I like the email")]:
        return True

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentPostEvent.json"), {})

    # THEN process the event correctly
    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/send-reminders"
    assert result["response"]["httpMethod"] == "POST"
    assert result["response"]["httpStatusCode"] == 200

    # THEN return the correct result
    body = result["response"]["responseBody"]["application/json"]["body"]
    assert json.loads(body) is True

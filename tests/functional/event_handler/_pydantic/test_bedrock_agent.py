import json
from functools import partial
from typing import Any, Dict, Optional

import pytest
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import BedrockAgentResolver, BedrockResponse, Response, content_types
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
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
    assert body["detail"][0]["type"] == "dict_type"


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


@pytest.mark.usefixtures("pydanticv2_only")
def test_openapi_schema_for_pydanticv2(openapi30_schema):
    # GIVEN BedrockAgentResolver is initialized with enable_validation=True
    app = BedrockAgentResolver(enable_validation=True)

    # WHEN we have a simple handler
    @app.get("/", description="Testing")
    def handler() -> Optional[Dict]:
        pass

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the schema must be a valid 3.0.3 version
    assert openapi30_schema(schema)
    assert schema.get("openapi") == "3.0.3"


def test_bedrock_agent_with_bedrock_response():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    # WHEN using BedrockResponse
    @app.get("/claims", description="Gets claims")
    def claims():
        assert isinstance(app.current_event, BedrockAgentEvent)
        assert app.lambda_context == {}
        return BedrockResponse(
            session_attributes={"user_id": "123"},
            prompt_session_attributes={"context": "testing"},
            knowledge_bases_configuration=[
                {
                    "knowledgeBaseId": "kb-123",
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 3, "overrideSearchType": "HYBRID"},
                    },
                },
            ],
        )

    result = app(load_event("bedrockAgentEvent.json"), {})

    assert result["messageVersion"] == "1.0"
    assert result["response"]["apiPath"] == "/claims"
    assert result["response"]["actionGroup"] == "ClaimManagementActionGroup"
    assert result["response"]["httpMethod"] == "GET"
    assert result["sessionAttributes"] == {"user_id": "123"}
    assert result["promptSessionAttributes"] == {"context": "testing"}
    assert result["knowledgeBasesConfiguration"] == [
        {
            "knowledgeBaseId": "kb-123",
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {"numberOfResults": 3, "overrideSearchType": "HYBRID"},
            },
        },
    ]


def test_bedrock_agent_with_empty_bedrock_response():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
    def claims():
        return BedrockResponse(body={"message": "test"})

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly without optional attributes
    assert result["messageVersion"] == "1.0"
    assert result["response"]["httpStatusCode"] == 200
    assert "sessionAttributes" not in result
    assert "promptSessionAttributes" not in result
    assert "knowledgeBasesConfiguration" not in result


def test_bedrock_agent_with_partial_bedrock_response():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
    def claims() -> Dict[str, Any]:
        return BedrockResponse(
            body={"message": "test"},
            session_attributes={"user_id": "123"},
            # Only include session_attributes to test partial response
        )

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly with only session_attributes
    assert result["messageVersion"] == "1.0"
    assert result["response"]["httpStatusCode"] == 200
    assert result["sessionAttributes"] == {"user_id": "123"}
    assert "promptSessionAttributes" not in result
    assert "knowledgeBasesConfiguration" not in result


def test_bedrock_agent_with_string():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
    def claims() -> str:
        return "a"

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly with only session_attributes
    assert result["messageVersion"] == "1.0"
    assert result["response"]["httpStatusCode"] == 200


def test_bedrock_agent_with_different_attributes_combination():
    # GIVEN a Bedrock Agent event
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
    def claims() -> Dict[str, Any]:
        return BedrockResponse(
            body={"message": "test"},
            prompt_session_attributes={"context": "testing"},
            knowledge_bases_configuration=[
                {
                    "knowledgeBaseId": "kb-123",
                    "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 3}},
                },
            ],
            # Omit session_attributes to test different combination
        )

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN process event correctly with specific attributes
    assert result["messageVersion"] == "1.0"
    assert result["response"]["httpStatusCode"] == 200
    assert "sessionAttributes" not in result
    assert result["promptSessionAttributes"] == {"context": "testing"}
    assert result["knowledgeBasesConfiguration"][0]["knowledgeBaseId"] == "kb-123"


def test_bedrock_resolver_with_openapi_extensions():
    # GIVEN BedrockAgentResolver is initialized with enable_validation=True
    app = BedrockAgentResolver(enable_validation=True)

    # WHEN we have a simple handler with openapi extension
    @app.get("/", description="Testing", openapi_extensions={"x-requireConfirmation": "ENABLED"})
    def handler() -> Optional[Dict]:
        pass

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the OpenAPI schema must contain the "x-requireConfirmation" extension at the operation level
    assert schema["paths"]["/"]["get"]["x-requireConfirmation"] == "ENABLED"


def test_bedrock_agent_with_comma_parameters():
    # GIVEN a Bedrock Agent resolver
    app = BedrockAgentResolver()

    @app.post("/sql-query", description="Run a SQL query")
    def run_sql_query(query: Annotated[str, Query()]):
        return {"result": query}

    # WHEN calling the event handler with a parameter containing commas
    event = {
        "actionGroup": "TestActionGroup",
        "messageVersion": "1.0",
        "sessionId": "12345678912345",
        "sessionAttributes": {},
        "promptSessionAttributes": {},
        "inputText": "Run a SQL query",
        "agent": {
            "alias": "TEST",
            "name": "test",
            "version": "1",
            "id": "test123",
        },
        "httpMethod": "POST",
        "apiPath": "/sql-query",
        "parameters": [
            {
                "name": "query",
                "type": "string",
                "value": "SELECT a.source_name, b.thing FROM table",
            },
        ],
    }

    result = app(event, {})

    # THEN the parameter with commas should be correctly passed to the handler
    body = json.loads(result["response"]["responseBody"]["application/json"]["body"])
    assert body["result"] == "SELECT a.source_name, b.thing FROM table"


def test_bedrock_agent_with_default_serializer_escapes_non_ascii():
    # GIVEN a Bedrock Agent resolver using the default serializer
    app = BedrockAgentResolver()

    @app.get("/claims", description="Gets claims")
    def claims() -> Dict[str, Any]:
        return {"output": "잔액은 1,000원입니다 💰"}

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN the body is valid JSON and non-ASCII characters are escaped (default json.dumps behavior)
    body = result["response"]["responseBody"]["application/json"]["body"]
    assert "\\uc794" in body  # "잔" escaped
    assert json.loads(body) == {"output": "잔액은 1,000원입니다 💰"}


def test_bedrock_agent_with_custom_serializer_preserves_non_ascii():
    # GIVEN a Bedrock Agent resolver initialized with a custom serializer that keeps non-ASCII characters
    app = BedrockAgentResolver(serializer=partial(json.dumps, ensure_ascii=False))

    @app.get("/claims", description="Gets claims")
    def claims() -> Dict[str, Any]:
        return {"output": "잔액은 1,000원입니다 💰"}

    # WHEN calling the event handler
    result = app(load_event("bedrockAgentEvent.json"), {})

    # THEN the non-ASCII characters are preserved verbatim in the response body
    body = result["response"]["responseBody"]["application/json"]["body"]
    assert "잔액은 1,000원입니다 💰" in body
    assert json.loads(body) == {"output": "잔액은 1,000원입니다 💰"}

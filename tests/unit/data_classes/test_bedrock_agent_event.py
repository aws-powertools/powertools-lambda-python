from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent
from tests.functional.utils import load_event


def test_bedrock_agent_event():
    raw_event = load_event("bedrockAgentEvent.json")
    parsed_event = BedrockAgentEvent(raw_event)

    assert parsed_event.session_id == "12345678912345"
    assert parsed_event.input_text == "I want to claim my insurance"
    assert parsed_event.message_version == "1.0"
    assert parsed_event.http_method == "GET"
    assert parsed_event.api_path == "/claims"
    assert parsed_event.session_attributes == {}
    assert parsed_event.prompt_session_attributes == {}
    assert parsed_event.action_group == "ClaimManagementActionGroup"

    agent = parsed_event.agent
    assert agent.alias == "TSTALIASID"
    assert agent.name == "test"
    assert agent.version == "DRAFT"
    assert agent.id == "8ZXY0W8P1H"


def test_bedrock_agent_event_with_post():
    raw_event = load_event("bedrockAgentPostEvent.json")
    parsed_event = BedrockAgentEvent(raw_event)

    assert parsed_event.session_id == "12345678912345"
    assert parsed_event.input_text == "Send reminders to all pending documents"
    assert parsed_event.message_version == "1.0"
    assert parsed_event.http_method == "POST"
    assert parsed_event.api_path == "/send-reminders"
    assert parsed_event.session_attributes == {}
    assert parsed_event.prompt_session_attributes == {}
    assert parsed_event.action_group == "ClaimManagementActionGroup"

    agent = parsed_event.agent
    assert agent.alias == "TSTALIASID"
    assert agent.name == "test"
    assert agent.version == "DRAFT"
    assert agent.id == "8ZXY0W8P1H"

    request_body = parsed_event.request_body.content
    assert "application/json" in request_body

    json_request = request_body["application/json"]
    properties = json_request.properties
    assert len(properties) == 2

    assert properties[0].name == "claimId"
    assert properties[0].type == "string"
    assert properties[0].value == "20"

    assert properties[1].name == "pendingDocuments"
    assert properties[1].type == "string"
    assert properties[1].value == "social number and vat"

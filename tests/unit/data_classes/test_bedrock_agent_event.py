from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent, BedrockAgentResponseEvent
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


def test_bedrock_agent_response_event():
    raw_event = load_event("bedrockAgentResponseEvent.json")
    parsed_event = BedrockAgentResponseEvent(raw_event)

    assert parsed_event.message_version == "1.0"

    assert parsed_event.response.action_group == "ClaimManagementActionGroup"
    assert parsed_event.response.api_path == "/claims/{claimId}/identify-missing-documents"
    assert parsed_event.response.http_method == "GET"
    assert parsed_event.response.http_status_code == 200

    response_body = parsed_event.response.response_body
    assert "application/json" in response_body

    json_response = response_body["application/json"]
    assert json_response.body == "This is the response"

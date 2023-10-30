from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent, BedrockAgentResponseEvent
from tests.functional.utils import load_event


def test_bedrock_agent_event():
    raw_event = load_event("bedrockAgentEvent.json")
    parsed_event = BedrockAgentEvent(raw_event)

    assert parsed_event.session_id == "12345678912345"
    assert parsed_event.input_text == "ABC12345"
    assert parsed_event.session_attributes == {}
    assert parsed_event.message_version == "1.0"

    agent = parsed_event.agent
    assert agent.alias == "TSTALIASID"
    assert agent.name == "test"
    assert agent.version == "DRAFT"
    assert agent.id == "8ZXY0W8P1H"

    action_groups = parsed_event.action_groups
    assert len(action_groups) == 1

    action_group = action_groups[0]
    assert action_group.http_method == "GET"
    assert action_group.api_path == "/claims/{claimId}/identify-missing-documents"
    assert action_group.action_group == "ClaimManagementActionGroup"

    parameters = action_group.parameters
    assert len(parameters) == 1

    parameter = parameters[0]
    assert parameter.name == "claimId"
    assert parameter.type == "string"
    assert parameter.value == "ABC12345"


def test_bedrock_agent_response_event():
    raw_event = load_event("bedrockAgentResponseEvent.json")
    parsed_event = BedrockAgentResponseEvent(raw_event)

    assert parsed_event.message_version == "1.0"

    responses = parsed_event.responses
    assert len(responses) == 1

    response = responses[0]
    assert response.action_group == "ClaimManagementActionGroup"
    assert response.api_path == "/claims/{claimId}/identify-missing-documents"
    assert response.http_method == "GET"
    assert response.http_status_code == 200

    response_body = response.response_body
    assert "application/json" in response_body

    json_response = response_body["application/json"]
    assert json_response.body == "This is the response"

from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent
from tests.functional.utils import load_event


def test_bedrock_agent_event():
    raw_event = load_event("bedrockAgentEvent.json")
    parsed_event = BedrockAgentEvent(raw_event)

    assert parsed_event.session_id == raw_event["sessionId"]
    assert parsed_event.input_text == raw_event["inputText"]
    assert parsed_event.message_version == raw_event["messageVersion"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.api_path == raw_event["apiPath"]
    assert parsed_event.session_attributes == {}
    assert parsed_event.prompt_session_attributes == {}
    assert parsed_event.action_group == raw_event["actionGroup"]

    assert parsed_event.request_body is None

    agent = parsed_event.agent
    raw_agent = raw_event["agent"]
    assert agent.alias == raw_agent["alias"]
    assert agent.name == raw_agent["name"]
    assert agent.version == raw_agent["version"]
    assert agent.id == raw_agent["id"]


def test_bedrock_agent_event_with_post():
    raw_event = load_event("bedrockAgentPostEvent.json")
    parsed_event = BedrockAgentEvent(raw_event)

    assert parsed_event.session_id == raw_event["sessionId"]
    assert parsed_event.input_text == raw_event["inputText"]
    assert parsed_event.message_version == raw_event["messageVersion"]
    assert parsed_event.http_method == raw_event["httpMethod"]
    assert parsed_event.api_path == raw_event["apiPath"]
    assert parsed_event.session_attributes == {}
    assert parsed_event.prompt_session_attributes == {}
    assert parsed_event.action_group == raw_event["actionGroup"]

    agent = parsed_event.agent
    raw_agent = raw_event["agent"]
    assert agent.alias == raw_agent["alias"]
    assert agent.name == raw_agent["name"]
    assert agent.version == raw_agent["version"]
    assert agent.id == raw_agent["id"]

    request_body = parsed_event.request_body.content
    assert "application/json" in request_body

    json_request = request_body["application/json"]
    properties = json_request.properties
    assert len(properties) == 2

    raw_properties = raw_event["requestBody"]["content"]["application/json"]["properties"]
    assert properties[0].name == raw_properties[0]["name"]
    assert properties[0].type == raw_properties[0]["type"]
    assert properties[0].value == raw_properties[0]["value"]

    assert properties[1].name == raw_properties[1]["name"]
    assert properties[1].type == raw_properties[1]["type"]
    assert properties[1].value == raw_properties[1]["value"]

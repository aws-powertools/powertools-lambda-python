from aws_lambda_powertools.utilities.parser import envelopes, parse
from aws_lambda_powertools.utilities.parser.models import BedrockAgentEventModel
from tests.functional.utils import load_event
from tests.unit.parser.schemas import MyBedrockAgentBusiness


def test_bedrock_agent_event_with_envelope():
    raw_event = load_event("bedrockAgentEvent.json")
    raw_event["inputText"] = '{"username": "Ruben", "name": "Fonseca"}'
    parsed_event: MyBedrockAgentBusiness = parse(
        event=raw_event,
        model=MyBedrockAgentBusiness,
        envelope=envelopes.BedrockAgentEnvelope,
    )

    assert parsed_event.username == "Ruben"
    assert parsed_event.name == "Fonseca"


def test_bedrock_agent_event():
    raw_event = load_event("bedrockAgentEvent.json")
    model = BedrockAgentEventModel(**raw_event)

    assert model.message_version == raw_event["messageVersion"]
    assert model.session_id == raw_event["sessionId"]
    assert model.input_text == raw_event["inputText"]
    assert model.message_version == raw_event["messageVersion"]
    assert model.http_method == raw_event["httpMethod"]
    assert model.api_path == raw_event["apiPath"]
    assert model.session_attributes == {}
    assert model.prompt_session_attributes == {}
    assert model.action_group == raw_event["actionGroup"]

    assert model.request_body is None

    agent = model.agent
    raw_agent = raw_event["agent"]
    assert agent.alias == raw_agent["alias"]
    assert agent.name == raw_agent["name"]
    assert agent.version == raw_agent["version"]
    assert agent.id_ == raw_agent["id"]


def test_bedrock_agent_event_with_post():
    raw_event = load_event("bedrockAgentPostEvent.json")
    model = BedrockAgentEventModel(**raw_event)

    assert model.session_id == raw_event["sessionId"]
    assert model.input_text == raw_event["inputText"]
    assert model.message_version == raw_event["messageVersion"]
    assert model.http_method == raw_event["httpMethod"]
    assert model.api_path == raw_event["apiPath"]
    assert model.session_attributes == {}
    assert model.prompt_session_attributes == {}
    assert model.action_group == raw_event["actionGroup"]

    agent = model.agent
    raw_agent = raw_event["agent"]
    assert agent.alias == raw_agent["alias"]
    assert agent.name == raw_agent["name"]
    assert agent.version == raw_agent["version"]
    assert agent.id_ == raw_agent["id"]

    request_body = model.request_body.content
    assert "application/json" in request_body

    json_request = request_body["application/json"]
    properties = json_request.properties
    assert len(properties) == 2

    raw_properties = raw_event["requestBody"]["content"]["application/json"]["properties"]
    assert properties[0].name == raw_properties[0]["name"]
    assert properties[0].type_ == raw_properties[0]["type"]
    assert properties[0].value == raw_properties[0]["value"]

    assert properties[1].name == raw_properties[1]["name"]
    assert properties[1].type_ == raw_properties[1]["type"]
    assert properties[1].value == raw_properties[1]["value"]

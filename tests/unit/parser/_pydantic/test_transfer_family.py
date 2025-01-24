from aws_lambda_powertools.utilities.parser.models import TransferFamilyAuthorizer
from tests.functional.utils import load_event


def test_transfer_family_authorizer_model():
    raw_event = load_event("transferFamilyAuthorizer.json")
    parsed_event = TransferFamilyAuthorizer(**raw_event)

    assert parsed_event.username == raw_event["username"]
    assert parsed_event.password == raw_event["password"]
    assert parsed_event.protocol == raw_event["protocol"]
    assert parsed_event.server_id == raw_event["serverId"]
    assert str(parsed_event.source_ip) == raw_event["sourceIp"]


def test_transfer_family_authorizer_model_without_password():
    raw_event = load_event("transferFamilyAuthorizer.json")
    del raw_event["password"]
    parsed_event = TransferFamilyAuthorizer(**raw_event)

    assert parsed_event.username == raw_event["username"]
    assert parsed_event.password is None
    assert parsed_event.protocol == raw_event["protocol"]
    assert parsed_event.server_id == raw_event["serverId"]
    assert str(parsed_event.source_ip) == raw_event["sourceIp"]

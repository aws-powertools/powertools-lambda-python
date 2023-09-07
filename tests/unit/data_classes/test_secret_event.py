from aws_lambda_powertools.utilities.data_classes.secrets_event import SecretManagerEvent
from tests.functional.utils import load_event


def test_vpc_lattice_event():
    raw_event = load_event("secretManagerEvent.json")
    parsed_event = SecretManagerEvent(raw_event)

    assert parsed_event.secret_id == raw_event["SecretId"]
    assert parsed_event.client_request_token == raw_event["ClientRequestToken"]
    assert parsed_event.step == raw_event["Step"]

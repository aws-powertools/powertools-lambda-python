from aws_lambda_powertools.utilities.data_classes.secrets_manager_event import SecretsManagerEvent
from tests.functional.utils import load_event


def test_secrets_manager_event():
    raw_event = load_event("secretsManagerEvent.json")
    parsed_event = SecretsManagerEvent(raw_event)

    assert parsed_event.secret_id == raw_event["SecretId"]
    assert parsed_event.client_request_token == raw_event["ClientRequestToken"]
    assert parsed_event.version_id == raw_event["ClientRequestToken"]
    assert parsed_event.step == raw_event["Step"]

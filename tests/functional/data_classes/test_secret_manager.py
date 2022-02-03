import pytest

from aws_lambda_powertools.utilities.data_classes.secret_manager import (
    SecretsManagerRotationEvent,
    SecretsManagerRotationEventStep,
)
from tests.functional.utils import load_event


def test_secrets_manager_rotation_event_step_invalid():
    # GIVEN an invalid step
    # WHEN calling from_str
    # THEN raise a ValueError
    with pytest.raises(ValueError) as exp:
        SecretsManagerRotationEventStep.from_str("unknown")
    assert str(exp.value) == "Invalid step: unknown"


def test_secrets_manager_rotation_event_step_valid():
    # GIVEN all values of SecretsManagerRotationEventStep
    # WHEN calling from_str
    # THEN match the lookup by name
    for item in SecretsManagerRotationEventStep:
        assert SecretsManagerRotationEventStep.from_str(item.value) == SecretsManagerRotationEventStep[item.name]


@pytest.mark.parametrize(
    "value",
    argvalues=[
        pytest.param(("createSecret", SecretsManagerRotationEventStep.CREATE_SECRET), id="CREATE_SECRET"),
        pytest.param(("setSecret", SecretsManagerRotationEventStep.SET_SECRET), id="SET_SECRET"),
        pytest.param(("testSecret", SecretsManagerRotationEventStep.TEST_SECRET), id="TEST_SECRET"),
        pytest.param(("finishSecret", SecretsManagerRotationEventStep.FINISH_SECRET), id="FINISH_SECRET"),
    ],
)
def test_secrets_manager_rotation_event_step(value):
    # GIVEN createSecret, setSecret, testSecret or finishSecret
    # WHEN calling from_str
    # THEN match the expected enum
    assert SecretsManagerRotationEventStep.from_str(value[0]) == value[1]


def test_secret_manager_rotation_event():
    # GIVEN a valid secretsManagerRotationEvent
    event = SecretsManagerRotationEvent(load_event("secretsManagerRotationEvent.json"))
    # WHEN accessing properties
    # THEN expect the values to match
    assert event.step == SecretsManagerRotationEventStep.CREATE_SECRET
    assert event.secret_id == "arn:aws:secretsmanager:us-east-2:111122223333:secret:DatabaseSecret"
    assert event.client_request_token == "51f72378-6a5d-5dc7-8fd8-29e4319f482a"

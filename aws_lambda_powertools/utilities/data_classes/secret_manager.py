from enum import Enum

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class SecretsManagerRotationEventStep(Enum):
    CREATE_SECRET = "createSecret"  # nosec
    """The first step of rotation is to create a new version of the secret. Depending on your rotation strategy,
    the new version can contain a new password, a new username and password, or more secret information. Secrets
    Manager labels the new version with the staging label `AWSPENDING`."""
    SET_SECRET = "setSecret"  # nosec
    """Second step, rotation changes the credentials in the database or service to match the new credentials in the
    `AWSPENDING` version of the secret. """
    TEST_SECRET = "testSecret"  # nosec
    """Third step, rotation tests the `AWSPENDING` version of the secret by using it to access the database or
    service."""
    FINISH_SECRET = "finishSecret"  # nosec
    """Final step, rotation moves the label `AWSCURRENT` from the previous secret version to this version.
    Secrets Manager adds the `AWSPREVIOUS` staging label to the previous version, so that you retain the last known
    good version of the secret."""

    @staticmethod
    def from_str(value: str) -> "SecretsManagerRotationEventStep":
        for item in SecretsManagerRotationEventStep:
            if item.value == value:
                return item
        raise ValueError(f"Invalid step: {value}")


class SecretsManagerRotationEvent(DictWrapper):
    """Secrets Manager Rotation event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_how.html
    - https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_customize.html
    - https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_available-rotation-templates.html
    """

    @property
    def step(self) -> SecretsManagerRotationEventStep:
        """The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)"""
        return SecretsManagerRotationEventStep.from_str(self["Step"])

    @property
    def secret_id(self) -> str:
        """The secret ARN or other identifier"""
        return self["SecretId"]

    @property
    def client_request_token(self) -> str:
        """The ClientRequestToken of the secret version"""
        return self["ClientRequestToken"]

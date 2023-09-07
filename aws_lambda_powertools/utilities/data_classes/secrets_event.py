from typing_extensions import Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class SecretManagerEvent(DictWrapper):
    @property
    def secret_id(self) -> str:
        """SecretId: The secret ARN or identifier"""
        return self["SecretId"]

    @property
    def client_request_token(self) -> str:
        """ClientRequestToken: The ClientRequestToken of the secret version"""
        return self["ClientRequestToken"]

    @property
    def step(self) -> Literal["createSecret", "setSecret", "testSecret", "finishSecret"]:
        """Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)"""
        return self["Step"]

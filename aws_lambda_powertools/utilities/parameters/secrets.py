"""
AWS Secrets Manager parameter retrieval and caching utility
"""


from typing import Dict, Optional, Union

import boto3

from .base import DEFAULT_PROVIDERS, BaseProvider


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider
    """

    client = None

    def __init__(self, region: Optional[str] = None):
        """
        Initialize the Secrets Manager client
        """

        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region

        self.client = boto3.client("secretsmanager", **client_kwargs)

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store
        """

        return self.client.get_secret_value(SecretId=name)["SecretString"]

    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()


def get_secret(name: str, transform: Optional[str] = None, decrypt: bool = False) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager
    """

    # Only create the provider if this function is called at least once
    if "secrets" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return DEFAULT_PROVIDERS["secrets"].get(name, transform=transform, decrypt=decrypt)

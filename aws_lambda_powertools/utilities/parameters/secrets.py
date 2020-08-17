"""
AWS Secrets Manager parameter retrieval and caching utility
"""


from typing import Dict, Optional, Union

import boto3
from botocore.config import Config

from .base import DEFAULT_PROVIDERS, BaseProvider


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider

    Example
    -------
    **Retrieves a parameter value from Secrets Manager**

        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>> secrets_provider = SecretsProvider()
        >>>
        >>> secrets_provider.get("my-parameter")

    **Retrieves a parameter value from Secrets Manager in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> secrets_provider = SecretsProvider(config=config)
        >>>
        >>> secrets_provider.get("my-parameter")
    """

    client = None

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Secrets Manager client
        """

        config = config or Config()

        self.client = boto3.client("secretsmanager", config=config)

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

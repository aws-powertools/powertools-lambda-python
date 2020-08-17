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

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization

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

    **Retrieves a parameter value from Secrets Manager passing options to the SDK call**

        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>> secrets_provider = SecretsProvider()
        >>>
        >>> secrets_provider.get("my-parameter", VersionId="f658cac0-98a5-41d9-b993-8a76a7799194")
    """

    client = None

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Secrets Manager client
        """

        config = config or Config()

        self.client = boto3.client("secretsmanager", config=config)

        super().__init__()

    def _get(self, name: str, **sdk_options) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store

        Parameters
        ----------
        name: str
            Name of the parameter
        sdk_options: dict
            Dictionary of options that will be passed to the get_secret_value call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["SecretId"] = name

        return self.client.get_secret_value(**sdk_options)["SecretString"]

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()


def get_secret(name: str, transform: Optional[str] = None, **sdk_options) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager

    Parameters
    ----------
    name: str
        Name of the parameter
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    sdk_options: dict, optional
        Dictionary of options that will be passed to the get_secret_value call

    Example
    -------
    **Retrieves a secret***

        >>> from aws_lambda_powertools.utilities.parameters import get_secret
        >>>
        >>> get_secret("my-secret")

    **Retrieves a secret and transforms using a JSON deserializer***

        >>> from aws_lambda_powertools.utilities.parameters import get_secret
        >>>
        >>> get_secret("my-secret", transform="json")

    **Retrieves a secret and passes custom arguments to the SDK**

        >>> from aws_lambda_powertools.utilities.parameters import get_secret
        >>>
        >>> get_secret("my-secret", VersionId="f658cac0-98a5-41d9-b993-8a76a7799194")
    """

    # Only create the provider if this function is called at least once
    if "secrets" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return DEFAULT_PROVIDERS["secrets"].get(name, transform=transform, **sdk_options)

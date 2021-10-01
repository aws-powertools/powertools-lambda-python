"""
AWS Secrets Manager parameter retrieval and caching utility
"""


from typing import Any, Dict, Optional, Union

import boto3
from botocore.config import Config

from .base import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS, BaseProvider


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication

    Example
    -------
    **Retrieves a parameter value from Secrets Manager**

        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>> secrets_provider = SecretsProvider()
        >>>
        >>> value = secrets_provider.get("my-parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from Secrets Manager in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> secrets_provider = SecretsProvider(config=config)
        >>>
        >>> value = secrets_provider.get("my-parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from Secrets Manager passing options to the SDK call**

        >>> from aws_lambda_powertools.utilities.parameters import SecretsProvider
        >>> secrets_provider = SecretsProvider()
        >>>
        >>> value = secrets_provider.get("my-parameter", VersionId="f658cac0-98a5-41d9-b993-8a76a7799194")
        >>>
        >>> print(value)
        My parameter value
    """

    client: Any = None

    def __init__(self, config: Optional[Config] = None, boto3_session: Optional[boto3.session.Session] = None):
        """
        Initialize the Secrets Manager client
        """

        config = config or Config()
        session = boto3_session or boto3.session.Session()
        self.client = session.client("secretsmanager", config=config)

        super().__init__()

    def _get(self, name: str, **sdk_options) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store

        Parameters
        ----------
        name: str
            Name of the parameter
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Secrets Manager get_secret_value API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["SecretId"] = name

        return self.client.get_secret_value(**sdk_options)["SecretString"]

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()


def get_secret(
    name: str,
    transform: Optional[str] = None,
    force_fetch: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    **sdk_options
) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager

    Parameters
    ----------
    name: str
        Name of the parameter
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int
        Maximum age of the cached value
    sdk_options: dict, optional
        Dictionary of options that will be passed to the get_secret_value call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

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

    return DEFAULT_PROVIDERS["secrets"].get(
        name, max_age=max_age, transform=transform, force_fetch=force_fetch, **sdk_options
    )

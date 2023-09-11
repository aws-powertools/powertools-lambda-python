"""
AWS Secrets Manager parameter retrieval and caching utility
"""


import os
import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_max_age

from .base import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS, BaseProvider


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to create a boto3_client from
    boto3_client: SecretsManagerClient, optional
            Boto3 SecretsManager Client to use, boto3_session will be ignored if both are provided

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

    def __init__(
        self,
        config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
        boto3_client: Optional["SecretsManagerClient"] = None,
    ):
        """
        Initialize the Secrets Manager client
        """

        super().__init__()

        self.client: "SecretsManagerClient" = self._build_boto3_client(
            service_name="secretsmanager",
            client=boto3_client,
            session=boto3_session,
            config=config,
        )

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

        secret_value = self.client.get_secret_value(**sdk_options)

        if "SecretString" in secret_value:
            return secret_value["SecretString"]

        return secret_value["SecretBinary"]

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()

    def set_secret(
            self,
            name: str,
            secret: Optional[str],
            secret_binary: Optional[str],
            idempotency_id: Optional[str],
            version_stages: Optional[list[str]],
            **sdk_options
        ) -> str:
        """
        Modifies the details of a secret, including metadata and the secret value.

        Parameters
        ----------
        name: str
            The ARN or name of the secret to add a new version to.
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Secrets Manager update_secret API call

        URLs:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/put_secret_value.html
        """

        if isinstance(secret, dict):
            secret = json.dumps(secret)

        if not isinstance(secret_binary, bytes):
            secret_binary = secret_binary.encode("utf-8")

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["SecretId"] = name
        if secret:
            sdk_options["SecretString"] = secret
        if secret_binary:
            sdk_options["SecretBinary"] = secret_binary
        if version_stages:
            sdk_options["VersionStages"] = version_stages
        if idempotency_id:
            sdk_options["ClientRequestToken"] = idempotency_id

        put_secret = self.client.put_secret_value(**sdk_options)

        return put_secret["VersionId"]


def get_secret(
    name: str,
    transform: Optional[str] = None,
    force_fetch: bool = False,
    max_age: Optional[int] = None,
    **sdk_options,
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
    max_age: int, optional
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

    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age)

    # Only create the provider if this function is called at least once
    if "secrets" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return DEFAULT_PROVIDERS["secrets"].get(
        name,
        max_age=max_age,
        transform=transform,
        force_fetch=force_fetch,
        **sdk_options,
    )


def set_secret(
    name: str,
    secret: Optional[Union[str, dict]] = None,
    secret_binary: Optional[bytes] = None,
    idempotency_id: Optional[str] = None,
    version_stages: Optional[list[str]] = None,
    max_age: Optional[int] = None,
    transform: Optional[str] = None,
    **sdk_options
) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager

    Parameters
    ----------
    name: str
        Name of the parameter
    max_age: int, optional
        Maximum age of the cached value
    idempotency_token: str, optional
        Idempotency token to use for the request to prevent the accidental
        creation of duplicate versions if there are failures and retries
        during the Lambda rotation function processing.
    sdk_options: dict, optional
        Dictionary of options that will be passed to the get_secret_value call

    Raises
    ------
    SetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Sets a secret***

        >>> from aws_lambda_powertools.utilities.parameters import set_secret
        >>>
        >>> set_secret(name="llamas-are-awesome", secret="supers3cr3tllam@passw0rd")

    **Set a secret and transforms using a JSON deserializer***

        >>> from aws_lambda_powertools.utilities.parameters import get_secret
        >>>
        >>> get_secret("my-secret", transform="json")

    **Retrieves a secret and set an idempotency_id**

        >>> from aws_lambda_powertools.utilities.parameters import set_secret
        >>>
        >>> set_secret("my-secret", idempotency_id="f658cac0-98a5-41d9-b993-8a76a7799194")
    """

    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age)

    # Only create the provider if this function is called at least once
    if "secrets" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    if secret and secret_binary:
        raise ValueError("secret and secret_binary are mutually exclusive")
    elif secret:
        return DEFAULT_PROVIDERS["secrets"].set_secret(
            name, secret=secret, idempotency_id=idempotency_id, version_stages=version_stages, max_age=max_age, **sdk_options
        )
    elif secret_binary:
        return DEFAULT_PROVIDERS["secrets"].set_secret(
            name, secret_binary=secret_binary, idempotency_id=idempotency_id, version_stages=version_stages, max_age=max_age, **sdk_options
        )
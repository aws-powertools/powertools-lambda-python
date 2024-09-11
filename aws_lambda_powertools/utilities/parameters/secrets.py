"""
AWS Secrets Manager parameter retrieval and caching utility
"""

from __future__ import annotations

import json
import logging
import os
import warnings
from typing import TYPE_CHECKING, Literal, overload

import boto3

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_max_age
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.parameters.base import BaseProvider
from aws_lambda_powertools.utilities.parameters.constants import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS
from aws_lambda_powertools.utilities.parameters.exceptions import SetSecretError
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from botocore.config import Config
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
    from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef

    from aws_lambda_powertools.utilities.parameters.types import TransformOptions

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        config: Config | None = None,
        boto_config: Config | None = None,
        boto3_session: boto3.session.Session | None = None,
        boto3_client: SecretsManagerClient | None = None,
    ):
        """
        Initialize the Secrets Manager client
        """
        if config:
            warnings.warn(
                message="The 'config' parameter is deprecated in V3 and will be removed in V4. "
                "Please use 'boto_config' instead.",
                category=PowertoolsDeprecationWarning,
                stacklevel=2,
            )

        if boto3_client is None:
            boto3_session = boto3_session or boto3.session.Session()
            boto3_client = boto3_session.client("secretsmanager", config=boto_config or config)
        self.client = boto3_client

        super().__init__(client=self.client)

    def _get(self, name: str, **sdk_options) -> str | bytes:
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

    def _get_multiple(self, path: str, **sdk_options) -> dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()

    def _create_secret(self, name: str, **sdk_options) -> CreateSecretResponseTypeDef:
        """
        Create a secret with the given name.

        Parameters:
        ----------
        name: str
            The name of the secret.
        **sdk_options:
            Additional options to be passed to the create_secret method.

        Raises:
            SetSecretError: If there is an error setting the secret.
        """
        try:
            sdk_options["Name"] = name
            return self.client.create_secret(**sdk_options)
        except Exception as exc:
            raise SetSecretError(f"Error setting secret - {str(exc)}") from exc

    def _update_secret(self, name: str, **sdk_options):
        """
        Update a secret with the given name.

        Parameters:
        ----------
        name: str
            The name of the secret.
        **sdk_options:
            Additional options to be passed to the create_secret method.
        """
        sdk_options["SecretId"] = name
        return self.client.put_secret_value(**sdk_options)

    def set(
        self,
        name: str,
        value: str | bytes | dict,
        *,  # force keyword arguments
        client_request_token: str | None = None,
        **sdk_options,
    ) -> CreateSecretResponseTypeDef:
        """
        Modify the details of a secret or create a new secret if it doesn't already exist.

        We aim to minimize API calls by assuming that the secret already exists and needs updating.
        If it doesn't exist, we attempt to create a new one. Refer to the following workflow for a better understanding:


                          ┌────────────────────────┐      ┌─────────────────┐
                ┌───────▶│Resource NotFound error?│────▶│Create Secret API│─────┐
                │         └────────────────────────┘      └─────────────────┘     │
                │                                                                 │
                │                                                                 │
                │                                                                 ▼
        ┌─────────────────┐                                              ┌─────────────────────┐
        │Update Secret API│────────────────────────────────────────────▶│ Return or Exception │
        └─────────────────┘                                              └─────────────────────┘

        Parameters
        ----------
        name: str
            The ARN or name of the secret to add a new version to or create a new one.
        value: str, dict or bytes
            Specifies text data that you want to encrypt and store in this new version of the secret.
        client_request_token: str, optional
            This value helps ensure idempotency. It's recommended that you generate
            a UUID-type value to ensure uniqueness within the specified secret.
            This value becomes the VersionId of the new version. This field is
            auto-populated if not provided, but no idempotency will be enforced this way.
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Secrets Manager update_secret API call

        Raises
        ------
        SetSecretError
            When attempting to update or create a secret fails.

        Returns:
        -------
        SetSecretResponse:
            The dict returned by boto3.

        Example
        -------
        **Sets a secret***

            >>> from aws_lambda_powertools.utilities import parameters
            >>>
            >>> parameters.set_secret(name="llamas-are-awesome", value="supers3cr3tllam@passw0rd")

        **Sets a secret and includes an client_request_token**

            >>> from aws_lambda_powertools.utilities import parameters
            >>> import uuid
            >>>
            >>> parameters.set_secret(
                    name="my-secret",
                    value='{"password": "supers3cr3tllam@passw0rd"}',
                    client_request_token=str(uuid.uuid4())
                )

        URLs:
        -------
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/put_secret_value.html
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/create_secret.html
        """

        if isinstance(value, dict):
            value = json.dumps(value, cls=Encoder)

        if isinstance(value, bytes):
            sdk_options["SecretBinary"] = value
        else:
            sdk_options["SecretString"] = value

        if client_request_token:
            sdk_options["ClientRequestToken"] = client_request_token

        try:
            logger.debug(f"Attempting to update secret {name}")
            return self._update_secret(name=name, **sdk_options)
        except self.client.exceptions.ResourceNotFoundException:
            logger.debug(f"Secret {name} doesn't exist, creating a new one")
            return self._create_secret(name=name, **sdk_options)
        except Exception as exc:
            raise SetSecretError(f"Error setting secret - {str(exc)}") from exc


@overload
def get_secret(
    name: str,
    transform: None = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str: ...


@overload
def get_secret(
    name: str,
    transform: Literal["json"],
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> dict: ...


@overload
def get_secret(
    name: str,
    transform: Literal["binary"],
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str | bytes | dict: ...


@overload
def get_secret(
    name: str,
    transform: Literal["auto"],
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> bytes: ...


def get_secret(
    name: str,
    transform: TransformOptions = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str | bytes | dict:
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
    value: str | bytes,
    *,  # force keyword arguments
    client_request_token: str | None = None,
    **sdk_options,
) -> CreateSecretResponseTypeDef:
    """
    Modify the details of a secret or create a new secret if it doesn't already exist.

    We aim to minimize API calls by assuming that the secret already exists and needs updating.
    If it doesn't exist, we attempt to create a new one. Refer to the following workflow for a better understanding:


                      ┌────────────────────────┐      ┌─────────────────┐
            ┌───────▶│Resource NotFound error?│────▶│Create Secret API│─────┐
            │         └────────────────────────┘      └─────────────────┘     │
            │                                                                 │
            │                                                                 │
            │                                                                 ▼
    ┌─────────────────┐                                              ┌─────────────────────┐
    │Update Secret API│────────────────────────────────────────────▶│ Return or Exception │
    └─────────────────┘                                              └─────────────────────┘

    Parameters
    ----------
    name: str
        The ARN or name of the secret to add a new version to or create a new one.
    value: str, dict or bytes
        Specifies text data that you want to encrypt and store in this new version of the secret.
    client_request_token: str, optional
        This value helps ensure idempotency. It's recommended that you generate
        a UUID-type value to ensure uniqueness within the specified secret.
        This value becomes the VersionId of the new version. This field is
        auto-populated if not provided, but no idempotency will be enforced this way.
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Secrets Manager update_secret API call

    Raises
    ------
    SetSecretError
        When attempting to update or create a secret fails.

    Returns:
    -------
    SetSecretResponse:
        The dict returned by boto3.

    Example
    -------
    **Sets a secret***

        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> parameters.set_secret(name="llamas-are-awesome", value="supers3cr3tllam@passw0rd")

    **Sets a secret and includes an client_request_token**

        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> parameters.set_secret(
                name="my-secret",
                value='{"password": "supers3cr3tllam@passw0rd"}',
                client_request_token="YOUR_TOKEN_HERE"
            )

    URLs:
    -------
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/put_secret_value.html
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/create_secret.html
    """

    # Only create the provider if this function is called at least once
    if "secrets" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return DEFAULT_PROVIDERS["secrets"].set(
        name=name,
        value=value,
        client_request_token=client_request_token,
        **sdk_options,
    )

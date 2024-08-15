"""
AWS App Config configuration retrieval and caching utility
"""

from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING

import boto3

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import (
    resolve_env_var_choice,
    resolve_max_age,
)
from aws_lambda_powertools.utilities.parameters.base import BaseProvider
from aws_lambda_powertools.utilities.parameters.constants import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

if TYPE_CHECKING:
    from botocore.config import Config
    from mypy_boto3_appconfigdata.client import AppConfigDataClient

    from aws_lambda_powertools.utilities.parameters.types import TransformOptions


class AppConfigProvider(BaseProvider):
    """
    AWS App Config Provider

    Parameters
    ----------
    environment: str
        Environment of the configuration to pass during client initialization
    application: str, optional
        Application of the configuration to pass during client initialization
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to create a boto3_client from
    boto3_client: AppConfigDataClient, optional
            Boto3 AppConfigData Client to use, boto3_session will be ignored if both are provided

    Example
    -------
    **Retrieves the latest configuration value from App Config**

        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> appconf_provider = parameters.AppConfigProvider(environment="my_env", application="my_app")
        >>>
        >>> value : bytes = appconf_provider.get("my_conf")
        >>>
        >>> print(value)
        My configuration value

    **Retrieves a configuration value from App Config in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> appconf_provider = parameters.AppConfigProvider(environment="my_env", application="my_app", config=config)
        >>>
        >>> value : bytes = appconf_provider.get("my_conf")
        >>>
        >>> print(value)
        My configuration value

    """

    def __init__(
        self,
        environment: str,
        application: str | None = None,
        config: Config | None = None,
        boto_config: Config | None = None,
        boto3_session: boto3.session.Session | None = None,
        boto3_client: AppConfigDataClient | None = None,
    ):
        """
        Initialize the App Config client
        """

        super().__init__()

        if config:
            warnings.warn(
                message="The 'config' parameter is deprecated in V3 and will be removed in V4. "
                "Please use 'boto_config' instead.",
                category=PowertoolsDeprecationWarning,
                stacklevel=2,
            )

        if boto3_client is None:
            boto3_session = boto3_session or boto3.session.Session()
            boto3_client = boto3_session.client("appconfigdata", config=boto_config or config)

        self.client = boto3_client

        self.application = resolve_env_var_choice(
            choice=application,
            env=os.getenv(constants.SERVICE_NAME_ENV, "service_undefined"),
        )
        self.environment = environment
        self.current_version = ""

        self._next_token: dict[str, str] = {}  # nosec - token for get_latest_configuration executions
        # Dict to store the recently retrieved value for a specific configuration.
        self.last_returned_value: dict[str, bytes] = {}

        super().__init__(client=self.client)

    def _get(self, name: str, **sdk_options) -> bytes:
        """
        Retrieve a parameter value from AWS App config.

        Parameters
        ----------
        name: str
            Name of the configuration
        sdk_options: dict, optional
            SDK options to propagate to `start_configuration_session` API call
        """
        if name not in self._next_token:
            sdk_options["ConfigurationProfileIdentifier"] = name
            sdk_options["ApplicationIdentifier"] = self.application
            sdk_options["EnvironmentIdentifier"] = self.environment
            response_configuration = self.client.start_configuration_session(**sdk_options)
            self._next_token[name] = response_configuration["InitialConfigurationToken"]

        # The new AppConfig APIs require two API calls to return the configuration
        # First we start the session and after that we retrieve the configuration
        # We need to store the token to use in the next execution
        response = self.client.get_latest_configuration(ConfigurationToken=self._next_token[name])
        return_value = response["Configuration"].read()
        self._next_token[name] = response["NextPollConfigurationToken"]

        # The return of get_latest_configuration can be null because this value is supposed to be cached
        # on the customer side.
        # We created a dictionary that stores the most recently retrieved value for a specific configuration.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata/client/get_latest_configuration.html
        if return_value:
            self.last_returned_value[name] = return_value

        return self.last_returned_value[name]

    def _get_multiple(self, path: str, **sdk_options) -> dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS App Config Provider
        """
        raise NotImplementedError()


def get_app_config(
    name: str,
    environment: str,
    application: str | None = None,
    transform: TransformOptions = None,
    force_fetch: bool = False,
    max_age: int | None = None,
    **sdk_options,
) -> str | bytes | list | dict:
    """
    Retrieve a configuration value from AWS App Config.

    Parameters
    ----------
    name: str
        Name of the configuration
    environment: str
        Environment of the configuration
    application: str
        Application of the configuration
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int, optional
        Maximum age of the cached value
    sdk_options: dict, optional
        SDK options to propagate to `start_configuration_session` API call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Retrieves the latest version of configuration value from App Config**

        >>> from aws_lambda_powertools.utilities.parameters import get_app_config
        >>>
        >>> value = get_app_config("my_config", environment="my_env", application="my_env")
        >>>
        >>> print(value)
        My configuration value

    **Retrieves a configuration value and decodes it using a JSON decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_app_config
        >>>
        >>> value = get_app_config("my_config", environment="my_env", application="my_env", transform='json')
        >>>
        >>> print(value)
        My configuration's JSON value
    """
    # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age)

    # Only create the provider if this function is called at least once
    if "appconfig" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["appconfig"] = AppConfigProvider(environment=environment, application=application)

    return DEFAULT_PROVIDERS["appconfig"].get(
        name,
        max_age=max_age,
        transform=transform,
        force_fetch=force_fetch,
        **sdk_options,
    )

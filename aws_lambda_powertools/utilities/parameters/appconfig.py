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
    from botocore.exceptions import ClientError
    from mypy_boto3_appconfigdata.client import AppConfigDataClient

    from aws_lambda_powertools.utilities.parameters.types import TransformOptions


class AppConfigProvider(BaseProvider):
    """
    AWS App Config Provider

    An expired or corrupted poll token starts a new configuration session and retries retrieval once.
    If the replacement token is expired or corrupted, retrieval raises GetParameterError and the next
    call can start a fresh session. Other service errors, including polling too early, retain
    the token and do not trigger session recovery.
    If reading the response body fails, retrieval raises GetParameterError and discards
    that configuration's token so the next retrieval can recover. Caching and transforms
    still apply, and recovery does not reset other configuration profiles.

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
            self._start_configuration_session(name, **sdk_options)

        try:
            return self._get_configuration(name)
        except self.client.exceptions.BadRequestException as exc:
            if not self._is_token_expired_or_corrupted(exc):
                raise
            # Expired or corrupted tokens cannot be reused. Restart once, without recursively
            # retrying a rejected replacement or bypassing the configured polling interval.
            self._start_configuration_session(name, **sdk_options)
            return self._get_configuration(name)

    def _start_configuration_session(self, name: str, **sdk_options) -> None:
        sdk_options["ConfigurationProfileIdentifier"] = name
        sdk_options["ApplicationIdentifier"] = self.application
        sdk_options["EnvironmentIdentifier"] = self.environment
        response = self.client.start_configuration_session(**sdk_options)
        self._next_token[name] = response["InitialConfigurationToken"]

    def _get_configuration(self, name: str) -> bytes:
        # The new AppConfig APIs require two API calls to return the configuration
        # First we start the session and after that we retrieve the configuration
        # We need to store the token to use in the next execution
        try:
            response = self.client.get_latest_configuration(ConfigurationToken=self._next_token[name])
        except self.client.exceptions.BadRequestException as exc:
            if self._is_token_expired_or_corrupted(exc):
                self._next_token.pop(name, None)
            raise

        try:
            return_value = response["Configuration"].read()
        except Exception:
            # The request consumed the token, but we did not receive a complete value.
            # A new session on the next call retrieves the configuration again.
            self._next_token.pop(name, None)
            raise
        self._next_token[name] = response["NextPollConfigurationToken"]

        # The return of get_latest_configuration can be null because this value is supposed to be cached
        # on the customer side.
        # We created a dictionary that stores the most recently retrieved value for a specific configuration.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata/client/get_latest_configuration.html
        if return_value:
            self.last_returned_value[name] = return_value

        return self.last_returned_value[name]

    @staticmethod
    def _is_token_expired_or_corrupted(exc: ClientError) -> bool:
        problem: object = exc.response
        for key in ("Details", "InvalidParameters", "ConfigurationToken", "Problem"):
            if not isinstance(problem, dict):
                return False
            problem = problem.get(key)
        return problem in ("Expired", "Corrupted")

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
) -> str | bytes | list | dict | None:
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

    # One provider per environment/application pair, created on first use
    provider_key = f"appconfig:{environment}:{application}"
    if provider_key not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS[provider_key] = AppConfigProvider(environment=environment, application=application)

    return DEFAULT_PROVIDERS[provider_key].get(
        name,
        max_age=max_age,
        transform=transform,
        force_fetch=force_fetch,
        **sdk_options,
    )

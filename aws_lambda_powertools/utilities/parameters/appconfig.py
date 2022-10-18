"""
AWS App Config configuration retrieval and caching utility
"""


import os
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from mypy_boto3_appconfigdata import AppConfigDataClient

from ...shared import constants
from ...shared.functions import resolve_env_var_choice
from .base import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS, BaseProvider


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

    client: Any = None

    def __init__(
        self,
        environment: str,
        application: Optional[str] = None,
        config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
        boto3_client: Optional["AppConfigDataClient"] = None,
    ):
        """
        Initialize the App Config client
        """

        super().__init__()

        self.client: "AppConfigDataClient" = self._build_boto3_client(
            service_name="appconfigdata", client=boto3_client, session=boto3_session, config=config
        )

        self.application = resolve_env_var_choice(
            choice=application, env=os.getenv(constants.SERVICE_NAME_ENV, "service_undefined")
        )
        self.environment = environment
        self.current_version = ""

        self._next_token = ""  # nosec - token for get_latest_configuration executions
        self.last_returned_value = ""

    def _get(self, name: str, **sdk_options) -> str:
        """
        Retrieve a parameter value from AWS App config.

        Parameters
        ----------
        name: str
            Name of the configuration
        sdk_options: dict, optional
            SDK options to propagate to `start_configuration_session` API call
        """
        if not self._next_token:
            sdk_options["ConfigurationProfileIdentifier"] = name
            sdk_options["ApplicationIdentifier"] = self.application
            sdk_options["EnvironmentIdentifier"] = self.environment
            response_configuration = self.client.start_configuration_session(**sdk_options)
            self._next_token = response_configuration["InitialConfigurationToken"]

        # The new AppConfig APIs require two API calls to return the configuration
        # First we start the session and after that we retrieve the configuration
        # We need to store the token to use in the next execution
        response = self.client.get_latest_configuration(ConfigurationToken=self._next_token)
        return_value = response["Configuration"].read()
        self._next_token = response["NextPollConfigurationToken"]

        if return_value:
            self.last_returned_value = return_value

        return self.last_returned_value

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS App Config Provider
        """
        raise NotImplementedError()


def get_app_config(
    name: str,
    environment: str,
    application: Optional[str] = None,
    transform: Optional[str] = None,
    force_fetch: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    **sdk_options
) -> Union[str, list, dict, bytes]:
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
    max_age: int
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

    # Only create the provider if this function is called at least once
    if "appconfig" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["appconfig"] = AppConfigProvider(environment=environment, application=application)

    return DEFAULT_PROVIDERS["appconfig"].get(
        name, max_age=max_age, transform=transform, force_fetch=force_fetch, **sdk_options
    )

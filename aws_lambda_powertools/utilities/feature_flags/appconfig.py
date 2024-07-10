import logging
import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

import boto3
from botocore.config import Config

from aws_lambda_powertools.utilities import jmespath_utils
from aws_lambda_powertools.utilities.parameters import (
    AppConfigProvider,
    GetParameterError,
    TransformParameterError,
)

from ... import Logger
from .base import StoreProvider
from .exceptions import ConfigurationStoreError, StoreClientError

if TYPE_CHECKING:
    from mypy_boto3_appconfigdata import AppConfigDataClient


class AppConfigStore(StoreProvider):
    def __init__(
        self,
        environment: str,
        application: str,
        name: str,
        max_age: int = 5,
        sdk_config: Optional[Config] = None,
        envelope: Optional[str] = "",
        jmespath_options: Optional[Dict] = None,
        logger: Optional[Union[logging.Logger, Logger]] = None,
        boto_config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
        boto3_client: Optional["AppConfigDataClient"] = None,
    ):
        """This class fetches JSON schemas from AWS AppConfig

        Parameters
        ----------
        environment: str
            Appconfig environment, e.g. 'dev/test' etc.
        application: str
            AppConfig application name, e.g. 'powertools'
        name: str
            AppConfig configuration name e.g. `my_conf`
        max_age: int
            cache expiration time in seconds, or how often to call AppConfig to fetch latest configuration
        sdk_config: Optional[Config]
            Botocore Config object to pass during client initialization
        envelope : Optional[str]
            JMESPath expression to pluck feature flags data from config
        jmespath_options : Optional[Dict]
            Alternative JMESPath options to be included when filtering expr
        logger: A logging object
            Used to log messages. If None is supplied, one will be created.
        boto_config: botocore.config.Config, optional
            Botocore configuration to pass during client initialization
        boto3_session : boto3.Session, optional
            Boto3 session to use for AWS API communication
        boto3_client : AppConfigDataClient, optional
            Boto3 AppConfigDataClient Client to use, boto3_session and boto_config will be ignored if both are provided
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.environment = environment
        self.application = application
        self.name = name
        self.cache_seconds = max_age
        self.config = sdk_config or boto_config
        self.envelope = envelope
        self.jmespath_options = jmespath_options
        self._conf_store = AppConfigProvider(
            environment=environment,
            application=application,
            config=sdk_config or boto_config,
            boto3_client=boto3_client,
            boto3_session=boto3_session,
        )

    @property
    def get_raw_configuration(self) -> Dict[str, Any]:
        """Fetch feature schema configuration from AWS AppConfig"""
        try:
            # parse result conf as JSON, keep in cache for self.max_age seconds
            self.logger.debug(
                "Fetching configuration from the store",
                extra={"param_name": self.name, "max_age": self.cache_seconds},
            )
            return cast(
                dict,
                self._conf_store.get(
                    name=self.name,
                    transform="json",
                    max_age=self.cache_seconds,
                ),
            )
        except (GetParameterError, TransformParameterError) as exc:
            err_msg = traceback.format_exc()
            if "AccessDenied" in err_msg:
                raise StoreClientError(err_msg) from exc
            raise ConfigurationStoreError("Unable to get AWS AppConfig configuration file") from exc

    def get_configuration(self) -> Dict[str, Any]:
        """Fetch feature schema configuration from AWS AppConfig

        If envelope is set, it'll extract and return feature flags from configuration,
        otherwise it'll return the entire configuration fetched from AWS AppConfig.

        Raises
        ------
        ConfigurationStoreError
            Any validation error or AppConfig error that can occur

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary
        """
        config = self.get_raw_configuration

        if self.envelope:
            self.logger.debug("Envelope enabled; extracting data from config", extra={"envelope": self.envelope})
            config = jmespath_utils.extract_data_from_envelope(
                data=config,
                envelope=self.envelope,
                jmespath_options=self.jmespath_options,
            )

        return config

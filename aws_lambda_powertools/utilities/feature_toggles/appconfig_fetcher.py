import logging
from typing import Any, Dict, Optional

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from .exceptions import ConfigurationError
from .schema_fetcher import SchemaFetcher

logger = logging.getLogger(__name__)


TRANSFORM_TYPE = "json"


class AppConfigFetcher(SchemaFetcher):
    def __init__(
        self,
        environment: str,
        service: str,
        configuration_name: str,
        cache_seconds: int,
        config: Optional[Config] = None,
    ):
        """This class fetches JSON schemas from AWS AppConfig

        Parameters
        ----------
        environment: str
            what appconfig environment to use 'dev/test' etc.
        service: str
            what service name to use from the supplied environment
        configuration_name: str
            what configuration to take from the environment & service combination
        cache_seconds: int
            cache expiration time, how often to call AppConfig to fetch latest configuration
        config: Optional[Config]
            boto3 client configuration
        """
        super().__init__(configuration_name, cache_seconds)
        self._logger = logger
        self._conf_store = AppConfigProvider(environment=environment, application=service, config=config)

    def get_json_configuration(self) -> Dict[str, Any]:
        """Get configuration string from AWs AppConfig and return the parsed JSON dictionary

        Raises
        ------
        ConfigurationError
            Any validation error or appconfig error that can occur

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary
        """
        try:
            return self._conf_store.get(
                name=self.configuration_name,
                transform=TRANSFORM_TYPE,
                max_age=self._cache_seconds,
            )  # parse result conf as JSON, keep in cache for self.max_age seconds
        except (GetParameterError, TransformParameterError) as exc:
            error_str = f"unable to get AWS AppConfig configuration file, exception={str(exc)}"
            self._logger.error(error_str)
            raise ConfigurationError(error_str)

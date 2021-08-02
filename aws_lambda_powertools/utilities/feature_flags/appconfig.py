import logging
from typing import Any, Dict, Optional, cast

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from .base import StoreProvider
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

TRANSFORM_TYPE = "json"


class AppConfigStore(StoreProvider):
    def __init__(
        self,
        environment: str,
        application: str,
        name: str,
        cache_seconds: int,
        config: Optional[Config] = None,
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
        cache_seconds: int
            cache expiration time, how often to call AppConfig to fetch latest configuration
        config: Optional[Config]
            boto3 client configuration
        """
        super().__init__(name, cache_seconds)
        self._logger = logger
        self._conf_store = AppConfigProvider(environment=environment, application=application, config=config)

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
            # parse result conf as JSON, keep in cache for self.max_age seconds
            return cast(
                dict,
                self._conf_store.get(
                    name=self.name,
                    transform=TRANSFORM_TYPE,
                    max_age=self._cache_seconds,
                ),
            )
        except (GetParameterError, TransformParameterError) as exc:
            raise ConfigurationError("Unable to get AWS AppConfig configuration file") from exc

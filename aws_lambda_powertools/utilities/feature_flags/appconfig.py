import logging
from typing import Any, Dict, Optional, cast

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from ...shared import jmespath_utils
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
        envelope: str = "",
        jmespath_options: Optional[Dict] = None,
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
        envelope : str
            JMESPath expression to pluck feature flags data from config
        jmespath_options : Dict
            Alternative JMESPath options to be included when filtering expr
        """
        super().__init__()
        self.environment = environment
        self.application = application
        self.name = name
        self.cache_seconds = cache_seconds
        self.config = config
        self.envelope = envelope
        self.jmespath_options = jmespath_options
        self._conf_store = AppConfigProvider(environment=environment, application=application, config=config)

    def get_json_configuration(self) -> Dict[str, Any]:
        """Get configuration string from AWS AppConfig and return the parsed JSON dictionary

        Raises
        ------
        ConfigurationError
            Any validation error or AppConfig error that can occur

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary
        """
        try:
            # parse result conf as JSON, keep in cache for self.max_age seconds
            config = self._conf_store.get(
                name=self.name,
                transform=TRANSFORM_TYPE,
                max_age=self.cache_seconds,
            )

            if self.envelope:
                config = jmespath_utils.unwrap_event_from_envelope(
                    data=config, envelope=self.envelope, jmespath_options=self.jmespath_options
                )

            return cast(dict, config)
        except (GetParameterError, TransformParameterError) as exc:
            raise ConfigurationError("Unable to get AWS AppConfig configuration file") from exc

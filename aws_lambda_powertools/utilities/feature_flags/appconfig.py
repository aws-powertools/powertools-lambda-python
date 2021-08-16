import logging
import traceback
from typing import Any, Dict, Optional, cast

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from ...shared import jmespath_utils
from .base import StoreProvider
from .exceptions import ConfigurationStoreError, StoreClientError

logger = logging.getLogger(__name__)

TRANSFORM_TYPE = "json"


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
        """
        super().__init__()
        self.environment = environment
        self.application = application
        self.name = name
        self.cache_seconds = max_age
        self.config = sdk_config
        self.envelope = envelope
        self.jmespath_options = jmespath_options
        self._conf_store = AppConfigProvider(environment=environment, application=application, config=sdk_config)

    def get_configuration(self) -> Dict[str, Any]:
        """Fetch feature schema configuration from AWS AppConfig

        Raises
        ------
        ConfigurationStoreError
            Any validation error or AppConfig error that can occur

        Returns
        -------
        Dict[str, Any]
            parsed JSON dictionary
        """
        try:
            # parse result conf as JSON, keep in cache for self.max_age seconds
            config = cast(
                dict,
                self._conf_store.get(
                    name=self.name,
                    transform=TRANSFORM_TYPE,
                    max_age=self.cache_seconds,
                ),
            )

            if self.envelope:
                config = jmespath_utils.extract_data_from_envelope(
                    data=config, envelope=self.envelope, jmespath_options=self.jmespath_options
                )

            return config
        except (GetParameterError, TransformParameterError) as exc:
            err_msg = traceback.format_exc()
            if "AccessDenied" in err_msg:
                raise StoreClientError(err_msg) from exc
            raise ConfigurationStoreError("Unable to get AWS AppConfig configuration file") from exc

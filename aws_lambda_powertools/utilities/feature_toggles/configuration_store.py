# pylint: disable=no-name-in-module,line-too-long
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from .exceptions import ConfigurationException

TRANSFORM_TYPE = "json"
FEATURES_KEY = "features"
RULES_KEY = "rules"
DEFAULT_VAL_KEY = "feature_default_value"
RESTRICTIONS_KEY = "restrictions"
RULE_NAME_KEY = "name"
RULE_DEFAULT_VALUE = "rule_default_value"
RESTRICTION_KEY = "key"
RESTRICTION_VALUE = "value"
RESTRICTION_ACTION = "action"


class ACTION(str, Enum):
    EQUALS = "EQUALS"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    CONTAINS = "CONTAINS"


logger = logging.getLogger(__name__)


class ConfigurationStore:
    def __init__(
        self, environment: str, service: str, conf_name: str, cache_seconds: int, config: Optional[Config] = None
    ):
        """constructor

        Args:
            environment (str): what appconfig environment to use 'dev/test' etc.
            service (str): what service name to use from the supplied environment
            conf_name (str): what configuration to take from the environment & service combination
            cache_seconds (int): cache expiration time, how often to call AppConfig to fetch latest configuration
        """
        self._cache_seconds = cache_seconds
        self.logger = logger
        self._conf_name = conf_name
        self._conf_store = AppConfigProvider(environment=environment, application=service, config=config)

    def _validate_json_schema(self, schema: str) -> bool:
        ## todo
        return True

    def _match_by_action(self, action: str, restriction_value: Any, context_value: Any) -> bool:
        if not context_value:
            return False
        mapping_by_action = {
            ACTION.EQUALS.value: lambda a, b: a == b,
            ACTION.STARTSWITH.value: lambda a, b: a.startswith(b),
            ACTION.ENDSWITH.value: lambda a, b: a.endswith(b),
            ACTION.CONTAINS.value: lambda a, b: a in b,
        }

        try:
            func = mapping_by_action.get(action, lambda a, b: False)
            return func(context_value, restriction_value)
        except Exception:
            return False

    def _handle_rules(
        self,
        *,
        feature_name: str,
        rules_context: Dict[str, Any],
        feature_default_value: bool,
        rules: List[Dict[str, Any]],
    ) -> bool:
        for rule in rules:
            rule_name = rule.get(RULE_NAME_KEY, "")
            rule_default_value = rule.get(RULE_DEFAULT_VALUE)
            is_match = True
            restrictions: Dict[str, str] = rule.get(RESTRICTIONS_KEY)

            for restriction in restrictions:
                context_value = rules_context.get(restriction.get(RESTRICTION_KEY, ""), "")
                if not self._match_by_action(
                    restriction.get(RESTRICTION_ACTION), restriction.get(RESTRICTION_VALUE), context_value
                ):
                    logger.debug(
                        f"rule did not match action, rule_name={rule_name}, rule_default_value={rule_default_value}, feature_name={feature_name}, context_value={str(context_value)}"  # noqa: E501
                    )
                    is_match = False  # rules doesn't match restriction
                    break
            # if we got here, all restrictions match
            if is_match:
                logger.debug(
                    f"rule matched, rule_name={rule_name}, rule_default_value={rule_default_value}, feature_name={feature_name}"  # noqa: E501
                )
                return rule_default_value
        # no rule matched, return default value of feature
        logger.debug(
            f"no rule matched, returning default value of feature, feature_default_value={feature_default_value}, feature_name={feature_name}"  # noqa: E501
        )
        return feature_default_value

    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration string from AWs AppConfig and returned the parsed JSON dictionary

        Raises:
            ConfigurationException: Any validation error or appconfig error that can occur

        Returns:
            Dict[str, Any]: parsed JSON dictionary
        """
        try:
            schema = self._conf_store.get(
                name=self._conf_name,
                transform=TRANSFORM_TYPE,
                max_age=self._cache_seconds,
            )  # parse result conf as JSON, keep in cache for self.max_age seconds
        except (GetParameterError, TransformParameterError) as exc:
            error_str = f"unable to get AWS AppConfig configuration file, exception={str(exc)}"
            logger.error(error_str)
            raise ConfigurationException(error_str)
        # validate schema
        if not self._validate_json_schema(schema):
            error_str = "AWS AppConfig schema failed validation"
            logger.error(error_str)
            raise ConfigurationException(error_str)
        return schema

    def get_feature_toggle(self, *, feature_name: str, rules_context: Dict[str, Any], value_if_missing: bool) -> bool:
        """get a feature toggle boolean value. Value is calculated according to a set of rules and conditions.
           see below for explanation.

        Args:
            feature_name (str): feature name that you wish to fetch
            rules_context (Dict[str, Any]): dict of attributes that you would like to match the rules
                                            against, can be {'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'} etc.
            value_if_missing (bool): this will be the returned value in case the feature toggle doesn't exist in the schema
                                  or there has been an error while fetching the configuration from appconfig

        Returns:
            bool: calculated feature toggle value. several possibilities:
                1. if the feature doesn't appear in the schema or there has been an error fetching the
                   configuration -> warning log would appear and value_if_missing is returned
                2. feature exists and has no rules or no rules have matched -> return feature_default_value of
                   the defined feature
                3. feature exists and a rule matches -> rule_default_value of rule is returned
        """
        try:
            toggles_dict: Dict[str, Any] = self.get_configuration()
        except ConfigurationException:
            logger.warning("unable to get feature toggles JSON, returning provided default value")
            return default_value

        feature: Dict[str, Dict] = toggles_dict.get(FEATURES_KEY, {}).get(feature_name, None)
        if feature is None:
            logger.warning(
                f"feature does not appear in configuration, using provided default value, feature_name={feature_name}, value_if_missing={value_if_missing}"  # noqa: E501
            )
            return value_if_missing

        rules_list = feature.get(RULES_KEY, [])
        feature_default_value = feature.get(DEFAULT_VAL_KEY)
        if not rules_list:
            # not rules but has a value
            logger.debug(
                f"no rules found, returning feature default value, feature_name={feature_name}, default_value={feature_default_value}"  # noqa: E501
            )
            return feature_default_value
        # look for first rule match
        logger.debug(
            f"looking for rule match,  feature_name={feature_name}, feature_default_value={feature_default_value}"
        )  # noqa: E501
        return self._handle_rules(
            feature_name=feature_name, rules_context=rules_context, feature_default_value=feature_default_value, rules=rules_list
        )

# pylint: disable=no-name-in-module,line-too-long
import logging
from typing import Any, Dict, List, Optional

from botocore.config import Config

from aws_lambda_powertools.utilities.parameters import AppConfigProvider, GetParameterError, TransformParameterError

from . import schema
from .exceptions import ConfigurationException

TRANSFORM_TYPE = "json"

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
        self._logger = logger
        self._conf_name = conf_name
        self._schema_validator = schema.SchemaValidator(self._logger)
        self._conf_store = AppConfigProvider(environment=environment, application=service, config=config)

    def _match_by_action(self, action: str, CONDITION_VALUE: Any, context_value: Any) -> bool:
        if not context_value:
            return False
        mapping_by_action = {
            schema.ACTION.EQUALS.value: lambda a, b: a == b,
            schema.ACTION.STARTSWITH.value: lambda a, b: a.startswith(b),
            schema.ACTION.ENDSWITH.value: lambda a, b: a.endswith(b),
            schema.ACTION.CONTAINS.value: lambda a, b: a in b,
        }

        try:
            func = mapping_by_action.get(action, lambda a, b: False)
            return func(context_value, CONDITION_VALUE)
        except Exception as exc:
            self._logger.error(f"caught exception while matching action, action={action}, exception={str(exc)}")
            return False

    def _is_rule_matched(self, feature_name: str, rule: Dict[str, Any], rules_context: Dict[str, Any]) -> bool:
        rule_name = rule.get(schema.RULE_NAME_KEY, "")
        rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
        conditions: Dict[str, str] = rule.get(schema.CONDITIONS_KEY)

        for condition in conditions:
            context_value = rules_context.get(condition.get(schema.CONDITION_KEY))
            if not self._match_by_action(
                condition.get(schema.CONDITION_ACTION),
                condition.get(schema.CONDITION_VALUE),
                context_value,
            ):
                logger.debug(
                    f"rule did not match action, rule_name={rule_name}, rule_default_value={rule_default_value}, feature_name={feature_name}, context_value={str(context_value)}"  # noqa: E501
                )
                # context doesn't match condition
                return False
            # if we got here, all conditions match
            logger.debug(
                f"rule matched, rule_name={rule_name}, rule_default_value={rule_default_value}, feature_name={feature_name}"  # noqa: E501
            )
            return True

    def _handle_rules(
        self,
        *,
        feature_name: str,
        rules_context: Dict[str, Any],
        feature_default_value: bool,
        rules: List[Dict[str, Any]],
    ) -> bool:
        for rule in rules:
            rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
            if self._is_rule_matched(feature_name, rule, rules_context):
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
            self._logger.error(error_str)
            raise ConfigurationException(error_str)

        # validate schema
        self._schema_validator.validate_json_schema(schema)
        return schema

    def get_feature_toggle(
        self, *, feature_name: str, rules_context: Optional[Dict[str, Any]] = None, value_if_missing: bool
    ) -> bool:
        """get a feature toggle boolean value. Value is calculated according to a set of rules and conditions.
           see below for explanation.

        Args:
            feature_name (str): feature name that you wish to fetch
            rules_context (Optional[Dict[str, Any]]): dict of attributes that you would like to match the rules
                                            against, can be {'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'} etc.
            value_if_missing (bool): this will be the returned value in case the feature toggle doesn't exist in
                                     the schema or there has been an error while fetching the
                                    configuration from appconfig

        Returns:
            bool: calculated feature toggle value. several possibilities:
                1. if the feature doesn't appear in the schema or there has been an error fetching the
                   configuration -> error/warning log would appear and value_if_missing is returned
                2. feature exists and has no rules or no rules have matched -> return feature_default_value of
                   the defined feature
                3. feature exists and a rule matches -> rule_default_value of rule is returned
        """
        if rules_context is None:
            rules_context = {}

        try:
            toggles_dict: Dict[str, Any] = self.get_configuration()
        except ConfigurationException:
            logger.error("unable to get feature toggles JSON, returning provided value_if_missing value")  # noqa: E501
            return value_if_missing

        feature: Dict[str, Dict] = toggles_dict.get(schema.FEATURES_KEY, {}).get(feature_name, None)
        if feature is None:
            logger.warning(
                f"feature does not appear in configuration, using provided value_if_missing, feature_name={feature_name}, value_if_missing={value_if_missing}"  # noqa: E501
            )
            return value_if_missing

        rules_list = feature.get(schema.RULES_KEY)
        feature_default_value = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
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
            feature_name=feature_name,
            rules_context=rules_context,
            feature_default_value=feature_default_value,
            rules=rules_list,
        )

    def get_all_enabled_feature_toggles(self, *, rules_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get all enabled feature toggles while also taking into account rule_context (when a feature has defined rules)

        Args:
            rules_context (Optional[Dict[str, Any]]): dict of attributes that you would like to match the rules
                                            against, can be {'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'} etc.

        Returns:
            List[str]: a list of all features name that are enabled by also taking into account
                       rule_context (when a feature has defined rules)
        """
        if rules_context is None:
            rules_context = {}
        try:
            toggles_dict: Dict[str, Any] = self.get_configuration()
        except ConfigurationException:
            logger.error("unable to get feature toggles JSON")  # noqa: E501
            return []
        ret_list = []
        features: Dict[str, Any] = toggles_dict.get(schema.FEATURES_KEY, {})
        for feature_name, feature_dict_def in features.items():
            rules_list = feature_dict_def.get(schema.RULES_KEY, [])
            feature_default_value = feature_dict_def.get(schema.FEATURE_DEFAULT_VAL_KEY)
            if feature_default_value and not rules_list:
                self._logger.debug(
                    f"feature is enabled by default and has no defined rules, feature_name={feature_name}"
                )
                ret_list.append(feature_name)
            elif self._handle_rules(
                feature_name=feature_name,
                rules_context=rules_context,
                feature_default_value=feature_default_value,
                rules=rules_list,
            ):
                self._logger.debug(f"feature's calculated value is True, feature_name={feature_name}")
                ret_list.append(feature_name)
        return ret_list

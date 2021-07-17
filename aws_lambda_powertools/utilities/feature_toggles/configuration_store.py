import logging
from typing import Any, Dict, List, Optional, cast

from . import schema
from .exceptions import ConfigurationError
from .schema_fetcher import SchemaFetcher

logger = logging.getLogger(__name__)


class ConfigurationStore:
    def __init__(self, schema_fetcher: SchemaFetcher):
        """constructor

        Parameters
        ----------
        schema_fetcher: SchemaFetcher
            A schema JSON fetcher, can be AWS AppConfig, Hashicorp Consul etc.
        """
        self._logger = logger
        self._schema_fetcher = schema_fetcher
        self._schema_validator = schema.SchemaValidator(self._logger)

    def _match_by_action(self, action: str, condition_value: Any, context_value: Any) -> bool:
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
            return func(context_value, condition_value)
        except Exception as exc:
            self._logger.error(f"caught exception while matching action, action={action}, exception={str(exc)}")
            return False

    def _is_rule_matched(self, feature_name: str, rule: Dict[str, Any], rules_context: Dict[str, Any]) -> bool:
        rule_name = rule.get(schema.RULE_NAME_KEY, "")
        rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
        conditions = cast(List[Dict], rule.get(schema.CONDITIONS_KEY))

        for condition in conditions:
            context_value = rules_context.get(str(condition.get(schema.CONDITION_KEY)))
            if not self._match_by_action(
                condition.get(schema.CONDITION_ACTION, ""),
                condition.get(schema.CONDITION_VALUE),
                context_value,
            ):
                logger.debug(
                    f"rule did not match action, rule_name={rule_name}, rule_default_value={rule_default_value}, "
                    f"feature_name={feature_name}, context_value={str(context_value)} "
                )
                # context doesn't match condition
                return False
            # if we got here, all conditions match
            logger.debug(
                f"rule matched, rule_name={rule_name}, rule_default_value={rule_default_value}, "
                f"feature_name={feature_name}"
            )
            return True
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
            rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
            if self._is_rule_matched(feature_name, rule, rules_context):
                return bool(rule_default_value)
            # no rule matched, return default value of feature
            logger.debug(
                f"no rule matched, returning default value of feature, feature_default_value={feature_default_value}, "
                f"feature_name={feature_name}"
            )
            return feature_default_value
        return False

    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration string from AWs AppConfig and returned the parsed JSON dictionary

        Raises
        ------
        ConfigurationError
            Any validation error or appconfig error that can occur

        Returns
        ------
        Dict[str, Any]
            parsed JSON dictionary
        """
        # parse result conf as JSON, keep in cache for self.max_age seconds
        config = self._schema_fetcher.get_json_configuration()
        # validate schema
        self._schema_validator.validate_json_schema(config)
        return config

    def get_feature_toggle(
        self, *, feature_name: str, rules_context: Optional[Dict[str, Any]] = None, value_if_missing: bool
    ) -> bool:
        """Get a feature toggle boolean value. Value is calculated according to a set of rules and conditions.

        See below for explanation.

        Parameters
        ----------
        feature_name: str
            feature name that you wish to fetch
        rules_context: Optional[Dict[str, Any]]
            dict of attributes that you would like to match the rules
            against, can be {'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'} etc.
        value_if_missing: bool
            this will be the returned value in case the feature toggle doesn't exist in
            the schema or there has been an error while fetching the
            configuration from appconfig

        Returns
        ------
        bool
            calculated feature toggle value. several possibilities:
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
        except ConfigurationError:
            logger.error("unable to get feature toggles JSON, returning provided value_if_missing value")
            return value_if_missing

        feature: Dict[str, Dict] = toggles_dict.get(schema.FEATURES_KEY, {}).get(feature_name, None)
        if feature is None:
            logger.warning(
                f"feature does not appear in configuration, using provided value_if_missing, "
                f"feature_name={feature_name}, value_if_missing={value_if_missing}"
            )
            return value_if_missing

        rules_list = feature.get(schema.RULES_KEY)
        feature_default_value = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
        if not rules_list:
            # not rules but has a value
            logger.debug(
                f"no rules found, returning feature default value, feature_name={feature_name}, "
                f"default_value={feature_default_value}"
            )
            return bool(feature_default_value)
        # look for first rule match
        logger.debug(
            f"looking for rule match,  feature_name={feature_name}, feature_default_value={feature_default_value}"
        )
        return self._handle_rules(
            feature_name=feature_name,
            rules_context=rules_context,
            feature_default_value=bool(feature_default_value),
            rules=cast(List, rules_list),
        )

    def get_all_enabled_feature_toggles(self, *, rules_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get all enabled feature toggles while also taking into account rule_context
        (when a feature has defined rules)

        Parameters
        ----------
        rules_context: Optional[Dict[str, Any]]
            dict of attributes that you would like to match the rules
            against, can be `{'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'}` etc.

        Returns
        ----------
        List[str]
            a list of all features name that are enabled by also taking into account
            rule_context (when a feature has defined rules)
        """
        if rules_context is None:
            rules_context = {}

        try:
            toggles_dict: Dict[str, Any] = self.get_configuration()
        except ConfigurationError:
            logger.error("unable to get feature toggles JSON")
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

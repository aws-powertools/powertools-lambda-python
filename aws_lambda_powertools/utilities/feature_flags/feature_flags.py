import logging
from typing import Any, Dict, List, Optional, Union, cast

from . import schema
from .base import StoreProvider
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class FeatureFlags:
    def __init__(self, store: StoreProvider):
        """constructor

        Parameters
        ----------
        store: StoreProvider
            A schema JSON fetcher, can be AWS AppConfig, Hashicorp Consul etc.
        """
        self._logger = logger
        self._store = store

    def _match_by_action(self, action: str, condition_value: Any, context_value: Any) -> bool:
        if not context_value:
            return False
        mapping_by_action = {
            schema.RuleAction.EQUALS.value: lambda a, b: a == b,
            schema.RuleAction.STARTSWITH.value: lambda a, b: a.startswith(b),
            schema.RuleAction.ENDSWITH.value: lambda a, b: a.endswith(b),
            schema.RuleAction.CONTAINS.value: lambda a, b: a in b,
        }

        try:
            func = mapping_by_action.get(action, lambda a, b: False)
            return func(context_value, condition_value)
        except Exception as exc:
            self._logger.debug(f"caught exception while matching action: action={action}, exception={str(exc)}")
            return False

    def _is_rule_matched(
        self, rule_name: str, feature_name: str, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
        conditions = cast(List[Dict], rule.get(schema.CONDITIONS_KEY))

        for condition in conditions:
            context_value = context.get(str(condition.get(schema.CONDITION_KEY)))
            if not self._match_by_action(
                condition.get(schema.CONDITION_ACTION, ""),
                condition.get(schema.CONDITION_VALUE),
                context_value,
            ):
                logger.debug(
                    f"rule did not match action, rule_name={rule_name}, rule_default_value={rule_default_value}, "
                    f"name={feature_name}, context_value={str(context_value)} "
                )
                # context doesn't match condition
                return False
            # if we got here, all conditions match
            logger.debug(
                f"rule matched, rule_name={rule_name}, rule_default_value={rule_default_value}, name={feature_name}"
            )
            return True
        return False

    def _handle_rules(
        self,
        *,
        feature_name: str,
        context: Dict[str, Any],
        feature_default_value: bool,
        rules: Dict[str, Any],
    ) -> bool:
        for rule_name, rule in rules.items():
            rule_default_value = rule.get(schema.RULE_DEFAULT_VALUE)
            if self._is_rule_matched(rule_name=rule_name, feature_name=feature_name, rule=rule, context=context):
                return bool(rule_default_value)
            # no rule matched, return default value of feature
            logger.debug(
                f"no rule matched, returning default value of feature, feature_default_value={feature_default_value}, "
                f"name={feature_name}"
            )
            return feature_default_value
        return False

    def get_configuration(self) -> Union[Dict[str, Dict], Dict]:
        """Get configuration string from AWs AppConfig and returned the parsed JSON dictionary

        Raises
        ------
        ConfigurationError
            Any validation error or appconfig error that can occur

        Returns
        ------
        Dict[str, Dict]
            parsed JSON dictionary

            {
                "my_feature": {
                    "feature_default_value": True,
                    "rules": [
                        {
                            "rule_name": "tenant id equals 345345435",
                            "value_when_applies": False,
                            "conditions": [
                                {
                                    "action": "EQUALS",
                                    "key": "tenant_id",
                                    "value": "345345435",
                                }
                            ],
                        },
                    ],
                }
            }
        """
        # parse result conf as JSON, keep in cache for self.max_age seconds
        config = self._store.get_json_configuration()

        validator = schema.SchemaValidator(schema=config)
        validator.validate()

        return config.get(schema.FEATURES_KEY, {})

    def evaluate(self, *, name: str, context: Optional[Dict[str, Any]] = None, default: bool) -> bool:
        """Get a feature toggle boolean value. Value is calculated according to a set of rules and conditions.

        See below for explanation.

        Parameters
        ----------
        name: str
            feature name that you wish to fetch
        context: Optional[Dict[str, Any]]
            dict of attributes that you would like to match the rules
            against, can be {'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'} etc.
        default: bool
            default value if feature flag doesn't exist in the schema,
            or there has been an error while fetching the configuration from appconfig

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
        if context is None:
            context = {}

        try:
            features = self.get_configuration()
        except ConfigurationError:
            logger.debug("Unable to get feature toggles JSON, returning provided default value")
            return default

        feature = features.get(name)
        if feature is None:
            logger.debug(
                f"feature does not appear in configuration, using provided default, name={name}, default={default}"
            )
            return default

        rules_list = feature.get(schema.RULES_KEY)
        feature_default_value = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
        if not rules_list:
            # no rules but value
            logger.debug(
                f"no rules found, returning feature default value, name={name}, "
                f"default_value={feature_default_value}"
            )
            return bool(feature_default_value)

        # look for first rule match
        logger.debug(f"looking for rule match,  name={name}, feature_default_value={feature_default_value}")
        return self._handle_rules(
            feature_name=name,
            context=context,
            feature_default_value=bool(feature_default_value),
            rules=cast(List, rules_list),
        )

    def get_enabled_features(self, *, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get all enabled feature toggles while also taking into account rule_context
        (when a feature has defined rules)

        Parameters
        ----------
        context: Optional[Dict[str, Any]]
            dict of attributes that you would like to match the rules
            against, can be `{'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'}` etc.

        Returns
        ----------
        List[str]
            a list of all features name that are enabled by also taking into account
            rule_context (when a feature has defined rules)
        """
        if context is None:
            context = {}

        features_enabled: List[str] = []

        try:
            features: Dict[str, Any] = self.get_configuration()
        except ConfigurationError:
            logger.debug("unable to get feature toggles JSON")
            return features_enabled

        for feature_name, feature_dict_def in features.items():
            rules = feature_dict_def.get(schema.RULES_KEY, {})
            feature_default_value = feature_dict_def.get(schema.FEATURE_DEFAULT_VAL_KEY)
            if feature_default_value and not rules:
                self._logger.debug(f"feature is enabled by default and has no defined rules, name={feature_name}")
                features_enabled.append(feature_name)
            elif self._handle_rules(
                feature_name=feature_name,
                context=context,
                feature_default_value=feature_default_value,
                rules=rules,
            ):
                self._logger.debug(f"feature's calculated value is True, name={feature_name}")
                features_enabled.append(feature_name)

        return features_enabled

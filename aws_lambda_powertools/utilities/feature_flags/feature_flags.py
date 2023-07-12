import logging
from typing import Any, Dict, List, Optional, Union, cast

from ... import Logger
from ...shared.types import JSONType
from . import schema
from .base import StoreProvider
from .comparators import (
    compare_datetime_range,
    compare_days_of_week,
    compare_modulo_range,
    compare_time_range,
)
from .exceptions import ConfigurationStoreError


class FeatureFlags:
    def __init__(self, store: StoreProvider, logger: Optional[Union[logging.Logger, Logger]] = None):
        """Evaluates whether feature flags should be enabled based on a given context.

        It uses the provided store to fetch feature flag rules before evaluating them.

        Examples
        --------

        ```python
        from aws_lambda_powertools.utilities.feature_flags import FeatureFlags, AppConfigStore

        app_config = AppConfigStore(
            environment="test",
            application="powertools",
            name="test_conf_name",
            max_age=300,
            envelope="features"
        )

        feature_flags: FeatureFlags = FeatureFlags(store=app_config)
        ```

        Parameters
        ----------
        store: StoreProvider
            Store to use to fetch feature flag schema configuration.
        logger: A logging object
            Used to log messages. If None is supplied, one will be created.
        """
        self.store = store
        self.logger = logger or logging.getLogger(__name__)

    def _match_by_action(self, action: str, condition_value: Any, context_value: Any) -> bool:
        mapping_by_action = {
            schema.RuleAction.EQUALS.value: lambda a, b: a == b,
            schema.RuleAction.NOT_EQUALS.value: lambda a, b: a != b,
            schema.RuleAction.KEY_GREATER_THAN_VALUE.value: lambda a, b: a > b,
            schema.RuleAction.KEY_GREATER_THAN_OR_EQUAL_VALUE.value: lambda a, b: a >= b,
            schema.RuleAction.KEY_LESS_THAN_VALUE.value: lambda a, b: a < b,
            schema.RuleAction.KEY_LESS_THAN_OR_EQUAL_VALUE.value: lambda a, b: a <= b,
            schema.RuleAction.STARTSWITH.value: lambda a, b: a.startswith(b),
            schema.RuleAction.ENDSWITH.value: lambda a, b: a.endswith(b),
            schema.RuleAction.IN.value: lambda a, b: a in b,
            schema.RuleAction.NOT_IN.value: lambda a, b: a not in b,
            schema.RuleAction.KEY_IN_VALUE.value: lambda a, b: a in b,
            schema.RuleAction.KEY_NOT_IN_VALUE.value: lambda a, b: a not in b,
            schema.RuleAction.VALUE_IN_KEY.value: lambda a, b: b in a,
            schema.RuleAction.VALUE_NOT_IN_KEY.value: lambda a, b: b not in a,
            schema.RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value: lambda a, b: compare_time_range(a, b),
            schema.RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value: lambda a, b: compare_datetime_range(a, b),
            schema.RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value: lambda a, b: compare_days_of_week(a, b),
            schema.RuleAction.MODULO_RANGE.value: lambda a, b: compare_modulo_range(a, b),
        }

        try:
            func = mapping_by_action.get(action, lambda a, b: False)
            return func(context_value, condition_value)
        except Exception as exc:
            self.logger.debug(f"caught exception while matching action: action={action}, exception={str(exc)}")
            return False

    def _evaluate_conditions(
        self,
        rule_name: str,
        feature_name: str,
        rule: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """Evaluates whether context matches conditions, return False otherwise"""
        rule_match_value = rule.get(schema.RULE_MATCH_VALUE)
        conditions = cast(List[Dict], rule.get(schema.CONDITIONS_KEY))

        if not conditions:
            self.logger.debug(
                f"rule did not match, no conditions to match, rule_name={rule_name}, rule_value={rule_match_value}, "
                f"name={feature_name} ",
            )
            return False

        for condition in conditions:
            context_value = context.get(condition.get(schema.CONDITION_KEY, ""))
            cond_action = condition.get(schema.CONDITION_ACTION, "")
            cond_value = condition.get(schema.CONDITION_VALUE)

            # time based rule actions have no user context. the context is the condition key
            if cond_action in (
                schema.RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
                schema.RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
                schema.RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
            ):
                context_value = condition.get(schema.CONDITION_KEY)  # e.g., CURRENT_TIME

            if not self._match_by_action(action=cond_action, condition_value=cond_value, context_value=context_value):
                self.logger.debug(
                    f"rule did not match action, rule_name={rule_name}, rule_value={rule_match_value}, "
                    f"name={feature_name}, context_value={str(context_value)} ",
                )
                return False  # context doesn't match condition

        self.logger.debug(f"rule matched, rule_name={rule_name}, rule_value={rule_match_value}, name={feature_name}")
        return True

    def _evaluate_rules(
        self,
        *,
        feature_name: str,
        context: Dict[str, Any],
        feat_default: Any,
        rules: Dict[str, Any],
        boolean_feature: bool,
    ) -> bool:
        """Evaluates whether context matches rules and conditions, otherwise return feature default"""
        for rule_name, rule in rules.items():
            rule_match_value = rule.get(schema.RULE_MATCH_VALUE)

            # Context might contain PII data; do not log its value
            self.logger.debug(
                f"Evaluating rule matching, rule={rule_name}, feature={feature_name}, default={str(feat_default)}, boolean_feature={boolean_feature}",  # noqa: E501
            )
            if self._evaluate_conditions(rule_name=rule_name, feature_name=feature_name, rule=rule, context=context):
                # Maintenance: Revisit before going GA.
                return bool(rule_match_value) if boolean_feature else rule_match_value

        # no rule matched, return default value of feature
        self.logger.debug(
            f"no rule matched, returning feature default, default={str(feat_default)}, name={feature_name}, boolean_feature={boolean_feature}",  # noqa: E501
        )
        return feat_default

    def get_configuration(self) -> Dict:
        """Get validated feature flag schema from configured store.

        Largely used to aid testing, since it's called by `evaluate` and `get_enabled_features` methods.

        Raises
        ------
        ConfigurationStoreError
            Any propagated error from store
        SchemaValidationError
            When schema doesn't conform with feature flag schema

        Returns
        ------
        Dict[str, Dict]
            parsed JSON dictionary

            **Example**

        ```python
        {
            "premium_features": {
                "default": False,
                "rules": {
                    "customer tier equals premium": {
                        "when_match": True,
                        "conditions": [
                            {
                                "action": "EQUALS",
                                "key": "tier",
                                "value": "premium",
                            }
                        ],
                    }
                },
            },
            "feature_two": {
                "default": False
            }
        }
        ```
        """
        # parse result conf as JSON, keep in cache for max age defined in store
        self.logger.debug(f"Fetching schema from registered store, store={self.store}")
        config: Dict = self.store.get_configuration()
        validator = schema.SchemaValidator(schema=config, logger=self.logger)
        validator.validate()

        return config

    def evaluate(self, *, name: str, context: Optional[Dict[str, Any]] = None, default: JSONType) -> JSONType:
        """Evaluate whether a feature flag should be enabled according to stored schema and input context

        **Logic when evaluating a feature flag**

        1. Feature exists and a rule matches, returns when_match value
        2. Feature exists but has either no rules or no match, return feature default value
        3. Feature doesn't exist in stored schema, encountered an error when fetching -> return default value provided

        Parameters
        ----------
        name: str
            feature name to evaluate
        context: Optional[Dict[str, Any]]
            Attributes that should be evaluated against the stored schema.

            for example: `{"tenant_id": "X", "username": "Y", "region": "Z"}`
        default: JSONType
            default value if feature flag doesn't exist in the schema,
            or there has been an error when fetching the configuration from the store
            Can be boolean or any JSON values for non-boolean features.

        Returns
        ------
        JSONType
            whether feature should be enabled (bool flags) or JSON value when non-bool feature matches

        Raises
        ------
        SchemaValidationError
            When schema doesn't conform with feature flag schema
        """
        if context is None:
            context = {}

        try:
            features = self.get_configuration()
        except ConfigurationStoreError as err:
            self.logger.debug(f"Failed to fetch feature flags from store, returning default provided, reason={err}")
            return default

        feature = features.get(name)
        if feature is None:
            self.logger.debug(f"Feature not found; returning default provided, name={name}, default={default}")
            return default

        rules = feature.get(schema.RULES_KEY)
        feat_default = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
        # Maintenance: Revisit before going GA. We might to simplify customers on-boarding by not requiring it
        # for non-boolean flags. It'll need minor implementation changes, docs changes, and maybe refactor
        # get_enabled_features. We can minimize breaking change, despite Beta label, by having a new
        # method `get_matching_features` returning Dict[feature_name, feature_value]
        boolean_feature = feature.get(
            schema.FEATURE_DEFAULT_VAL_TYPE_KEY,
            True,
        )  # backwards compatibility, assume feature flag
        if not rules:
            self.logger.debug(
                f"no rules found, returning feature default, name={name}, default={str(feat_default)}, boolean_feature={boolean_feature}",  # noqa: E501
            )
            # Maintenance: Revisit before going GA. We might to simplify customers on-boarding by not requiring it
            # for non-boolean flags.
            return bool(feat_default) if boolean_feature else feat_default

        self.logger.debug(
            f"looking for rule match, name={name}, default={str(feat_default)}, boolean_feature={boolean_feature}",  # noqa: E501
        )
        return self._evaluate_rules(
            feature_name=name,
            context=context,
            feat_default=feat_default,
            rules=rules,
            boolean_feature=boolean_feature,
        )

    def get_enabled_features(self, *, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get all enabled feature flags while also taking into account context
        (when a feature has defined rules)

        Parameters
        ----------
        context: Optional[Dict[str, Any]]
            dict of attributes that you would like to match the rules
            against, can be `{'tenant_id: 'X', 'username':' 'Y', 'region': 'Z'}` etc.

        Returns
        ----------
        List[str]
            list of all feature names that either matches context or have True as default

            **Example**

        ```python
        ["premium_features", "my_feature_two", "always_true_feature"]
        ```

        Raises
        ------
        SchemaValidationError
            When schema doesn't conform with feature flag schema
        """
        if context is None:
            context = {}

        features_enabled: List[str] = []

        try:
            features: Dict[str, Any] = self.get_configuration()
        except ConfigurationStoreError as err:
            self.logger.debug(f"Failed to fetch feature flags from store, returning empty list, reason={err}")
            return features_enabled

        self.logger.debug("Evaluating all features")
        for name, feature in features.items():
            rules = feature.get(schema.RULES_KEY, {})
            feature_default_value = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
            boolean_feature = feature.get(
                schema.FEATURE_DEFAULT_VAL_TYPE_KEY,
                True,
            )  # backwards compatibility, assume feature flag

            if feature_default_value and not rules:
                self.logger.debug(f"feature is enabled by default and has no defined rules, name={name}")
                features_enabled.append(name)
            elif self._evaluate_rules(
                feature_name=name,
                context=context,
                feat_default=feature_default_value,
                rules=rules,
                boolean_feature=boolean_feature,
            ):
                self.logger.debug(f"feature's calculated value is True, name={name}")
                features_enabled.append(name)

        return features_enabled

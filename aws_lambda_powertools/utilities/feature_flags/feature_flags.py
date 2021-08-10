import logging
from typing import Any, Dict, List, Optional, Union, cast

from . import schema
from .base import StoreProvider
from .exceptions import ConfigurationStoreError

logger = logging.getLogger(__name__)


class FeatureFlags:
    def __init__(self, store: StoreProvider):
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
        """
        self._store = store

    @staticmethod
    def _match_by_action(action: str, condition_value: Any, context_value: Any) -> bool:
        if not context_value:
            return False
        mapping_by_action = {
            schema.RuleAction.EQUALS.value: lambda a, b: a == b,
            schema.RuleAction.STARTSWITH.value: lambda a, b: a.startswith(b),
            schema.RuleAction.ENDSWITH.value: lambda a, b: a.endswith(b),
            schema.RuleAction.IN.value: lambda a, b: a in b,
            schema.RuleAction.NOT_IN.value: lambda a, b: a not in b,
        }

        try:
            func = mapping_by_action.get(action, lambda a, b: False)
            return func(context_value, condition_value)
        except Exception as exc:
            logger.debug(f"caught exception while matching action: action={action}, exception={str(exc)}")
            return False

    def _evaluate_conditions(
        self, rule_name: str, feature_name: str, rule: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Evaluates whether context matches conditions, return False otherwise"""
        rule_match_value = rule.get(schema.RULE_MATCH_VALUE)
        conditions = cast(List[Dict], rule.get(schema.CONDITIONS_KEY))

        if not conditions:
            logger.debug(
                f"rule did not match, no conditions to match, rule_name={rule_name}, rule_value={rule_match_value}, "
                f"name={feature_name} "
            )
            return False

        for condition in conditions:
            context_value = context.get(str(condition.get(schema.CONDITION_KEY)))
            cond_action = condition.get(schema.CONDITION_ACTION, "")
            cond_value = condition.get(schema.CONDITION_VALUE)

            if not self._match_by_action(action=cond_action, condition_value=cond_value, context_value=context_value):
                logger.debug(
                    f"rule did not match action, rule_name={rule_name}, rule_value={rule_match_value}, "
                    f"name={feature_name}, context_value={str(context_value)} "
                )
                return False  # context doesn't match condition

        logger.debug(f"rule matched, rule_name={rule_name}, rule_value={rule_match_value}, name={feature_name}")
        return True

    def _evaluate_rules(
        self, *, feature_name: str, context: Dict[str, Any], feat_default: bool, rules: Dict[str, Any]
    ) -> bool:
        """Evaluates whether context matches rules and conditions, otherwise return feature default"""
        for rule_name, rule in rules.items():
            rule_match_value = rule.get(schema.RULE_MATCH_VALUE)

            # Context might contain PII data; do not log its value
            logger.debug(f"Evaluating rule matching, rule={rule_name}, feature={feature_name}, default={feat_default}")
            if self._evaluate_conditions(rule_name=rule_name, feature_name=feature_name, rule=rule, context=context):
                return bool(rule_match_value)

            # no rule matched, return default value of feature
            logger.debug(f"no rule matched, returning feature default, default={feat_default}, name={feature_name}")
            return feat_default
        return False

    def get_configuration(self) -> Union[Dict[str, Dict], Dict]:
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
        logger.debug(f"Fetching schema from registered store, store={self._store}")
        config = self._store.get_configuration()
        validator = schema.SchemaValidator(schema=config)
        validator.validate()

        return config

    def evaluate(self, *, name: str, context: Optional[Dict[str, Any]] = None, default: bool) -> bool:
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
        default: bool
            default value if feature flag doesn't exist in the schema,
            or there has been an error when fetching the configuration from the store

        Returns
        ------
        bool
            whether feature should be enabled or not

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
            logger.debug(f"Failed to fetch feature flags from store, returning default provided, reason={err}")
            return default

        feature = features.get(name)
        if feature is None:
            logger.debug(f"Feature not found; returning default provided, name={name}, default={default}")
            return default

        rules = feature.get(schema.RULES_KEY)
        feat_default = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
        if not rules:
            logger.debug(f"no rules found, returning feature default, name={name}, default={feat_default}")
            return bool(feat_default)

        logger.debug(f"looking for rule match, name={name}, default={feat_default}")
        return self._evaluate_rules(feature_name=name, context=context, feat_default=bool(feat_default), rules=rules)

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
            logger.debug(f"Failed to fetch feature flags from store, returning empty list, reason={err}")
            return features_enabled

        logger.debug("Evaluating all features")
        for name, feature in features.items():
            rules = feature.get(schema.RULES_KEY, {})
            feature_default_value = feature.get(schema.FEATURE_DEFAULT_VAL_KEY)
            if feature_default_value and not rules:
                logger.debug(f"feature is enabled by default and has no defined rules, name={name}")
                features_enabled.append(name)
            elif self._evaluate_rules(
                feature_name=name, context=context, feat_default=feature_default_value, rules=rules
            ):
                logger.debug(f"feature's calculated value is True, name={name}")
                features_enabled.append(name)

        return features_enabled

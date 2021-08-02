import logging
from enum import Enum
from typing import Any, Dict, Optional

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

FEATURES_KEY = "features"
RULES_KEY = "rules"
FEATURE_DEFAULT_VAL_KEY = "feature_default_value"
CONDITIONS_KEY = "conditions"
RULE_NAME_KEY = "rule_name"
RULE_DEFAULT_VALUE = "value_when_applies"
CONDITION_KEY = "key"
CONDITION_VALUE = "value"
CONDITION_ACTION = "action"


class ACTION(str, Enum):
    EQUALS = "EQUALS"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    CONTAINS = "CONTAINS"


class SchemaValidator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    @staticmethod
    def _is_dict_and_non_empty(value: Optional[Dict]):
        return not value or not isinstance(value, dict)

    @staticmethod
    def _validate_condition(rule_name: str, condition: Dict[str, str]) -> None:
        if not condition or not isinstance(condition, dict):
            raise ConfigurationError(f"invalid condition type, not a dictionary, rule_name={rule_name}")

        action = condition.get(CONDITION_ACTION, "")
        if action not in [ACTION.EQUALS.value, ACTION.STARTSWITH.value, ACTION.ENDSWITH.value, ACTION.CONTAINS.value]:
            raise ConfigurationError(f"invalid action value, rule_name={rule_name}, action={action}")

        key = condition.get(CONDITION_KEY, "")
        if not key or not isinstance(key, str):
            raise ConfigurationError(f"Invalid key value, key has to be a non empty string, rule_name={rule_name}")

        value = condition.get(CONDITION_VALUE, "")
        if not value:
            raise ConfigurationError(f"Missing condition value, rule_name={rule_name}")

    def _validate_rule(self, feature_name: str, rule: Dict[str, Any]) -> None:
        if not rule or not isinstance(rule, dict):
            raise ConfigurationError(f"Feature rule is not a dictionary, feature_name={feature_name}")

        rule_name = rule.get(RULE_NAME_KEY)
        if not rule_name or rule_name is None or not isinstance(rule_name, str):
            raise ConfigurationError(f"Invalid rule_name, feature_name={feature_name}")

        rule_default_value = rule.get(RULE_DEFAULT_VALUE)
        if rule_default_value is None or not isinstance(rule_default_value, bool):
            raise ConfigurationError(f"Invalid rule_default_value, rule_name={rule_name}")

        conditions = rule.get(CONDITIONS_KEY, {})
        if not conditions or not isinstance(conditions, list):
            raise ConfigurationError(f"Invalid condition, rule_name={rule_name}")

        # validate conditions
        for condition in conditions:
            self._validate_condition(rule_name, condition)

    def _validate_feature(self, name: str, feature: Dict[str, Any]) -> None:
        if not feature or not isinstance(feature, dict):
            raise ConfigurationError(f"Invalid AWS AppConfig JSON schema detected, feature {name} is invalid")

        feature_default_value = feature.get(FEATURE_DEFAULT_VAL_KEY)
        if feature_default_value is None or not isinstance(feature_default_value, bool):
            raise ConfigurationError(f"Missing feature_default_value for feature, feature_name={name}")

        # validate rules
        rules = feature.get(RULES_KEY, [])
        if not rules:
            return

        if not isinstance(rules, list):
            raise ConfigurationError(f"Feature rules is not a list, feature_name={name}")

        for rule in rules:
            self._validate_rule(name, rule)

    def validate(self) -> None:
        if self._is_dict_and_non_empty(self.schema):
            raise ConfigurationError(f"Schema must be a dictionary, schema={str(self.schema)}")

        features: Optional[Dict[str, Dict]] = self.schema.get(FEATURES_KEY)
        if not isinstance(features, dict):
            raise ConfigurationError(f"'features' key must be present, schema={self.schema}")

        for name, feature in features.items():
            self._validate_feature(name, feature)

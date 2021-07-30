from enum import Enum
from logging import Logger
from typing import Any, Dict

from .exceptions import ConfigurationError

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
    def __init__(self, logger: Logger):
        self._logger = logger

    def _validate_condition(self, rule_name: str, condition: Dict[str, str]) -> None:
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

    def _validate_feature(self, feature_name: str, feature_dict_def: Dict[str, Any]) -> None:
        if not feature_dict_def or not isinstance(feature_dict_def, dict):
            raise ConfigurationError(f"Invalid AWS AppConfig JSON schema detected, feature {feature_name} is invalid")

        feature_default_value = feature_dict_def.get(FEATURE_DEFAULT_VAL_KEY)
        if feature_default_value is None or not isinstance(feature_default_value, bool):
            raise ConfigurationError(f"Missing feature_default_value for feature, feature_name={feature_name}")

        # validate rules
        rules = feature_dict_def.get(RULES_KEY, [])
        if not rules:
            return

        if not isinstance(rules, list):
            raise ConfigurationError(f"Feature rules is not a list, feature_name={feature_name}")

        for rule in rules:
            self._validate_rule(feature_name, rule)

    def validate_json_schema(self, schema: Dict[str, Any]) -> None:
        if not isinstance(schema, dict):
            raise ConfigurationError("invalid AWS AppConfig JSON schema detected, root schema is not a dictionary")

        features_dict = schema.get(FEATURES_KEY)
        if not isinstance(features_dict, dict):
            raise ConfigurationError("invalid AWS AppConfig JSON schema detected, missing features dictionary")

        for feature_name, feature_dict_def in features_dict.items():
            self._validate_feature(feature_name, feature_dict_def)

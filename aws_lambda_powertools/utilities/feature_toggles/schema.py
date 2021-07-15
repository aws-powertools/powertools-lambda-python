from enum import Enum
from typing import Any, Dict

from .exceptions import ConfigurationException

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
    def __init__(self, logger: object):
        self._logger = logger

    def _raise_conf_exc(self, error_str: str) -> None:
        self._logger.error(error_str)
        raise ConfigurationException(error_str)

    def _validate_condition(self, rule_name: str, condition: Dict[str, str]) -> None:
        if not condition or not isinstance(condition, dict):
            self._raise_conf_exc(f"invalid condition type, not a dictionary, rule_name={rule_name}")
        action = condition.get(CONDITION_ACTION, "")
        if action not in [ACTION.EQUALS.value, ACTION.STARTSWITH.value, ACTION.ENDSWITH.value, ACTION.CONTAINS.value]:
            self._raise_conf_exc(f"invalid action value, rule_name={rule_name}, action={action}")
        key = condition.get(CONDITION_KEY, "")
        if not key or not isinstance(key, str):
            self._raise_conf_exc(f"invalid key value, key has to be a non empty string, rule_name={rule_name}")
        value = condition.get(CONDITION_VALUE, "")
        if not value:
            self._raise_conf_exc(f"missing condition value, rule_name={rule_name}")

    def _validate_rule(self, feature_name: str, rule: Dict[str, Any]) -> None:
        if not rule or not isinstance(rule, dict):
            self._raise_conf_exc(f"feature rule is not a dictionary, feature_name={feature_name}")
        rule_name = rule.get(RULE_NAME_KEY)
        if not rule_name or rule_name is None or not isinstance(rule_name, str):
            self._raise_conf_exc(f"invalid rule_name, feature_name={feature_name}")
        rule_default_value = rule.get(RULE_DEFAULT_VALUE)
        if rule_default_value is None or not isinstance(rule_default_value, bool):
            self._raise_conf_exc(f"invalid rule_default_value, rule_name={rule_name}")
        conditions = rule.get(CONDITIONS_KEY, {})
        if not conditions or not isinstance(conditions, list):
            self._raise_conf_exc(f"invalid condition, rule_name={rule_name}")
        # validate conditions
        for condition in conditions:
            self._validate_condition(rule_name, condition)

    def _validate_feature(self, feature_name: str, feature_dict_def: Dict[str, Any]) -> None:
        if not feature_dict_def or not isinstance(feature_dict_def, dict):
            self._raise_conf_exc(f"invalid AWS AppConfig JSON schema detected, feature {feature_name} is invalid")
        feature_default_value = feature_dict_def.get(FEATURE_DEFAULT_VAL_KEY)
        if feature_default_value is None or not isinstance(feature_default_value, bool):
            self._raise_conf_exc(f"missing feature_default_value for feature, feature_name={feature_name}")
        # validate rules
        rules = feature_dict_def.get(RULES_KEY, [])
        if not rules:
            return
        if not isinstance(rules, list):
            self._raise_conf_exc(f"feature rules is not a list, feature_name={feature_name}")
        for rule in rules:
            self._validate_rule(feature_name, rule)

    def validate_json_schema(self, schema: Dict[str, Any]) -> None:
        if not isinstance(schema, dict):
            self._raise_conf_exc("invalid AWS AppConfig JSON schema detected, root schema is not a dictionary")
        features_dict: Dict = schema.get(FEATURES_KEY)
        if not isinstance(features_dict, dict):
            self._raise_conf_exc("invalid AWS AppConfig JSON schema detected, missing features dictionary")
        for feature_name, feature_dict_def in features_dict.items():
            self._validate_feature(feature_name, feature_dict_def)

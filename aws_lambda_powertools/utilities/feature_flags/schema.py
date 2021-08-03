import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from .base import BaseValidator
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

RULES_KEY = "rules"
FEATURE_DEFAULT_VAL_KEY = "default"
CONDITIONS_KEY = "conditions"
RULE_DEFAULT_VALUE = "when_match"
CONDITION_KEY = "key"
CONDITION_VALUE = "value"
CONDITION_ACTION = "action"


class RuleAction(str, Enum):
    EQUALS = "EQUALS"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    CONTAINS = "CONTAINS"


class SchemaValidator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self) -> None:
        if not isinstance(self.schema, dict):
            raise ConfigurationError(f"Features must be a dictionary, schema={str(self.schema)}")

        features = FeaturesValidator(schema=self.schema)
        features.validate()


class FeaturesValidator(BaseValidator):
    def __init__(self, schema: Dict):
        self.schema = schema

    def validate(self):
        for name, feature in self.schema.items():
            self.validate_feature(name, feature)
            rules = RulesValidator(feature=feature)
            rules.validate()

    @staticmethod
    def validate_feature(name, feature):
        if not feature or not isinstance(feature, dict):
            raise ConfigurationError(f"Feature must be a non-empty dictionary, feature={name}")

        default_value = feature.get(FEATURE_DEFAULT_VAL_KEY)
        if default_value is None or not isinstance(default_value, bool):
            raise ConfigurationError(f"'feature_default_value' boolean key must be present, feature_name={name}")


class RulesValidator(BaseValidator):
    def __init__(self, feature: Dict[str, Any]):
        self.feature = feature
        self.feature_name = next(iter(self.feature))
        self.rules: Optional[Dict] = self.feature.get(RULES_KEY)

    def validate(self):
        if not self.rules:
            logger.debug("Rules are empty, ignoring validation")
            return

        if not isinstance(self.rules, dict):
            raise ConfigurationError(f"Feature rules must be a dictionary, feature_name={self.feature_name}")

        for rule_name, rule in self.rules.items():
            self.validate_rule(rule=rule, rule_name=rule_name, feature_name=self.feature_name)
            conditions = ConditionsValidator(rule=rule, rule_name=rule_name)
            conditions.validate()

    @staticmethod
    def validate_rule(rule, rule_name, feature_name):
        if not rule or not isinstance(rule, dict):
            raise ConfigurationError(f"Feature rule must be a dictionary, feature_name={feature_name}")

        RulesValidator.validate_rule_name(rule_name=rule_name, feature_name=feature_name)
        RulesValidator.validate_rule_default_value(rule=rule, rule_name=rule_name)

    @staticmethod
    def validate_rule_name(rule_name: str, feature_name: str):
        if not rule_name or not isinstance(rule_name, str):
            raise ConfigurationError(f"Rule name key must have a non-empty string, feature_name={feature_name}")

    @staticmethod
    def validate_rule_default_value(rule: Dict, rule_name: str):
        rule_default_value = rule.get(RULE_DEFAULT_VALUE)
        if not isinstance(rule_default_value, bool):
            raise ConfigurationError(f"'rule_default_value' key must have be bool, rule_name={rule_name}")


class ConditionsValidator(BaseValidator):
    def __init__(self, rule: Dict[str, Any], rule_name: str):
        self.conditions: List[Dict[str, Any]] = rule.get(CONDITIONS_KEY, {})
        self.rule_name = rule_name

    def validate(self):
        if not self.conditions or not isinstance(self.conditions, list):
            raise ConfigurationError(f"Invalid condition, rule_name={self.rule_name}")

        for condition in self.conditions:
            self.validate_condition(rule_name=self.rule_name, condition=condition)

    @staticmethod
    def validate_condition(rule_name: str, condition: Dict[str, str]) -> None:
        if not condition or not isinstance(condition, dict):
            raise ConfigurationError(f"Feature rule condition must be a dictionary, rule_name={rule_name}")

        ConditionsValidator.validate_condition_action(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)

    @staticmethod
    def validate_condition_action(condition: Dict[str, Any], rule_name: str):
        action = condition.get(CONDITION_ACTION, "")
        if action not in RuleAction.__members__:
            allowed_values = [_action.value for _action in RuleAction]
            raise ConfigurationError(
                f"'action' value must be either {allowed_values}, rule_name={rule_name}, action={action}"
            )

    @staticmethod
    def validate_condition_key(condition: Dict[str, Any], rule_name: str):
        key = condition.get(CONDITION_KEY, "")
        if not key or not isinstance(key, str):
            raise ConfigurationError(f"'key' value must be a non empty string, rule_name={rule_name}")

    @staticmethod
    def validate_condition_value(condition: Dict[str, Any], rule_name: str):
        value = condition.get(CONDITION_VALUE, "")
        if not value:
            raise ConfigurationError(f"'value' key must not be empty, rule_name={rule_name}")

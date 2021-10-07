import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ... import Logger
from .base import BaseValidator
from .exceptions import SchemaValidationError

RULES_KEY = "rules"
FEATURE_DEFAULT_VAL_KEY = "default"
CONDITIONS_KEY = "conditions"
RULE_MATCH_VALUE = "when_match"
CONDITION_KEY = "key"
CONDITION_VALUE = "value"
CONDITION_ACTION = "action"


class RuleAction(str, Enum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    KEY_GREATER_THAN_VALUE = "KEY_GREATER_THAN_VALUE"
    KEY_GREATER_THAN_OR_EQUAL_VALUE = "KEY_GREATER_THAN_OR_EQUAL_VALUE"
    KEY_LESS_THAN_VALUE = "KEY_LESS_THAN_VALUE"
    KEY_LESS_THAN_OR_EQUAL_VALUE = "KEY_LESS_THAN_OR_EQUAL_VALUE"
    STARTSWITH = "STARTSWITH"
    ENDSWITH = "ENDSWITH"
    IN = "IN"
    NOT_IN = "NOT_IN"
    KEY_IN_VALUE = "KEY_IN_VALUE"
    KEY_NOT_IN_VALUE = "KEY_NOT_IN_VALUE"
    VALUE_IN_KEY = "VALUE_IN_KEY"
    VALUE_NOT_IN_KEY = "VALUE_NOT_IN_KEY"


class SchemaValidator(BaseValidator):
    """Validates feature flag schema configuration

    Raises
    ------
    SchemaValidationError
        When schema doesn't conform with feature flag schema

    Schema
    ------

    **Feature object**

    A dictionary containing default value and rules for matching.
    The value MUST be an object and MIGHT contain the following members:

    * **default**: `bool`. Defines default feature value. This MUST be present
    * **rules**: `Dict[str, Dict]`. Rules object. This MIGHT be present

    ```python
    {
        "my_feature": {
            "default": True,
            "rules": {}
        }
    }
    ```

    **Rules object**

    A dictionary with each rule and their conditions that a feature might have.
    The value MIGHT be present, and when defined it MUST contain the following members:

    * **when_match**: `bool`. Defines value to return when context matches conditions
    * **conditions**: `List[Dict]`. Conditions object. This MUST be present

    ```python
    {
        "my_feature": {
            "default": True,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": False,
                    "conditions": []
                }
            }
        }
    }
    ```

    **Conditions object**

    A list of dictionaries containing conditions for a given rule.
    The value MUST contain the following members:

    * **action**: `str`. Operation to perform to match a key and value.
    The value MUST be either EQUALS, STARTSWITH, ENDSWITH,
    KEY_IN_VALUE KEY_NOT_IN_VALUE VALUE_IN_KEY VALUE_NOT_IN_KEY

    * **key**: `str`. Key in given context to perform operation
    * **value**: `Any`. Value in given context that should match action operation.

    ```python
    {
        "my_feature": {
            "default": True,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": False,
                    "conditions": [
                        {
                            "action": "EQUALS",
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ]
                }
            }
        }
    }
    ```
    """

    def __init__(self, schema: Dict[str, Any], logger: Optional[Union[logging.Logger, Logger]] = None):
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__)

    def validate(self) -> None:
        self.logger.debug("Validating schema")
        if not isinstance(self.schema, dict):
            raise SchemaValidationError(f"Features must be a dictionary, schema={str(self.schema)}")

        features = FeaturesValidator(schema=self.schema)
        features.validate()


class FeaturesValidator(BaseValidator):
    """Validates each feature and calls RulesValidator to validate its rules"""

    def __init__(self, schema: Dict, logger: Optional[Union[logging.Logger, Logger]] = None):
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__)

    def validate(self):
        for name, feature in self.schema.items():
            self.logger.debug(f"Attempting to validate feature '{name}'")
            self.validate_feature(name, feature)
            rules = RulesValidator(feature=feature)
            rules.validate()

    @staticmethod
    def validate_feature(name, feature):
        if not feature or not isinstance(feature, dict):
            raise SchemaValidationError(f"Feature must be a non-empty dictionary, feature={name}")

        default_value = feature.get(FEATURE_DEFAULT_VAL_KEY)
        if default_value is None or not isinstance(default_value, bool):
            raise SchemaValidationError(f"feature 'default' boolean key must be present, feature={name}")


class RulesValidator(BaseValidator):
    """Validates each rule and calls ConditionsValidator to validate each rule's conditions"""

    def __init__(self, feature: Dict[str, Any], logger: Optional[Union[logging.Logger, Logger]] = None):
        self.feature = feature
        self.feature_name = next(iter(self.feature))
        self.rules: Optional[Dict] = self.feature.get(RULES_KEY)
        self.logger = logger or logging.getLogger(__name__)

    def validate(self):
        if not self.rules:
            self.logger.debug("Rules are empty, ignoring validation")
            return

        if not isinstance(self.rules, dict):
            raise SchemaValidationError(f"Feature rules must be a dictionary, feature={self.feature_name}")

        for rule_name, rule in self.rules.items():
            self.logger.debug(f"Attempting to validate rule '{rule_name}'")
            self.validate_rule(rule=rule, rule_name=rule_name, feature_name=self.feature_name)
            conditions = ConditionsValidator(rule=rule, rule_name=rule_name)
            conditions.validate()

    @staticmethod
    def validate_rule(rule, rule_name, feature_name):
        if not rule or not isinstance(rule, dict):
            raise SchemaValidationError(f"Feature rule must be a dictionary, feature={feature_name}")

        RulesValidator.validate_rule_name(rule_name=rule_name, feature_name=feature_name)
        RulesValidator.validate_rule_default_value(rule=rule, rule_name=rule_name)

    @staticmethod
    def validate_rule_name(rule_name: str, feature_name: str):
        if not rule_name or not isinstance(rule_name, str):
            raise SchemaValidationError(f"Rule name key must have a non-empty string, feature={feature_name}")

    @staticmethod
    def validate_rule_default_value(rule: Dict, rule_name: str):
        rule_default_value = rule.get(RULE_MATCH_VALUE)
        if not isinstance(rule_default_value, bool):
            raise SchemaValidationError(f"'rule_default_value' key must have be bool, rule={rule_name}")


class ConditionsValidator(BaseValidator):
    def __init__(self, rule: Dict[str, Any], rule_name: str, logger: Optional[Union[logging.Logger, Logger]] = None):
        self.conditions: List[Dict[str, Any]] = rule.get(CONDITIONS_KEY, {})
        self.rule_name = rule_name
        self.logger = logger or logging.getLogger(__name__)

    def validate(self):
        if not self.conditions or not isinstance(self.conditions, list):
            raise SchemaValidationError(f"Invalid condition, rule={self.rule_name}")

        for condition in self.conditions:
            # Condition can contain PII data; do not log condition value
            self.logger.debug(f"Attempting to validate condition for '{self.rule_name}'")
            self.validate_condition(rule_name=self.rule_name, condition=condition)

    @staticmethod
    def validate_condition(rule_name: str, condition: Dict[str, str]) -> None:
        if not condition or not isinstance(condition, dict):
            raise SchemaValidationError(f"Feature rule condition must be a dictionary, rule={rule_name}")

        ConditionsValidator.validate_condition_action(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)

    @staticmethod
    def validate_condition_action(condition: Dict[str, Any], rule_name: str):
        action = condition.get(CONDITION_ACTION, "")
        if action not in RuleAction.__members__:
            allowed_values = [_action.value for _action in RuleAction]
            raise SchemaValidationError(
                f"'action' value must be either {allowed_values}, rule_name={rule_name}, action={action}"
            )

    @staticmethod
    def validate_condition_key(condition: Dict[str, Any], rule_name: str):
        key = condition.get(CONDITION_KEY, "")
        if not key or not isinstance(key, str):
            raise SchemaValidationError(f"'key' value must be a non empty string, rule={rule_name}")

    @staticmethod
    def validate_condition_value(condition: Dict[str, Any], rule_name: str):
        value = condition.get(CONDITION_VALUE, "")
        if not value:
            raise SchemaValidationError(f"'value' key must not be empty, rule={rule_name}")

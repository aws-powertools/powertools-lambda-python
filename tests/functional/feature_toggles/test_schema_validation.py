import logging

import pytest  # noqa: F401

from aws_lambda_powertools.utilities.feature_flags.exceptions import ConfigurationError
from aws_lambda_powertools.utilities.feature_flags.schema import (
    CONDITION_ACTION,
    CONDITION_KEY,
    CONDITION_VALUE,
    CONDITIONS_KEY,
    FEATURE_DEFAULT_VAL_KEY,
    FEATURES_KEY,
    RULE_DEFAULT_VALUE,
    RULE_NAME_KEY,
    RULES_KEY,
    ConditionsValidator,
    RuleAction,
    RulesValidator,
    SchemaValidator,
)

logger = logging.getLogger(__name__)

EMPTY_SCHEMA = {"": ""}


def test_invalid_features_dict():
    schema = {}
    # empty dict
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    schema = []
    # invalid type
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # invalid features key
    schema = {FEATURES_KEY: []}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()


def test_empty_features_not_fail():
    schema = {FEATURES_KEY: {}}
    validator = SchemaValidator(schema)
    validator.validate()


def test_invalid_feature_dict():
    # invalid feature type, not dict
    schema = {FEATURES_KEY: {"my_feature": []}}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # empty feature dict
    schema = {FEATURES_KEY: {"my_feature": {}}}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: "False"}}}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean #2
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: 5}}}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # invalid rules type, not list
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: "4"}}}
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()


def test_valid_feature_dict():
    # empty rules list
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: []}}}
    validator = SchemaValidator(schema)
    validator.validate()

    # no rules list at all
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False}}}
    validator = SchemaValidator(schema)
    validator.validate()


def test_invalid_rule():
    # rules list is not a list of dict
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    "a",
                    "b",
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # rules RULE_DEFAULT_VALUE is not bool
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: "False",
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # missing conditions list
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # condition list is empty
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {RULE_NAME_KEY: "tenant id equals 345345435", RULE_DEFAULT_VALUE: False, CONDITIONS_KEY: []},
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # condition is invalid type, not list
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {RULE_NAME_KEY: "tenant id equals 345345435", RULE_DEFAULT_VALUE: False, CONDITIONS_KEY: {}},
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()


def test_invalid_condition():
    # invalid condition action
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        CONDITIONS_KEY: {CONDITION_ACTION: "stuff", CONDITION_KEY: "a", CONDITION_VALUE: "a"},
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # missing condition key and value
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        CONDITIONS_KEY: {CONDITION_ACTION: RuleAction.EQUALS.value},
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()

    # invalid condition key type, not string
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        CONDITIONS_KEY: {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: 5,
                            CONDITION_VALUE: "a",
                        },
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(schema)
    with pytest.raises(ConfigurationError):
        validator.validate()


def test_valid_condition_all_actions():
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 645654 and username is a",
                        RULE_DEFAULT_VALUE: True,
                        CONDITIONS_KEY: [
                            {
                                CONDITION_ACTION: RuleAction.EQUALS.value,
                                CONDITION_KEY: "tenant_id",
                                CONDITION_VALUE: "645654",
                            },
                            {
                                CONDITION_ACTION: RuleAction.STARTSWITH.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: "a",
                            },
                            {
                                CONDITION_ACTION: RuleAction.ENDSWITH.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: "a",
                            },
                            {
                                CONDITION_ACTION: RuleAction.CONTAINS.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: ["a", "b"],
                            },
                        ],
                    },
                ],
            }
        },
    }
    validator = SchemaValidator(schema)
    validator.validate()


def test_validate_condition_invalid_condition_type():
    # GIVEN an invalid condition type of empty dict
    rule_conditions = {"conditions": {}}
    condition = rule_conditions[CONDITIONS_KEY]
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Invalid condition type"):
        validator = ConditionsValidator(rule=rule_conditions, rule_name=rule_name)
        validator.validate_condition(condition=condition, rule_name=rule_name)


def test_validate_condition_invalid_condition_action():
    # GIVEN an invalid condition action of foo
    rule_conditions = {
        "conditions": [{"action": "INVALID", "key": "tenant_id", "value": "12345"}],
    }
    condition = rule_conditions[CONDITIONS_KEY][0]
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Invalid action value"):
        validator = ConditionsValidator(rule=rule_conditions, rule_name=rule_name)
        validator.validate_condition_action(condition=condition, rule_name=rule_name)


def test_validate_condition_invalid_condition_key():
    # GIVEN a configuration with a missing "key"
    rule_conditions = {
        "conditions": [{"action": RuleAction.EQUALS.value, "value": "12345"}],
    }
    condition = rule_conditions[CONDITIONS_KEY][0]
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Invalid key value"):
        validator = ConditionsValidator(rule=rule_conditions, rule_name=rule_name)
        validator.validate_condition_key(condition=condition, rule_name=rule_name)


def test_validate_condition_missing_condition_value():
    # GIVEN a configuration with a missing condition value
    rule_conditions = {
        "conditions": [
            {
                "action": RuleAction.EQUALS.value,
                "key": "tenant_id",
            }
        ],
    }
    condition = rule_conditions[CONDITIONS_KEY][0]
    rule_name = "dummy"

    # WHEN calling validate_condition
    with pytest.raises(ConfigurationError, match="Missing condition value"):
        validator = ConditionsValidator(rule=rule_conditions, rule_name=rule_name)
        validator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_rule_invalid_rule_name():
    # GIVEN a rule_name not in the rule dict
    feature = {
        "feature_default_value": True,
        "rules": [
            {"invalid_rule_name": "tenant id equals 345345435"},
        ],
    }
    rule = feature[RULES_KEY][0]

    # WHEN calling _validate_rule
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="'rule_name' key must be present*"):
        rules_validator = RulesValidator(feature=feature, feature_name="my_feature")
        rules_validator.validate_rule_name(rule=rule, feature_name="my_feature")

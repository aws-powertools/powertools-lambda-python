import logging

import pytest  # noqa: F401

from aws_lambda_powertools.utilities.feature_toggles.exceptions import ConfigurationError
from aws_lambda_powertools.utilities.feature_toggles.schema import (
    ACTION,
    CONDITION_ACTION,
    CONDITION_KEY,
    CONDITION_VALUE,
    CONDITIONS_KEY,
    FEATURE_DEFAULT_VAL_KEY,
    FEATURES_KEY,
    RULE_DEFAULT_VALUE,
    RULE_NAME_KEY,
    RULES_KEY,
    SchemaValidator,
)

logger = logging.getLogger(__name__)


def test_invalid_features_dict():
    schema = {}
    # empty dict
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    schema = []
    # invalid type
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # invalid features key
    schema = {FEATURES_KEY: []}
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)


def test_empty_features_not_fail():
    schema = {FEATURES_KEY: {}}
    validator = SchemaValidator(logger)
    validator.validate_json_schema(schema)


def test_invalid_feature_dict():
    # invalid feature type, not dict
    schema = {FEATURES_KEY: {"my_feature": []}}
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # empty feature dict
    schema = {FEATURES_KEY: {"my_feature": {}}}
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: "False"}}}
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean #2
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: 5}}}
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # invalid rules type, not list
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: "4"}}}
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)


def test_valid_feature_dict():
    # no rules list at all
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False}}}
    validator = SchemaValidator(logger)
    validator.validate_json_schema(schema)

    # empty rules list
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: []}}}
    validator.validate_json_schema(schema)


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
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

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
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

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
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

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
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

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
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)


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
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

    # missing condition key and value
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        CONDITIONS_KEY: {CONDITION_ACTION: ACTION.EQUALS.value},
                    },
                ],
            }
        }
    }
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)

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
                            CONDITION_ACTION: ACTION.EQUALS.value,
                            CONDITION_KEY: 5,
                            CONDITION_VALUE: "a",
                        },
                    },
                ],
            }
        }
    }
    with pytest.raises(ConfigurationError):
        validator.validate_json_schema(schema)


def test_valid_condition_all_actions():
    validator = SchemaValidator(logger)
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
                                CONDITION_ACTION: ACTION.EQUALS.value,
                                CONDITION_KEY: "tenant_id",
                                CONDITION_VALUE: "645654",
                            },
                            {
                                CONDITION_ACTION: ACTION.STARTSWITH.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: "a",
                            },
                            {
                                CONDITION_ACTION: ACTION.ENDSWITH.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: "a",
                            },
                            {
                                CONDITION_ACTION: ACTION.CONTAINS.value,
                                CONDITION_KEY: "username",
                                CONDITION_VALUE: ["a", "b"],
                            },
                        ],
                    },
                ],
            }
        },
    }
    validator.validate_json_schema(schema)


def test_validate_condition_invalid_condition_type():
    # GIVEN an invalid condition type of empty dict
    validator = SchemaValidator(logger)
    condition = {}

    # WHEN calling _validate_condition
    with pytest.raises(ConfigurationError) as err:
        validator._validate_condition("foo", condition)

    # THEN raise ConfigurationError
    assert "invalid condition type" in str(err)


def test_validate_condition_invalid_condition_action():
    # GIVEN an invalid condition action of foo
    validator = SchemaValidator(logger)
    condition = {"action": "foo"}

    # WHEN calling _validate_condition
    with pytest.raises(ConfigurationError) as err:
        validator._validate_condition("foo", condition)

    # THEN raise ConfigurationError
    assert "invalid action value" in str(err)


def test_validate_condition_invalid_condition_key():
    # GIVEN a configuration with a missing "key"
    validator = SchemaValidator(logger)
    condition = {"action": ACTION.EQUALS.value}

    # WHEN calling _validate_condition
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Invalid key value"):
        validator._validate_condition("foo", condition)


def test_validate_condition_missing_condition_value():
    # GIVEN a configuration with a missing condition value
    validator = SchemaValidator(logger)
    condition = {"action": ACTION.EQUALS.value, "key": "Foo"}

    # WHEN calling _validate_condition
    with pytest.raises(ConfigurationError, match="Missing condition value"):
        validator._validate_condition("foo", condition)


def test_validate_rule_invalid_rule_name():
    # GIVEN a rule_name not in the rule dict
    validator = SchemaValidator(logger)
    rule_name = "invalid_rule_name"
    rule = {"missing": ""}

    # WHEN calling _validate_rule
    # THEN raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Invalid rule_name"):
        validator._validate_rule(rule_name, rule)

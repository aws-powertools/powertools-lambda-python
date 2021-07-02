import logging

import pytest  # noqa: F401

from aws_lambda_powertools.utilities.feature_toggles.exceptions import ConfigurationException
from aws_lambda_powertools.utilities.feature_toggles.schema import (
    ACTION,
    FEATURE_DEFAULT_VAL_KEY,
    FEATURES_KEY,
    RESTRICTION_ACTION,
    RESTRICTION_KEY,
    RESTRICTION_VALUE,
    RESTRICTIONS_KEY,
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
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    schema = []
    # invalid type
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # invalid features key
    schema = {FEATURES_KEY: []}
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)


def test_empty_features_not_fail():
    schema = {FEATURES_KEY: {}}
    validator = SchemaValidator(logger)
    validator.validate_json_schema(schema)


def test_invalid_feature_dict():
    # invalid feature type, not dict
    schema = {FEATURES_KEY: {"my_feature": []}}
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # empty feature dict
    schema = {FEATURES_KEY: {"my_feature": {}}}
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: "False"}}}
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # invalid FEATURE_DEFAULT_VAL_KEY type, not boolean #2
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: 5}}}
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # invalid rules type, not list
    schema = {FEATURES_KEY: {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: "4"}}}
    with pytest.raises(ConfigurationException):
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
    with pytest.raises(ConfigurationException):
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
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # missing restrictions list
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
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # restriction list is empty
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {RULE_NAME_KEY: "tenant id equals 345345435", RULE_DEFAULT_VALUE: False, RESTRICTIONS_KEY: []},
                ],
            }
        }
    }
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # restriction is invalid type, not list
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {RULE_NAME_KEY: "tenant id equals 345345435", RULE_DEFAULT_VALUE: False, RESTRICTIONS_KEY: {}},
                ],
            }
        }
    }
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)


def test_invalid_restriction():
    # invalid restriction action
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        RESTRICTIONS_KEY: {RESTRICTION_ACTION: "stuff", RESTRICTION_KEY: "a", RESTRICTION_VALUE: "a"},
                    },
                ],
            }
        }
    }
    validator = SchemaValidator(logger)
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # missing restriction key and value
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        RESTRICTIONS_KEY: {RESTRICTION_ACTION: ACTION.EQUALS.value},
                    },
                ],
            }
        }
    }
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)

    # invalid restriction key type, not string
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 345345435",
                        RULE_DEFAULT_VALUE: False,
                        RESTRICTIONS_KEY: {
                            RESTRICTION_ACTION: ACTION.EQUALS.value,
                            RESTRICTION_KEY: 5,
                            RESTRICTION_VALUE: "a",
                        },
                    },
                ],
            }
        }
    }
    with pytest.raises(ConfigurationException):
        validator.validate_json_schema(schema)


def test_valid_restriction_all_actions():
    validator = SchemaValidator(logger)
    schema = {
        FEATURES_KEY: {
            "my_feature": {
                FEATURE_DEFAULT_VAL_KEY: False,
                RULES_KEY: [
                    {
                        RULE_NAME_KEY: "tenant id equals 645654 and username is a",
                        RULE_DEFAULT_VALUE: True,
                        RESTRICTIONS_KEY: [
                            {
                                RESTRICTION_ACTION: ACTION.EQUALS.value,
                                RESTRICTION_KEY: "tenant_id",
                                RESTRICTION_VALUE: "645654",
                            },
                            {
                                RESTRICTION_ACTION: ACTION.STARTSWITH.value,
                                RESTRICTION_KEY: "username",
                                RESTRICTION_VALUE: "a",
                            },
                            {
                                RESTRICTION_ACTION: ACTION.ENDSWITH.value,
                                RESTRICTION_KEY: "username",
                                RESTRICTION_VALUE: "a",
                            },
                            {
                                RESTRICTION_ACTION: ACTION.CONTAINS.value,
                                RESTRICTION_KEY: "username",
                                RESTRICTION_VALUE: ["a", "b"],
                            },
                        ],
                    },
                ],
            }
        },
    }
    validator.validate_json_schema(schema)

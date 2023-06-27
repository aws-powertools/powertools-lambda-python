import logging
import re

import pytest  # noqa: F401

from aws_lambda_powertools.utilities.feature_flags.exceptions import (
    SchemaValidationError,
)
from aws_lambda_powertools.utilities.feature_flags.schema import (
    CONDITION_ACTION,
    CONDITION_KEY,
    CONDITION_VALUE,
    CONDITIONS_KEY,
    FEATURE_DEFAULT_VAL_KEY,
    FEATURE_DEFAULT_VAL_TYPE_KEY,
    RULE_MATCH_VALUE,
    RULES_KEY,
    ConditionsValidator,
    ModuloRangeValues,
    RuleAction,
    RulesValidator,
    SchemaValidator,
    TimeKeys,
    TimeValues,
)

logger = logging.getLogger(__name__)

EMPTY_SCHEMA = {"": ""}


def test_invalid_features_dict():
    validator = SchemaValidator(schema=[])
    with pytest.raises(SchemaValidationError):
        validator.validate()


def test_empty_features_not_fail():
    validator = SchemaValidator(schema={})
    validator.validate()


@pytest.mark.parametrize(
    "schema",
    [
        pytest.param({"my_feature": []}, id="feat_as_list"),
        pytest.param({"my_feature": {}}, id="feat_empty_dict"),
        pytest.param({"my_feature": {FEATURE_DEFAULT_VAL_KEY: "False"}}, id="feat_default_non_bool"),
        pytest.param({"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: "4"}}, id="feat_rules_non_dict"),
        pytest.param("%<>[]{}|^", id="unsafe-rfc3986"),
    ],
)
def test_invalid_feature(schema):
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()


def test_valid_feature_dict():
    # empty rules list
    schema = {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False, RULES_KEY: []}}
    validator = SchemaValidator(schema)
    validator.validate()

    # no rules list at all
    schema = {"my_feature": {FEATURE_DEFAULT_VAL_KEY: False}}
    validator = SchemaValidator(schema)
    validator.validate()


def test_invalid_feature_default_value_is_not_boolean():
    #  feature is boolean but default value is a number, not a boolean
    schema = {"my_feature": {FEATURE_DEFAULT_VAL_KEY: 3, FEATURE_DEFAULT_VAL_TYPE_KEY: True, RULES_KEY: []}}
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()


def test_invalid_rule():
    # rules list is not a list of dict
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: [
                "a",
                "b",
            ],
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # rules RULE_MATCH_VALUE is not bool
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: "False",
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # missing conditions list
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: False,
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # condition list is empty
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {RULE_MATCH_VALUE: False, CONDITIONS_KEY: []},
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # condition is invalid type, not list
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {RULE_MATCH_VALUE: False, CONDITIONS_KEY: {}},
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()


def test_invalid_condition():
    # invalid condition action
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: False,
                    CONDITIONS_KEY: {CONDITION_ACTION: "stuff", CONDITION_KEY: "a", CONDITION_VALUE: "a"},
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # missing condition key and value
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: False,
                    CONDITIONS_KEY: {CONDITION_ACTION: RuleAction.EQUALS.value},
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()

    # invalid condition key type, not string
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: False,
                    CONDITIONS_KEY: {
                        CONDITION_ACTION: RuleAction.EQUALS.value,
                        CONDITION_KEY: 5,
                        CONDITION_VALUE: "a",
                    },
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    with pytest.raises(SchemaValidationError):
        validator.validate()


def test_valid_condition_all_actions():
    schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id equals 645654 and username is a": {
                    RULE_MATCH_VALUE: True,
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
                            CONDITION_ACTION: RuleAction.IN.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: ["a", "b"],
                        },
                        {
                            CONDITION_ACTION: RuleAction.NOT_IN.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: ["c"],
                        },
                        {
                            CONDITION_ACTION: RuleAction.KEY_IN_VALUE.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: ["a", "b"],
                        },
                        {
                            CONDITION_ACTION: RuleAction.KEY_NOT_IN_VALUE.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: ["c"],
                        },
                        {
                            CONDITION_ACTION: RuleAction.VALUE_IN_KEY.value,
                            CONDITION_KEY: "groups",
                            CONDITION_VALUE: "SYSADMIN",
                        },
                        {
                            CONDITION_ACTION: RuleAction.VALUE_NOT_IN_KEY.value,
                            CONDITION_KEY: "groups",
                            CONDITION_VALUE: "GUEST",
                        },
                    ],
                },
            },
        },
    }
    validator = SchemaValidator(schema)
    validator.validate()


def test_validate_condition_invalid_condition_type():
    # GIVEN an invalid condition type of empty dict
    condition = {}

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Feature rule condition must be a dictionary"):
        ConditionsValidator.validate_condition(condition=condition, rule_name="dummy")


def test_validate_condition_invalid_condition_action():
    # GIVEN an invalid condition action of foo
    condition = {"action": "INVALID", "key": "tenant_id", "value": "12345"}

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="'action' value must be either"):
        ConditionsValidator.validate_condition_action(condition=condition, rule_name="dummy")


def test_validate_condition_invalid_condition_key():
    # GIVEN a configuration with a missing "key"
    condition = {"action": RuleAction.EQUALS.value, "value": "12345"}

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="'key' value must be a non empty string"):
        ConditionsValidator.validate_condition_key(condition=condition, rule_name="dummy")


def test_validate_condition_missing_condition_value():
    # GIVEN a configuration with a missing condition value
    condition = {
        "action": RuleAction.EQUALS.value,
        "key": "tenant_id",
    }

    # WHEN calling validate_condition
    with pytest.raises(SchemaValidationError, match="'value' key must not be null"):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_condition_none_condition_value():
    # GIVEN a configuration with a missing condition value
    condition = {
        "action": RuleAction.EQUALS.value,
        "key": "tenant_id",
        "value": None,
    }

    # WHEN calling validate_condition
    with pytest.raises(SchemaValidationError, match="'value' key must not be null"):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_condition_empty_condition_value():
    # GIVEN a configuration with a missing condition value
    condition = {
        "action": RuleAction.EQUALS.value,
        "key": "tenant_id",
        "value": "",
    }

    # WHEN calling validate_condition
    ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_condition_valid_falsy_condition_value():
    # GIVEN a configuration with a missing condition value
    condition = {
        "action": RuleAction.EQUALS.value,
        "key": "tenant_id",
        "value": 0,
    }

    # WHEN calling validate_condition
    ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_rule_invalid_rule_type():
    # GIVEN an invalid rule type of empty list
    # WHEN calling validate_rule
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Feature rule must be a dictionary"):
        RulesValidator.validate_rule(rule=[], rule_name="dummy", feature_name="dummy")


def test_validate_rule_invalid_rule_name():
    # GIVEN a rule name is empty
    # WHEN calling validate_rule_name
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match="Rule name key must have a non-empty string"):
        RulesValidator.validate_rule_name(rule_name="", feature_name="dummy")


def test_validate_rule_invalid_when_match_type_boolean_feature_is_set():
    # GIVEN an invalid rule with non boolean when_match but feature type boolean
    # WHEN calling validate_rule
    # THEN raise SchemaValidationError
    rule_name = "dummy"
    rule = {
        RULE_MATCH_VALUE: ["matched_value"],
        CONDITIONS_KEY: {
            CONDITION_ACTION: RuleAction.EQUALS.value,
            CONDITION_KEY: 5,
            CONDITION_VALUE: "a",
        },
    }
    with pytest.raises(SchemaValidationError, match=f"rule_default_value' key must have be bool, rule={rule_name}"):
        RulesValidator.validate_rule(rule=rule, rule_name=rule_name, feature_name="dummy", boolean_feature=True)


def test_validate_rule_invalid_when_match_type_boolean_feature_is_not_set():
    # GIVEN an invalid rule with non boolean when_match but feature type boolean. validate_rule is called without validate_rule=True # type: ignore # noqa: E501
    # WHEN calling validate_rule
    # THEN raise SchemaValidationError
    rule_name = "dummy"
    rule = {
        RULE_MATCH_VALUE: ["matched_value"],
        CONDITIONS_KEY: {
            CONDITION_ACTION: RuleAction.EQUALS.value,
            CONDITION_KEY: 5,
            CONDITION_VALUE: "a",
        },
    }
    with pytest.raises(SchemaValidationError, match=f"rule_default_value' key must have be bool, rule={rule_name}"):
        RulesValidator.validate_rule(rule=rule, rule_name=rule_name, feature_name="dummy")


def test_validate_rule_boolean_feature_is_set():
    # GIVEN a rule with a boolean when_match and feature type boolean
    # WHEN calling validate_rule
    # THEN schema is validated and declared as valid
    rule_name = "dummy"
    rule = {
        RULE_MATCH_VALUE: True,
        CONDITIONS_KEY: {
            CONDITION_ACTION: RuleAction.EQUALS.value,
            CONDITION_KEY: 5,
            CONDITION_VALUE: "a",
        },
    }
    RulesValidator.validate_rule(rule=rule, rule_name=rule_name, feature_name="dummy", boolean_feature=True)


def test_validate_time_condition_between_time_range_invalid_condition_key():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action,
    # value of between 11:11 to 23:59 and a key of CURRENT_DATETIME
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: "23:59"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'condition with a 'SCHEDULE_BETWEEN_TIME_RANGE' action must have a 'CURRENT_TIME' condition key, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_condition_value():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and invalid value of string
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: "11:00-22:33",
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_TIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_condition_value_no_start_time():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and invalid value
    # dict without START key
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.END.value: "23:59"},
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_TIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_condition_value_no_end_time():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and invalid value
    # dict without END key
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: "23:59"},
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_TIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_condition_value_invalid_start_time_type():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # invalid START value as a number
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: 4, TimeValues.END.value: "23:59"},
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'START' and 'END' must be a non empty string, rule={rule_name}",
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_condition_value_invalid_end_time_type():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # invalid START value as a number
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: 4},
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'START' and 'END' must be a non empty string, rule={rule_name}",
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


@pytest.mark.parametrize(
    "cond_value",
    [
        {TimeValues.START.value: "11-11", TimeValues.END.value: "23:59"},
        {TimeValues.START.value: "24:99", TimeValues.END.value: "23:59"},
    ],
)
def test_validate_time_condition_between_time_range_invalid_condition_value_invalid_start_time_value(cond_value):
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # invalid START value as an invalid time format
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: cond_value,
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"
    match_str = f"'START' and 'END' must be a valid time format, time_format=%H:%M, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


@pytest.mark.parametrize(
    "cond_value",
    [
        {TimeValues.START.value: "10:11", TimeValues.END.value: "11-11"},
        {TimeValues.START.value: "10:11", TimeValues.END.value: "999:59"},
    ],
)
def test_validate_time_condition_between_time_range_invalid_condition_value_invalid_end_time_value(cond_value):
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # invalid END value as an invalid time format
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: cond_value,
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"
    match_str = f"'START' and 'END' must be a valid time format, time_format=%H:%M, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_invalid_timezone():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # invalid timezone
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {
            TimeValues.START.value: "10:11",
            TimeValues.END.value: "10:59",
            TimeValues.TIMEZONE.value: "Europe/Tokyo",
        },
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"
    match_str = f"'TIMEZONE' value must represent a valid IANA timezone, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_time_range_valid_timezone():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_TIME_RANGE action, key CURRENT_TIME and
    # valid timezone
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
        CONDITION_VALUE: {
            TimeValues.START.value: "10:11",
            TimeValues.END.value: "10:59",
            TimeValues.TIMEZONE.value: "Europe/Copenhagen",
        },
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    # WHEN calling validate_condition
    # THEN nothing is raised
    ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_time_condition_between_datetime_range_invalid_condition_key():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action,
    # value of between "2022-10-05T12:15:00Z" to "2022-10-10T12:15:00Z" and a key of CURRENT_TIME
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {
            TimeValues.START.value: "2022-10-05T12:15:00Z",
            TimeValues.END.value: "2022-10-10T12:15:00Z",
        },
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'condition with a 'SCHEDULE_BETWEEN_DATETIME_RANGE' action must have a 'CURRENT_DATETIME' condition key, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)


def test_a_validate_time_condition_between_datetime_range_invalid_condition_value():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and invalid value of string # noqa: E501
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: "11:00-22:33",
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_DATETIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_invalid_condition_value_no_start_time():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and invalid value
    # dict without START key
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.END.value: "2022-10-10T12:15:00Z"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_DATETIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_invalid_condition_value_no_end_time():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and invalid value
    # dict without END key
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: "2022-10-10T12:15:00Z"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"condition with a 'SCHEDULE_BETWEEN_DATETIME_RANGE' action must have a condition value type dictionary with 'START' and 'END' keys, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_invalid_condition_value_invalid_start_time_type():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and
    # invalid START value as a number
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.START.value: 4, TimeValues.END.value: "2022-10-10T12:15:00Z"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'START' and 'END' must be a non empty string, rule={rule_name}",
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_invalid_condition_value_invalid_end_time_type():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and
    # invalid START value as a number
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.END.value: 4, TimeValues.START.value: "2022-10-10T12:15:00Z"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'START' and 'END' must be a non empty string, rule={rule_name}",
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


@pytest.mark.parametrize(
    "cond_value",
    [
        {TimeValues.START.value: "11:11", TimeValues.END.value: "2022-10-10T12:15:00Z"},
        {TimeValues.START.value: "24:99", TimeValues.END.value: "2022-10-10T12:15:00Z"},
        {TimeValues.START.value: "2022-10-10T", TimeValues.END.value: "2022-10-10T12:15:00Z"},
    ],
)
def test_validate_time_condition_between_datetime_range_invalid_condition_value_invalid_start_time_value(cond_value):
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and
    # invalid START value as an invalid time format
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: cond_value,
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"
    match_str = f"'START' and 'END' must be a valid ISO8601 time format, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_invalid_condition_value_invalid_end_time_value():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and
    # invalid END value as an invalid time format
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.END.value: "10:10", TimeValues.START.value: "2022-10-10T12:15:00"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"
    match_str = f"'START' and 'END' must be a valid ISO8601 time format, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match=match_str):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_datetime_range_including_timezone():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DATETIME_RANGE action, key CURRENT_DATETIME and
    # invalid START and END timestamps with timezone information
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,
        CONDITION_VALUE: {TimeValues.END.value: "2022-10-10T11:15:00Z", TimeValues.START.value: "2022-10-10T12:15:00Z"},
        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
    }
    rule_name = "dummy"
    match_str = (
        f"'START' and 'END' must not include timezone information. Set the timezone using the 'TIMEZONE' "
        f"field, rule={rule_name} "
    )
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(SchemaValidationError, match=match_str):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_days_range_invalid_condition_key():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DAYS_OF_WEEK action,
    # value of SUNDAY and a key of CURRENT_TIME
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
        CONDITION_VALUE: {
            TimeValues.DAYS.value: [TimeValues.SUNDAY.value],
        },
        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
    }
    rule_name = "dummy"

    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=f"'condition with a 'SCHEDULE_BETWEEN_DAYS_OF_WEEK' action must have a 'CURRENT_DAY_OF_WEEK' condition key, rule={rule_name}",  # noqa: E501
    ):
        ConditionsValidator.validate_condition_key(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_days_range_invalid_condition_type():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DAYS_OF_WEEK action
    # key CURRENT_DAY_OF_WEEK and invalid value type string
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
        CONDITION_VALUE: TimeValues.SATURDAY.value,
        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
    }
    rule_name = "dummy"
    match_str = f"condition with a CURRENT_DAY_OF_WEEK action must have a condition value dictionary with 'DAYS' and 'TIMEZONE' (optional) keys, rule={rule_name}"  # noqa: E501
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=re.escape(match_str),
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


@pytest.mark.parametrize(
    "cond_value",
    [
        {TimeValues.DAYS.value: [TimeValues.SUNDAY.value, "funday"]},
        {TimeValues.DAYS.value: [TimeValues.SUNDAY, TimeValues.MONDAY.value]},
    ],
)
def test_validate_time_condition_between_days_range_invalid_condition_value(cond_value):
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DAYS_OF_WEEK action
    # key CURRENT_DAY_OF_WEEK and invalid value not day string
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
        CONDITION_VALUE: cond_value,
        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
    }
    rule_name = "dummy"
    match_str = (
        f"condition value DAYS must represent a day of the week in 'TimeValues' enum, rule={rule_name}"  # noqa: E501
    )
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_days_range_invalid_timezone():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DAYS_OF_WEEK action
    # key CURRENT_DAY_OF_WEEK and an invalid timezone
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
        CONDITION_VALUE: {TimeValues.DAYS.value: [TimeValues.SUNDAY.value], TimeValues.TIMEZONE.value: "Europe/Tokyo"},
        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
    }
    rule_name = "dummy"
    match_str = f"'TIMEZONE' value must represent a valid IANA timezone, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_time_condition_between_days_range_valid_timezone():
    # GIVEN a configuration with a SCHEDULE_BETWEEN_DAYS_OF_WEEK action
    # key CURRENT_DAY_OF_WEEK and a valid timezone
    condition = {
        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
        CONDITION_VALUE: {
            TimeValues.DAYS.value: [TimeValues.SUNDAY.value],
            TimeValues.TIMEZONE.value: "Europe/Copenhagen",
        },
        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
    }
    # WHEN calling validate_condition
    # THEN nothing is raised
    ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")


def test_validate_modulo_range_condition_invalid_value():
    # GIVEN a condition with a MODULO_RANGE action and invalid value
    condition = {CONDITION_ACTION: RuleAction.MODULO_RANGE.value, CONDITION_VALUE: "invalid", CONDITION_KEY: "a"}
    rule_name = "dummy"
    match_str = f"condition with a 'MODULO_RANGE' action must have a condition value type dictionary with 'BASE', 'START' and 'END' keys, rule={rule_name}"  # noqa: E501
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_missing_parameter():
    # GIVEN a condition with a MODULO_RANGE action and missing required parameter
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: 100,
            ModuloRangeValues.START.value: 0,
        },
        CONDITION_KEY: "a",
    }
    rule_name = "dummy"
    match_str = f"condition with a 'MODULO_RANGE' action must have a condition value type dictionary with 'BASE', 'START' and 'END' keys, rule={rule_name}"  # noqa: E501
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_non_integer_parameters():
    # GIVEN a condition with a MODULO_RANGE action and non integer parameters
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: "100",
            ModuloRangeValues.START.value: "0",
            ModuloRangeValues.END.value: "49",
        },
        CONDITION_KEY: "a",
    }
    rule_name = "dummy"
    match_str = f"'BASE', 'START' and 'END' must be integers, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_start_greater_than_end():
    # GIVEN a condition with a MODULO_RANGE action and invalid parameters
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: 100,
            ModuloRangeValues.START.value: 50,
            ModuloRangeValues.END.value: 49,
        },
        CONDITION_KEY: "a",
    }
    rule_name = "dummy"
    match_str = f"condition with 'MODULO_RANGE' action must satisfy 0 <= START <= END <= BASE-1, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_start_less_than_zero():
    # GIVEN a condition with a MODULO_RANGE action and invalid parameters
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: 100,
            ModuloRangeValues.START.value: -10,
            ModuloRangeValues.END.value: 49,
        },
        CONDITION_KEY: "a",
    }
    rule_name = "dummy"
    match_str = f"condition with 'MODULO_RANGE' action must satisfy 0 <= START <= END <= BASE-1, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_end_greater_than_equal_to_base():
    # GIVEN a condition with a MODULO_RANGE action and invalid parameters
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: 100,
            ModuloRangeValues.START.value: 0,
            ModuloRangeValues.END.value: 100,
        },
        CONDITION_KEY: "a",
    }
    rule_name = "dummy"
    match_str = f"condition with 'MODULO_RANGE' action must satisfy 0 <= START <= END <= BASE-1, rule={rule_name}"
    # WHEN calling validate_condition
    # THEN raise SchemaValidationError
    with pytest.raises(
        SchemaValidationError,
        match=match_str,
    ):
        ConditionsValidator.validate_condition_value(condition=condition, rule_name=rule_name)


def test_validate_modulo_range_condition_valid():
    # GIVEN a condition with a MODULO_RANGE action and valid parameters
    condition = {
        CONDITION_ACTION: RuleAction.MODULO_RANGE.value,
        CONDITION_VALUE: {
            ModuloRangeValues.BASE.value: 100,
            ModuloRangeValues.START.value: 0,
            ModuloRangeValues.END.value: 19,
        },
        CONDITION_KEY: "a",
    }
    # WHEN calling validate_condition
    # THEN nothing is raised
    ConditionsValidator.validate_condition_value(condition=condition, rule_name="dummy")

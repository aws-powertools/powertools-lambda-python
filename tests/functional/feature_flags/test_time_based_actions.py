import datetime
from typing import Dict, Optional

import pytest
from botocore.config import Config
from dateutil import tz

from aws_lambda_powertools.utilities.feature_flags.appconfig import AppConfigStore
from aws_lambda_powertools.utilities.feature_flags.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.feature_flags.schema import (
    CONDITION_ACTION,
    CONDITION_KEY,
    CONDITION_VALUE,
    CONDITIONS_KEY,
    FEATURE_DEFAULT_VAL_KEY,
    RULE_MATCH_VALUE,
    RULES_KEY,
    RuleAction,
    TimeKeys,
    TimeValues,
)


@pytest.fixture(scope="module")
def config():
    return Config(region_name="us-east-1")


def init_feature_flags(
    mocker, mock_schema: Dict, config: Config, envelope: str = "", jmespath_options: Optional[Dict] = None
) -> FeatureFlags:
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.return_value = mock_schema

    app_conf_fetcher = AppConfigStore(
        environment="test_env",
        application="test_app",
        name="test_conf_name",
        max_age=600,
        sdk_config=config,
        envelope=envelope,
        jmespath_options=jmespath_options,
    )
    feature_flags: FeatureFlags = FeatureFlags(store=app_conf_fetcher)
    return feature_flags


def init_fetcher_side_effect(mocker, config: Config, side_effect) -> AppConfigStore:
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.side_effect = side_effect
    return AppConfigStore(
        environment="env",
        application="application",
        name="conf",
        max_age=1,
        sdk_config=config,
    )


def mock_current_utc_time(
    mocker,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    msec: int,
) -> None:
    mocked_time = mocker.patch("aws_lambda_powertools.utilities.feature_flags.time_conditions._get_utc_time_now")
    mocked_time.return_value = datetime.datetime(year, month, day, hour, minute, second, msec, tz.gettz("UTC"))


def test_time_based_utc_in_between_time_range_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC 11:11-23:59": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC.value,
                            CONDITION_VALUE: {TimeValues.START_TIME.value: "11:11", TimeValues.END_TIME.value: "23:59"},
                        },
                    ],
                }
            },
        }
    }
    mock_current_utc_time(mocker, 2022, 2, 15, 11, 12, 0, 0)  # will rule match

    # mock time for rule match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )

    assert toggle == expected_value


def test_time_based_utc_in_between_time_range_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC 11:11-23:59": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC.value,
                            CONDITION_VALUE: {TimeValues.START_TIME.value: "11:11", TimeValues.END_TIME.value: "23:59"},
                        },
                    ],
                }
            },
        }
    }
    mock_current_utc_time(mocker, 2022, 2, 15, 7, 12, 0, 0)  # no rule match 7:12 am

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )

    assert toggle == expected_value


def test_time_based_utc_in_between_full_time_range_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                            CONDITION_VALUE: {
                                TimeValues.START_TIME.value: "2022-10-05T12:15:00Z",
                                TimeValues.END_TIME.value: "2022-10-10T12:15:00Z",
                            },
                        },
                    ],
                }
            },
        }
    }

    mock_current_utc_time(mocker, 2022, 10, 7, 10, 0, 0, 0)  # will rule match

    # mock time for rule match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_utc_in_between_full_time_range_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                            CONDITION_VALUE: {
                                TimeValues.START_TIME.value: "2022-10-05T12:15:00Z",
                                TimeValues.END_TIME.value: "2022-10-10T12:15:00Z",
                            },
                        },
                    ],
                }
            },
        }
    }

    mock_current_utc_time(mocker, 2022, 9, 7, 10, 0, 0, 0)  # will not rule match

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_multiple_conditions_utc_in_between_time_range_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC 09:00-17:00 and username is ran": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC,
                            CONDITION_VALUE: {TimeValues.START_TIME: "09:00", TimeValues.END_TIME: "17:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: "ran",
                        },
                    ],
                }
            },
        }
    }

    mock_current_utc_time(mocker, 2022, 10, 7, 10, 0, 0, 0)  # will rule match

    # mock time for rule match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"username": "ran"},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_multiple_conditions_utc_in_between_time_range_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "lambda time is between UTC 09:00-17:00 and username is ran": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC,
                            CONDITION_VALUE: {TimeValues.START_TIME: "09:00", TimeValues.END_TIME: "17:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: "ran",
                        },
                    ],
                }
            },
        }
    }

    mock_current_utc_time(mocker, 2022, 10, 7, 7, 0, 0, 0)  # will cause no rule match, 7:00

    # mock time for rule match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"username": "ran"},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_utc_days_range_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match only monday through friday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,  # similar to "IN" actions
                            CONDITION_VALUE: [
                                TimeValues.MONDAY,
                                TimeValues.TUESDAY,
                                TimeValues.WEDNESDAY,
                                TimeValues.THURSDAY,
                                TimeValues.FRIDAY,
                            ],
                        },
                    ],
                }
            },
        }
    }
    # mock time for rule match
    mock_current_utc_time(mocker, 2022, 11, 18, 10, 0, 0, 0)  # friday
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_utc_days_range_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match only monday through friday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,  # similar to "IN" actions
                            CONDITION_VALUE: [
                                TimeValues.MONDAY,
                                TimeValues.TUESDAY,
                                TimeValues.WEDNESDAY,
                                TimeValues.THURSDAY,
                                TimeValues.FRIDAY,
                            ],
                        },
                    ],
                }
            },
        }
    }
    mock_current_utc_time(mocker, 2022, 11, 20, 10, 0, 0, 0)  # sunday, no match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_utc_only_weekend_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match only on weekend": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,  # similar to "IN" actions
                            CONDITION_VALUE: [TimeValues.SATURDAY, TimeValues.SUNDAY],
                        },
                    ],
                }
            },
        }
    }
    # mock time for rule match
    mock_current_utc_time(mocker, 2022, 11, 19, 10, 0, 0, 0)  # saturday
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_utc_only_weekend_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match only on weekend": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,  # similar to "IN" actions
                            CONDITION_VALUE: [TimeValues.SATURDAY, TimeValues.SUNDAY],
                        },
                    ],
                }
            },
        }
    }
    mock_current_utc_time(mocker, 2022, 11, 18, 10, 0, 0, 0)  # friday, no match
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_rule_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC,
                            CONDITION_VALUE: {TimeValues.START_TIME: "11:00", TimeValues.END_TIME: "23:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,
                            CONDITION_VALUE: [TimeValues.MONDAY, TimeValues.THURSDAY],
                        },
                    ],
                }
            },
        }
    }
    # mock time for rule match
    mock_current_utc_time(mocker, 2022, 11, 17, 16, 0, 0, 0)  # thursday 16:00
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_no_rule_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.TIME_RANGE.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_HOUR_UTC,
                            CONDITION_VALUE: {TimeValues.START_TIME: "11:00", TimeValues.END_TIME: "23:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.TIME_SELECTED_DAYS.value,  # this condition matches
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC,
                            CONDITION_VALUE: [TimeValues.MONDAY, TimeValues.THURSDAY],
                        },
                    ],
                }
            },
        }
    }
    # first condition fail, second match
    mock_current_utc_time(mocker, 2022, 11, 17, 9, 0, 0, 0)  # thursday 9:00
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value

    # second condition fail, first match
    mock_current_utc_time(mocker, 2022, 11, 18, 13, 0, 0, 0)  # friday 16:00
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value

    # both conditions fail
    mock_current_utc_time(mocker, 2022, 11, 18, 9, 0, 0, 0)  # friday 9:00
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value

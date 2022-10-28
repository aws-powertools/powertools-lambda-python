from typing import Dict, Optional

import pytest
from botocore.config import Config

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
    # mock time for rule match
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
    # mock time for rule match
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
                            CONDITION_KEY: "tenant",
                            CONDITION_VALUE: {"username": "ran"},
                        },
                    ],
                }
            },
        }
    }
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
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={},
        default=False,
    )
    assert toggle == expected_value

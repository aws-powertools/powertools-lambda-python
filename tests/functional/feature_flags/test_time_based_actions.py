import datetime
from typing import Any, Dict, Optional, Tuple

from botocore.config import Config
from dateutil.tz import gettz

from aws_lambda_powertools.shared.types import JSONType
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


def evaluate_mocked_schema(
    mocker,
    rules: Dict[str, Any],
    mocked_time: Tuple[int, int, int, int, int, int, datetime.tzinfo],  # year, month, day, hour, minute, second
    context: Optional[Dict[str, Any]] = None,
) -> JSONType:
    """
    This helper does the following:
    1. mocks the current time
    2. mocks the feature flag payload returned from AppConfig
    3. evaluates the rules and return True for a rule match, otherwise a False
    """

    # Mock the current time
    year, month, day, hour, minute, second, timezone = mocked_time
    time = mocker.patch("aws_lambda_powertools.utilities.feature_flags.time_conditions._get_now_from_timezone")
    time.return_value = datetime.datetime(
        year=year, month=month, day=day, hour=hour, minute=minute, second=second, microsecond=0, tzinfo=timezone
    )

    # Mock the returned data from AppConfig
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.return_value = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: rules,
        }
    }

    # Create a dummy AppConfigStore that returns our mocked FeatureFlag
    app_conf_fetcher = AppConfigStore(
        environment="test_env",
        application="test_app",
        name="test_conf_name",
        max_age=600,
        sdk_config=Config(region_name="us-east-1"),
    )
    feature_flags: FeatureFlags = FeatureFlags(store=app_conf_fetcher)

    # Evaluate our feature flag
    context = {} if context is None else context
    return feature_flags.evaluate(
        name="my_feature",
        context=context,
        default=False,
    )


def test_time_based_utc_in_between_time_range_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: "23:59"},
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 11, 12, 0, datetime.timezone.utc),
    )


def test_time_based_utc_in_between_time_range_no_rule_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: "23:59"},
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 7, 12, 0, datetime.timezone.utc),  # no rule match 7:12 am
    )


def test_time_based_utc_in_between_time_range_full_hour_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 20:00-23:00": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "20:00", TimeValues.END.value: "23:00"},
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 21, 12, 0, datetime.timezone.utc),  # rule match 21:12
    )


def test_time_based_utc_in_between_time_range_between_days_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 23:00-04:00": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "23:00", TimeValues.END.value: "04:00"},
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 2, 3, 0, datetime.timezone.utc),  # rule match 2:03 am
    )


def test_time_based_utc_in_between_time_range_between_days_rule_no_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 23:00-04:00": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "23:00", TimeValues.END.value: "04:00"},
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 5, 0, 0, datetime.timezone.utc),  # rule no match 5:00 am
    )


def test_time_based_between_time_range_rule_timezone_match(mocker):
    timezone_name = "Europe/Copenhagen"

    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59, Copenhagen Time": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "11:11",
                            TimeValues.END.value: "23:59",
                            TimeValues.TIMEZONE.value: timezone_name,
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 11, 11, 0, gettz(timezone_name)),  # rule match 11:11 am, Europe/Copenhagen
    )


def test_time_based_between_time_range_rule_timezone_no_match(mocker):
    timezone_name = "Europe/Copenhagen"

    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59, Copenhagen Time": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "11:11",
                            TimeValues.END.value: "23:59",
                            TimeValues.TIMEZONE.value: timezone_name,
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 2, 15, 10, 11, 0, gettz(timezone_name)),  # no rule match 10:11 am, Europe/Copenhagen
    )


def test_time_based_utc_in_between_full_time_range_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,  # condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "2022-10-05T12:15:00",
                            TimeValues.END.value: "2022-10-10T12:15:00",
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 10, 7, 10, 0, 0, datetime.timezone.utc),  # will match rule
    )


def test_time_based_utc_in_between_full_time_range_no_rule_match(mocker):
    timezone_name = "Europe/Copenhagen"

    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,  # condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "2022-10-05T12:15:00",
                            TimeValues.END.value: "2022-10-10T12:15:00",
                            TimeValues.TIMEZONE.value: timezone_name,
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 9, 7, 10, 0, 0, gettz(timezone_name)),  # will not rule match
    )


def test_time_based_utc_in_between_full_time_range_timezone_no_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,  # condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DATETIME.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "2022-10-05T12:15:00",
                            TimeValues.END.value: "2022-10-10T12:15:00",
                            TimeValues.TIMEZONE.value: "Europe/Copenhagen",
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 10, 10, 12, 15, 0, gettz("America/New_York")),  # will not rule match, it's too late
    )


def test_time_based_multiple_conditions_utc_in_between_time_range_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 09:00-17:00 and username is ran": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "09:00", TimeValues.END.value: "17:00"},
                    },
                    {
                        CONDITION_ACTION: RuleAction.EQUALS.value,
                        CONDITION_KEY: "username",
                        CONDITION_VALUE: "ran",
                    },
                ],
            }
        },
        mocked_time=(2022, 10, 7, 10, 0, 0, datetime.timezone.utc),  # will rule match
        context={"username": "ran"},
    )


def test_time_based_multiple_conditions_utc_in_between_time_range_no_rule_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 09:00-17:00 and username is ran": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "09:00", TimeValues.END.value: "17:00"},
                    },
                    {
                        CONDITION_ACTION: RuleAction.EQUALS.value,
                        CONDITION_KEY: "username",
                        CONDITION_VALUE: "ran",
                    },
                ],
            }
        },
        mocked_time=(2022, 10, 7, 7, 0, 0, datetime.timezone.utc),  # will cause no rule match, 7:00
        context={"username": "ran"},
    )


def test_time_based_utc_days_range_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only monday through friday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [
                                TimeValues.MONDAY.value,
                                TimeValues.TUESDAY.value,
                                TimeValues.WEDNESDAY.value,
                                TimeValues.THURSDAY.value,
                                TimeValues.FRIDAY.value,
                            ],
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 18, 10, 0, 0, datetime.timezone.utc),  # friday
    )


def test_time_based_utc_days_range_no_rule_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only monday through friday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [
                                TimeValues.MONDAY.value,
                                TimeValues.TUESDAY.value,
                                TimeValues.WEDNESDAY.value,
                                TimeValues.THURSDAY.value,
                                TimeValues.FRIDAY.value,
                            ],
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 20, 10, 0, 0, datetime.timezone.utc),  # sunday, no match
    )


def test_time_based_utc_only_weekend_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 19, 10, 0, 0, datetime.timezone.utc),  # saturday
    )


def test_time_based_utc_only_weekend_with_timezone_rule_match(mocker):
    timezone_name = "Europe/Copenhagen"

    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                            TimeValues.TIMEZONE.value: timezone_name,
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 19, 10, 0, 0, gettz(timezone_name)),  # saturday
    )


def test_time_based_utc_only_weekend_with_timezone_rule_no_match(mocker):
    timezone_name = "Europe/Copenhagen"

    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                            TimeValues.TIMEZONE.value: timezone_name,
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 21, 0, 0, 0, gettz("Europe/Copenhagen")),  # monday, 00:00
    )


def test_time_based_utc_only_weekend_no_rule_match(mocker):
    assert not evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,  # similar to "IN" actions
                        CONDITION_VALUE: {
                            TimeValues.DAYS.value: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                        },
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 18, 10, 0, 0, datetime.timezone.utc),  # friday, no match
    )


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_rule_match(mocker):
    assert evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:00", TimeValues.END.value: "23:00"},
                    },
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
                        CONDITION_VALUE: {TimeValues.DAYS.value: [TimeValues.MONDAY.value, TimeValues.THURSDAY.value]},
                    },
                ],
            }
        },
        mocked_time=(2022, 11, 17, 16, 0, 0, datetime.timezone.utc),  # thursday 16:00
    )


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_no_rule_match(mocker):
    def evaluate(mocked_time: Tuple[int, int, int, int, int, int, datetime.tzinfo]):
        evaluate_mocked_schema(
            mocker=mocker,
            rules={
                "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
                            CONDITION_KEY: TimeKeys.CURRENT_TIME.value,
                            CONDITION_VALUE: {TimeValues.START.value: "11:00", TimeValues.END.value: "23:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_OF_WEEK.value,
                            CONDITION_VALUE: {
                                TimeValues.DAYS.value: [TimeValues.MONDAY.value, TimeValues.THURSDAY.value]
                            },
                        },
                    ],
                }
            },
            mocked_time=mocked_time,
        )

    assert not evaluate(mocked_time=(2022, 11, 17, 9, 0, 0, datetime.timezone.utc))  # thursday 9:00
    assert not evaluate(mocked_time=(2022, 11, 18, 13, 0, 0, datetime.timezone.utc))  # friday 16:00
    assert not evaluate(mocked_time=(2022, 11, 18, 9, 0, 0, datetime.timezone.utc))  # friday 9:00

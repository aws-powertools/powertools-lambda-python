import datetime
from typing import Optional

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


def evaluate_mocked_schema(
    mocker,
    rules: dict,
    expected_value: bool,
    mocked_time: tuple[int, int, int, int, int, int],
    context: Optional[dict] = None,
):
    """
    This helper does the following:
    1. mocks the current time
    2. mocks the feature flag payload returend from AppConfig
    3. evaluates the rules against the expected value
    """

    # Mock the current time
    year, month, day, hour, minute, second = mocked_time

    mocked_time = mocker.patch("aws_lambda_powertools.utilities.feature_flags.time_conditions._get_utc_time_now")
    mocked_time.return_value = datetime.datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=0,
        tzinfo=datetime.timezone.utc,
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
    toggle = feature_flags.evaluate(
        name="my_feature",
        context=context,
        default=False,
    )

    # Assert result against expected value
    assert toggle == expected_value


def test_time_based_utc_in_between_time_range_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: "23:59"},
                    },
                ],
            }
        },
        expected_value=True,
        mocked_time=(2022, 2, 15, 11, 12, 0),
    )


def test_time_based_utc_in_between_time_range_no_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 11:11-23:59": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:11", TimeValues.END.value: "23:59"},
                    },
                ],
            }
        },
        expected_value=False,
        mocked_time=(2022, 2, 15, 7, 12, 0),  # no rule match 7:12 am
    )


def test_time_based_utc_in_between_full_time_range_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,  # condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DATETIME_UTC.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "2022-10-05T12:15:00Z",
                            TimeValues.END.value: "2022-10-10T12:15:00Z",
                        },
                    },
                ],
            }
        },
        expected_value=True,
        mocked_time=(2022, 10, 7, 10, 0, 0),  # will match rule
    )


def test_time_based_utc_in_between_full_time_range_no_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC october 5th 2022 12:14:32PM to october 10th 2022 12:15:00 PM": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DATETIME_RANGE.value,  # condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DATETIME_UTC.value,
                        CONDITION_VALUE: {
                            TimeValues.START.value: "2022-10-05T12:15:00Z",
                            TimeValues.END.value: "2022-10-10T12:15:00Z",
                        },
                    },
                ],
            }
        },
        expected_value=False,
        mocked_time=(2022, 9, 7, 10, 0, 0),  # will not rule match
    )


def test_time_based_multiple_conditions_utc_in_between_time_range_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 09:00-17:00 and username is ran": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
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
        expected_value=True,
        mocked_time=(2022, 10, 7, 10, 0, 0),  # will rule match
        context={"username": "ran"},
    )


def test_time_based_multiple_conditions_utc_in_between_time_range_no_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "lambda time is between UTC 09:00-17:00 and username is ran": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
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
        expected_value=False,
        mocked_time=(2022, 10, 7, 7, 0, 0),  # will cause no rule match, 7:00
        context={"username": "ran"},
    )


def test_time_based_utc_days_range_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only monday through friday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,  # similar to "IN" actions
                        CONDITION_VALUE: [
                            TimeValues.MONDAY.value,
                            TimeValues.TUESDAY.value,
                            TimeValues.WEDNESDAY.value,
                            TimeValues.THURSDAY.value,
                            TimeValues.FRIDAY.value,
                        ],
                    },
                ],
            }
        },
        expected_value=True,
        mocked_time=(2022, 11, 18, 10, 0, 0),  # friday
    )


def test_time_based_utc_days_range_no_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only monday through friday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,  # similar to "IN" actions
                        CONDITION_VALUE: [
                            TimeValues.MONDAY.value,
                            TimeValues.TUESDAY.value,
                            TimeValues.WEDNESDAY.value,
                            TimeValues.THURSDAY.value,
                            TimeValues.FRIDAY.value,
                        ],
                    },
                ],
            }
        },
        expected_value=False,
        mocked_time=(2022, 11, 20, 10, 0, 0),  # sunday, no match
    )


def test_time_based_utc_only_weekend_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,  # similar to "IN" actions
                        CONDITION_VALUE: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                    },
                ],
            }
        },
        expected_value=True,
        mocked_time=(2022, 11, 19, 10, 0, 0),  # saturday
    )


def test_time_based_utc_only_weekend_no_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match only on weekend": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,  # similar to "IN" actions
                        CONDITION_VALUE: [TimeValues.SATURDAY.value, TimeValues.SUNDAY.value],
                    },
                ],
            }
        },
        expected_value=False,
        mocked_time=(2022, 11, 18, 10, 0, 0),  # friday, no match
    )


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_rule_match(mocker):
    evaluate_mocked_schema(
        mocker=mocker,
        rules={
            "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                RULE_MATCH_VALUE: True,
                CONDITIONS_KEY: [
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                        CONDITION_VALUE: {TimeValues.START.value: "11:00", TimeValues.END.value: "23:00"},
                    },
                    {
                        CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,  # this condition matches
                        CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,
                        CONDITION_VALUE: [TimeValues.MONDAY.value, TimeValues.THURSDAY.value],
                    },
                ],
            }
        },
        expected_value=True,
        mocked_time=(2022, 11, 17, 16, 0, 0),  # thursday 16:00
    )


def test_time_based_multiple_conditions_utc_days_range_and_certain_hours_no_rule_match(mocker):
    def evaluate(mocked_time: tuple[int, int, int, int, int, int], expected_value: bool):
        evaluate_mocked_schema(
            mocker=mocker,
            rules={
                "match when lambda time is between UTC 11:00-23:00 and day is either monday or thursday": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_TIME_RANGE.value,
                            CONDITION_KEY: TimeKeys.CURRENT_TIME_UTC.value,
                            CONDITION_VALUE: {TimeValues.START.value: "11:00", TimeValues.END.value: "23:00"},
                        },
                        {
                            CONDITION_ACTION: RuleAction.SCHEDULE_BETWEEN_DAYS_OF_WEEK.value,
                            CONDITION_KEY: TimeKeys.CURRENT_DAY_UTC.value,
                            CONDITION_VALUE: [TimeValues.MONDAY.value, TimeValues.THURSDAY.value],
                        },
                    ],
                }
            },
            expected_value=expected_value,
            mocked_time=mocked_time,
        )

    evaluate(mocked_time=(2022, 11, 17, 9, 0, 0), expected_value=False)  # thursday 9:00
    evaluate(mocked_time=(2022, 11, 18, 13, 0, 0), expected_value=False)  # friday 16:00
    evaluate(mocked_time=(2022, 11, 18, 9, 0, 0), expected_value=False)  # friday 9:00

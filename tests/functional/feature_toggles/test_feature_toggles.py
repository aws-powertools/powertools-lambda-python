from typing import Dict, List

import pytest
from botocore.config import Config

from aws_lambda_powertools.utilities.feature_toggles import ConfigurationError, schema
from aws_lambda_powertools.utilities.feature_toggles.appconfig import AppConfigStore
from aws_lambda_powertools.utilities.feature_toggles.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.feature_toggles.schema import ACTION
from aws_lambda_powertools.utilities.parameters import GetParameterError


@pytest.fixture(scope="module")
def config():
    return Config(region_name="us-east-1")


def init_configuration_store(mocker, mock_schema: Dict, config: Config) -> FeatureFlags:
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.return_value = mock_schema

    app_conf_fetcher = AppConfigStore(
        environment="test_env",
        application="test_app",
        name="test_conf_name",
        cache_seconds=600,
        config=config,
    )
    conf_store: FeatureFlags = FeatureFlags(store=app_conf_fetcher)
    return conf_store


def init_fetcher_side_effect(mocker, config: Config, side_effect) -> AppConfigStore:
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.side_effect = side_effect
    return AppConfigStore(
        environment="env",
        application="application",
        name="conf",
        cache_seconds=1,
        config=config,
    )


# this test checks that we get correct value of feature that exists in the schema.
# we also don't send an empty context dict in this case
def test_toggles_rule_does_not_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "rule_name": "tenant id equals 345345435",
                        "value_when_applies": False,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "345345435",
                            }
                        ],
                    },
                ],
            }
        },
    }

    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={}, default=False)
    assert toggle == expected_value


# this test checks that if you try to get a feature that doesn't exist in the schema,
# you get the default value of False that was sent to the evaluate API
def test_toggles_no_conditions_feature_does_not_exist(mocker, config):
    expected_value = False
    mocked_app_config_schema = {"features": {"my_fake_feature": {"feature_default_value": True}}}

    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={}, default=expected_value)
    assert toggle == expected_value


# check that feature match works when they are no rules and we send context.
# default value is False but the feature has a True default_value.
def test_toggles_no_rules(mocker, config):
    expected_value = True
    mocked_app_config_schema = {"features": {"my_feature": {"feature_default_value": expected_value}}}
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature
def test_toggles_conditions_no_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "rule_name": "tenant id equals 345345435",
                        "value_when_applies": False,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "345345435",
                            }
                        ],
                    },
                ],
            }
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


# check that a rule can match when it has multiple conditions, see rule name for further explanation
def test_toggles_conditions_rule_match_equal_multiple_conditions(mocker, config):
    expected_value = False
    tenant_id_val = "6"
    username_val = "a"
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": True,
                "rules": [
                    {
                        "rule_name": "tenant id equals 6 and username is a",
                        "value_when_applies": expected_value,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,  # this rule will match, it has multiple conditions
                                "key": "tenant_id",
                                "value": tenant_id_val,
                            },
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "username",
                                "value": username_val,
                            },
                        ],
                    },
                ],
            }
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(
        feature_name="my_feature",
        context={
            "tenant_id": tenant_id_val,
            "username": username_val,
        },
        default=True,
    )
    assert toggle == expected_value


# check a case when rule doesn't match and it has multiple conditions,
# different tenant id causes the rule to not match.
# default value of the feature in this case is True
def test_toggles_conditions_no_rule_match_equal_multiple_conditions(mocker, config):
    expected_val = True
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_val,
                "rules": [
                    {
                        "rule_name": "tenant id equals 645654 and username is a",  # rule will not match
                        "value_when_applies": False,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "645654",
                            },
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "username",
                                "value": "a",
                            },
                        ],
                    },
                ],
            }
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_val


# check rule match for multiple of action types
def test_toggles_conditions_rule_match_multiple_actions_multiple_rules_multiple_conditions(mocker, config):
    expected_value_first_check = True
    expected_value_second_check = False
    expected_value_third_check = False
    expected_value_fourth_case = False
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value_third_check,
                "rules": [
                    {
                        "rule_name": "tenant id equals 6 and username startswith a",
                        "value_when_applies": expected_value_first_check,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "6",
                            },
                            {
                                "action": ACTION.STARTSWITH.value,
                                "key": "username",
                                "value": "a",
                            },
                        ],
                    },
                    {
                        "rule_name": "tenant id equals 4446 and username startswith a and endswith z",
                        "value_when_applies": expected_value_second_check,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "4446",
                            },
                            {
                                "action": ACTION.STARTSWITH.value,
                                "key": "username",
                                "value": "a",
                            },
                            {
                                "action": ACTION.ENDSWITH.value,
                                "key": "username",
                                "value": "z",
                            },
                        ],
                    },
                ],
            }
        },
    }

    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    # match first rule
    toggle = conf_store.evaluate(
        feature_name="my_feature", context={"tenant_id": "6", "username": "abcd"}, default=False
    )
    assert toggle == expected_value_first_check
    # match second rule
    toggle = conf_store.evaluate(
        feature_name="my_feature", context={"tenant_id": "4446", "username": "az"}, default=False
    )
    assert toggle == expected_value_second_check
    # match no rule
    toggle = conf_store.evaluate(
        feature_name="my_feature", context={"tenant_id": "11114446", "username": "ab"}, default=False
    )
    assert toggle == expected_value_third_check
    # feature doesn't exist
    toggle = conf_store.evaluate(
        feature_name="my_fake_feature",
        context={"tenant_id": "11114446", "username": "ab"},
        default=expected_value_fourth_case,
    )
    assert toggle == expected_value_fourth_case


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature
def test_toggles_match_rule_with_contains_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": False,
                "rules": [
                    {
                        "rule_name": "tenant id is contained in [6,2] ",
                        "value_when_applies": expected_value,
                        "conditions": [
                            {
                                "action": ACTION.CONTAINS.value,
                                "key": "tenant_id",
                                "value": ["6", "2"],
                            }
                        ],
                    },
                ],
            }
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_toggles_no_match_rule_with_contains_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "rule_name": "tenant id is contained in [6,2] ",
                        "value_when_applies": True,
                        "conditions": [
                            {
                                "action": ACTION.CONTAINS.value,
                                "key": "tenant_id",
                                "value": ["8", "2"],
                            }
                        ],
                    },
                ],
            }
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.evaluate(feature_name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_multiple_features_enabled(mocker, config):
    expected_value = ["my_feature", "my_feature2"]
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": False,
                "rules": [
                    {
                        "rule_name": "tenant id is contained in [6,2] ",
                        "value_when_applies": True,
                        "conditions": [
                            {
                                "action": ACTION.CONTAINS.value,
                                "key": "tenant_id",
                                "value": ["6", "2"],
                            }
                        ],
                    },
                ],
            },
            "my_feature2": {
                "feature_default_value": True,
            },
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    enabled_list: List[str] = conf_store.get_all_enabled_feature_toggles(context={"tenant_id": "6", "username": "a"})
    assert enabled_list == expected_value


def test_multiple_features_only_some_enabled(mocker, config):
    expected_value = ["my_feature", "my_feature2", "my_feature4"]
    mocked_app_config_schema = {
        "features": {
            "my_feature": {  # rule will match here, feature is enabled due to rule match
                "feature_default_value": False,
                "rules": [
                    {
                        "rule_name": "tenant id is contained in [6,2] ",
                        "value_when_applies": True,
                        "conditions": [
                            {
                                "action": ACTION.CONTAINS.value,
                                "key": "tenant_id",
                                "value": ["6", "2"],
                            }
                        ],
                    },
                ],
            },
            "my_feature2": {
                "feature_default_value": True,
            },
            "my_feature3": {
                "feature_default_value": False,
            },
            "my_feature4": {  # rule will not match here, feature is enabled by default
                "feature_default_value": True,
                "rules": [
                    {
                        "rule_name": "tenant id equals 7",
                        "value_when_applies": False,
                        "conditions": [
                            {
                                "action": ACTION.EQUALS.value,
                                "key": "tenant_id",
                                "value": "7",
                            }
                        ],
                    },
                ],
            },
        },
    }
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    enabled_list: List[str] = conf_store.get_all_enabled_feature_toggles(context={"tenant_id": "6", "username": "a"})
    assert enabled_list == expected_value


def test_get_feature_toggle_handles_error(mocker, config):
    # GIVEN a schema fetch that raises a ConfigurationError
    schema_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())
    conf_store = FeatureFlags(schema_fetcher)

    # WHEN calling evaluate
    toggle = conf_store.evaluate(feature_name="Foo", default=False)

    # THEN handle the error and return the default
    assert toggle is False


def test_get_all_enabled_feature_toggles_handles_error(mocker, config):
    # GIVEN a schema fetch that raises a ConfigurationError
    schema_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())
    conf_store = FeatureFlags(schema_fetcher)

    # WHEN calling get_all_enabled_feature_toggles
    toggles = conf_store.get_all_enabled_feature_toggles(context=None)

    # THEN handle the error and return an empty list
    assert toggles == []


def test_app_config_get_parameter_err(mocker, config):
    # GIVEN an appconfig with a missing config
    app_conf_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())

    # WHEN calling get_json_configuration
    with pytest.raises(ConfigurationError) as err:
        app_conf_fetcher.get_json_configuration()

    # THEN raise ConfigurationError error
    assert "AWS AppConfig configuration" in str(err.value)


def test_match_by_action_no_matching_action(mocker, config):
    # GIVEN an unsupported action
    conf_store = init_configuration_store(mocker, {}, config)
    # WHEN calling _match_by_action
    result = conf_store._match_by_action("Foo", None, "foo")
    # THEN default to False
    assert result is False


def test_match_by_action_attribute_error(mocker, config):
    # GIVEN a startswith action and 2 integer
    conf_store = init_configuration_store(mocker, {}, config)
    # WHEN calling _match_by_action
    result = conf_store._match_by_action(ACTION.STARTSWITH.value, 1, 100)
    # THEN swallow the AttributeError and return False
    assert result is False


def test_is_rule_matched_no_matches(mocker, config):
    # GIVEN an empty list of conditions
    rule = {schema.CONDITIONS_KEY: []}
    rules_context = {}
    conf_store = init_configuration_store(mocker, {}, config)

    # WHEN calling _is_rule_matched
    result = conf_store._is_rule_matched("feature_name", rule, rules_context)

    # THEN return False
    assert result is False

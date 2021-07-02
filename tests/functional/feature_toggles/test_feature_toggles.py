from typing import Dict

import pytest  # noqa: F401
from botocore.config import Config

from aws_lambda_powertools.utilities.feature_toggles.configuration_store import ACTION, ConfigurationStore


@pytest.fixture(scope="module")
def config():
    return Config(region_name="us-east-1")


def init_configuration_store(mocker, mock_schema: Dict, config: Config) -> ConfigurationStore:
    mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.parameters.AppConfigProvider.get")
    mocked_get_conf.return_value = mock_schema
    conf_store: ConfigurationStore = ConfigurationStore(
        environment="test_env",
        service="test_app",
        conf_name="test_conf_name",
        cache_seconds=600,
        config=config,
    )
    return conf_store


# this test checks that we get correct value of feature that exists in the schema.
# we also don't send an empty rules_context dict in this case
def test_toggles_rule_does_not_match(mocker, config):
    expected_value = "True"
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "name": "tenant id equals 345345435",
                        "rule_default_value": "False",
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(feature_name="my_feature", rules_context={}, value_if_missing=False)
    assert str(toggle) == expected_value


# this test checks that if you try to get a feature that doesn't exist in the schema,
# you get the default value of False that was sent to the get_feature_toggle API
def test_toggles_no_restrictions_feature_does_not_exist(mocker, config):
    expected_value = False
    mocked_app_config_schema = {"features": {"my_fake_feature": {"feature_default_value": "True"}}}

    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.get_feature_toggle(feature_name="my_feature", rules_context={}, value_if_missing=expected_value)
    assert toggle == expected_value


# check that feature match works when they are no rules and we send rules_context.
# default value is False but the feature has a True default_value.
def test_toggles_no_rules(mocker, config):
    expected_value = "True"
    mocked_app_config_schema = {"features": {"my_feature": {"feature_default_value": expected_value}}}
    conf_store = init_configuration_store(mocker, mocked_app_config_schema, config)
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature", rules_context={"tenant_id": "6", "username": "a"}, value_if_missing=False
    )
    assert str(toggle) == expected_value


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature
def test_toggles_restrictions_no_match(mocker, config):
    expected_value = "True"
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "name": "tenant id equals 345345435",
                        "rule_default_value": "False",
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "6", "username": "a"},  # rule will not match
        value_if_missing=False,
    )
    assert str(toggle) == expected_value


# check that a rule can match when it has multiple restrictions, see rule name for further explanation
def test_toggles_restrictions_rule_match_equal_multiple_restrictions(mocker, config):
    expected_value = "False"
    tenant_id_val = "6"
    username_val = "a"
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": "True",
                "rules": [
                    {
                        "name": "tenant id equals 6 and username is a",
                        "rule_default_value": expected_value,
                        "restrictions": [
                            {
                                "action": ACTION.EQUALS.value,  # this rule will match, it has multiple restrictions
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={
            "tenant_id": tenant_id_val,
            "username": username_val,
        },
        value_if_missing=True,
    )
    assert str(toggle) == expected_value


# check a case when rule doesn't match and it has multiple restrictions,
# different tenant id causes the rule to not match.
# default value of the feature in this case is True
def test_toggles_restrictions_no_rule_match_equal_multiple_restrictions(mocker, config):
    expected_val = "True"
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_val,
                "rules": [
                    {
                        "name": "tenant id equals 645654 and username is a",  # rule will not match
                        "rule_default_value": "False",
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature", rules_context={"tenant_id": "6", "username": "a"}, value_if_missing=False
    )
    assert str(toggle) == expected_val


# check rule match for multiple of action types
def test_toggles_restrictions_rule_match_multiple_actions_multiple_rules_multiple_restrictions(mocker, config):
    expected_value_first_check = "True"
    expected_value_second_check = "False"
    expected_value_third_check = "False"
    expected_value_fourth_case = False
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value_third_check,
                "rules": [
                    {
                        "name": "tenant id equals 6 and username startswith a",
                        "rule_default_value": expected_value_first_check,
                        "restrictions": [
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
                        "name": "tenant id equals 4446 and username startswith a and endswith z",
                        "rule_default_value": expected_value_second_check,
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "6", "username": "abcd"},
        value_if_missing=False,
    )
    assert str(toggle) == expected_value_first_check
    # match second rule
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "4446", "username": "az"},
        value_if_missing=False,
    )
    assert str(toggle) == expected_value_second_check
    # match no rule
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "11114446", "username": "ab"},
        value_if_missing=False,
    )
    assert str(toggle) == expected_value_third_check
    # feature doesn't exist
    toggle = conf_store.get_feature_toggle(
        feature_name="my_fake_feature",
        rules_context={"tenant_id": "11114446", "username": "ab"},
        value_if_missing=expected_value_fourth_case,
    )
    assert toggle == expected_value_fourth_case


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature
def test_toggles_match_rule_with_contains_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "name": "tenant id equals 345345435",
                        "rule_default_value": True,
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "6", "username": "a"},  # rule will match
        value_if_missing=False,
    )
    assert toggle == expected_value


def test_toggles_no_match_rule_with_contains_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "features": {
            "my_feature": {
                "feature_default_value": expected_value,
                "rules": [
                    {
                        "name": "tenant id equals 345345435",
                        "rule_default_value": True,
                        "restrictions": [
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
    toggle = conf_store.get_feature_toggle(
        feature_name="my_feature",
        rules_context={"tenant_id": "6", "username": "a"},  # rule will not match
        value_if_missing=False,
    )
    assert toggle == expected_value

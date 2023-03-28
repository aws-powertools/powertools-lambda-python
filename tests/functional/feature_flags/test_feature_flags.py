from typing import Dict, List, Optional

import pytest
from botocore.config import Config

from aws_lambda_powertools.utilities.feature_flags import (
    ConfigurationStoreError,
    schema,
)
from aws_lambda_powertools.utilities.feature_flags.appconfig import AppConfigStore
from aws_lambda_powertools.utilities.feature_flags.exceptions import StoreClientError
from aws_lambda_powertools.utilities.feature_flags.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.feature_flags.schema import (
    CONDITION_ACTION,
    CONDITION_KEY,
    CONDITION_VALUE,
    CONDITIONS_KEY,
    FEATURE_DEFAULT_VAL_KEY,
    FEATURE_DEFAULT_VAL_TYPE_KEY,
    RULE_MATCH_VALUE,
    RULES_KEY,
    RuleAction,
)
from aws_lambda_powertools.utilities.parameters import GetParameterError


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


# this test checks that we get correct value of feature that exists in the schema.
# we also don't send an empty context dict in this case
def test_flags_rule_does_not_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": False,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ],
                }
            },
        }
    }

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={}, default=False)
    assert toggle == expected_value


# this test checks that if you try to get a feature that doesn't exist in the schema,
# you get the default value of False that was sent to the evaluate API
def test_flags_no_conditions_feature_does_not_exist(mocker, config):
    expected_value = False
    mocked_app_config_schema = {"my_fake_feature": {"default": True}}

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={}, default=expected_value)
    assert toggle == expected_value


# check that feature match works when they are no rules and we send context.
# default value is False but the feature has a True default_value.
def test_flags_no_rules(mocker, config):
    expected_value = True
    mocked_app_config_schema = {"my_feature": {"default": expected_value}}
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature
def test_flags_conditions_no_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id equals 345345435": {
                    "when_match": False,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


# check that a rule can match when it has multiple conditions, see rule name for further explanation
def test_flags_conditions_rule_not_match_multiple_conditions_match_only_one_condition(mocker, config):
    expected_value = False
    tenant_id_val = "6"
    username_val = "a"
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id equals 6 and username is a": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,  # this condition matches
                            "key": "tenant_id",
                            "value": tenant_id_val,
                        },
                        {
                            "action": RuleAction.EQUALS.value,  # this condition does not
                            "key": "username",
                            "value": "bbb",
                        },
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={
            "tenant_id": tenant_id_val,
            "username": username_val,
        },
        default=True,
    )
    assert toggle == expected_value


def test_flags_conditions_rule_match_equal_multiple_conditions(mocker, config):
    expected_value = False
    tenant_id_val = "6"
    username_val = "a"
    mocked_app_config_schema = {
        "my_feature": {
            "default": True,
            "rules": {
                "tenant id equals 6 and username is a": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,  # this rule will match, it has multiple conditions
                            "key": "tenant_id",
                            "value": tenant_id_val,
                        },
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "username",
                            "value": username_val,
                        },
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
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
def test_flags_conditions_no_rule_match_equal_multiple_conditions(mocker, config):
    expected_val = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_val,
            "rules": {
                # rule will not match
                "tenant id equals 645654 and username is a": {
                    "when_match": False,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "645654",
                        },
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "username",
                            "value": "a",
                        },
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_val


# check rule match for multiple of action types
def test_flags_conditions_rule_match_multiple_actions_multiple_rules_multiple_conditions(mocker, config):
    expected_value_first_check = True
    expected_value_second_check = True
    expected_value_third_check = False
    expected_value_fourth_check = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value_third_check,
            "rules": {
                "tenant id equals 6 and username startswith a": {
                    "when_match": expected_value_first_check,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "6",
                        },
                        {
                            "action": RuleAction.STARTSWITH.value,
                            "key": "username",
                            "value": "a",
                        },
                    ],
                },
                "tenant id equals 4446 and username startswith a and endswith z": {
                    "when_match": expected_value_second_check,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant_id",
                            "value": "4446",
                        },
                        {
                            "action": RuleAction.STARTSWITH.value,
                            "key": "username",
                            "value": "a",
                        },
                        {
                            "action": RuleAction.ENDSWITH.value,
                            "key": "username",
                            "value": "z",
                        },
                    ],
                },
            },
        }
    }

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    # match first rule
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "abcd"}, default=False)
    assert toggle == expected_value_first_check
    # match second rule
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "4446", "username": "az"}, default=False)
    assert toggle == expected_value_second_check
    # match no rule
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "11114446", "username": "ab"}, default=False
    )
    assert toggle == expected_value_third_check
    # feature doesn't exist
    toggle = feature_flags.evaluate(
        name="my_fake_feature",
        context={"tenant_id": "11114446", "username": "ab"},
        default=expected_value_fourth_check,
    )
    assert toggle == expected_value_fourth_check


# check a case where the feature exists but the rule doesn't match so we revert to the default value of the feature


# Check IN/NOT_IN/KEY_IN_VALUE/KEY_NOT_IN_VALUE/VALUE_IN_KEY/VALUE_NOT_IN_KEY conditions
def test_flags_match_rule_with_in_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is contained in [6, 2]": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.IN.value,
                            "key": "tenant_id",
                            "value": ["6", "2"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_no_match_rule_with_in_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.IN.value,
                            "key": "tenant_id",
                            "value": ["8", "2"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_match_rule_with_not_in_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.NOT_IN.value,
                            "key": "tenant_id",
                            "value": ["10", "4"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_no_match_rule_with_not_in_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.NOT_IN.value,
                            "key": "tenant_id",
                            "value": ["6", "4"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_match_rule_with_key_in_value_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is contained in [6, 2]": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_IN_VALUE.value,
                            "key": "tenant_id",
                            "value": ["6", "2"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_no_match_rule_with_key_in_value_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_IN_VALUE.value,
                            "key": "tenant_id",
                            "value": ["8", "2"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_match_rule_with_key_not_in_value_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_NOT_IN_VALUE.value,
                            "key": "tenant_id",
                            "value": ["10", "4"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_no_match_rule_with_key_not_in_value_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_NOT_IN_VALUE.value,
                            "key": "tenant_id",
                            "value": ["6", "4"],
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "6", "username": "a"}, default=False)
    assert toggle == expected_value


def test_flags_match_rule_with_value_in_key_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "user is in the SYSADMIN group": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.VALUE_IN_KEY.value,
                            "key": "groups",
                            "value": "SYSADMIN",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "6", "username": "a", "groups": ["SYSADMIN", "IT"]}, default=False
    )
    assert toggle == expected_value


def test_flags_no_match_rule_with_value_in_key_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id is contained in [8, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.VALUE_IN_KEY.value,
                            "key": "groups",
                            "value": "GUEST",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "6", "username": "a", "groups": ["SYSADMIN", "IT"]}, default=False
    )
    assert toggle == expected_value


def test_flags_match_rule_with_value_not_in_key_action(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "user is in the GUEST group": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.VALUE_NOT_IN_KEY.value,
                            "key": "groups",
                            "value": "GUEST",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "6", "username": "a", "groups": ["SYSADMIN", "IT"]}, default=False
    )
    assert toggle == expected_value


def test_flags_no_match_rule_with_value_not_in_key_action(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "user is in the SYSADMIN group": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.VALUE_NOT_IN_KEY.value,
                            "key": "groups",
                            "value": "SYSADMIN",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "6", "username": "a", "groups": ["SYSADMIN", "IT"]}, default=False
    )
    assert toggle == expected_value


# Check multiple features
def test_multiple_features_enabled(mocker, config):
    expected_value = ["my_feature", "my_feature2"]
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is contained in [6, 2]": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.IN.value,
                            "key": "tenant_id",
                            "value": ["6", "2"],
                        }
                    ],
                }
            },
        },
        "my_feature2": {
            "default": True,
        },
        "my_feature3": {
            "default": False,
        },
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    enabled_list: List[str] = feature_flags.get_enabled_features(context={"tenant_id": "6", "username": "a"})
    assert enabled_list == expected_value


def test_get_feature_toggle_handles_error(mocker, config):
    # GIVEN a schema fetch that raises a ConfigurationStoreError
    schema_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())
    feature_flags = FeatureFlags(schema_fetcher)

    # WHEN calling evaluate
    toggle = feature_flags.evaluate(name="Foo", default=False)

    # THEN handle the error and return the default
    assert toggle is False


def test_get_all_enabled_feature_flags_handles_error(mocker, config):
    # GIVEN a schema fetch that raises a ConfigurationStoreError
    schema_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())
    feature_flags = FeatureFlags(schema_fetcher)

    # WHEN calling get_enabled_features
    flags = feature_flags.get_enabled_features(context=None)

    # THEN handle the error and return an empty list
    assert flags == []


def test_app_config_get_parameter_err(mocker, config):
    # GIVEN an appconfig with a missing config
    app_conf_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError())

    # WHEN calling get_configuration
    with pytest.raises(ConfigurationStoreError) as err:
        app_conf_fetcher.get_configuration()

    # THEN raise ConfigurationStoreError error
    assert "AWS AppConfig configuration" in str(err.value)


def test_match_by_action_no_matching_action(mocker, config):
    # GIVEN an unsupported action
    feature_flags = init_feature_flags(mocker, {}, config)
    # WHEN calling _match_by_action
    result = feature_flags._match_by_action("Foo", None, "foo")
    # THEN default to False
    assert result is False


def test_match_by_action_attribute_error(mocker, config):
    # GIVEN a startswith action and 2 integer
    feature_flags = init_feature_flags(mocker, {}, config)
    # WHEN calling _match_by_action
    result = feature_flags._match_by_action(RuleAction.STARTSWITH.value, 1, 100)
    # THEN swallow the AttributeError and return False
    assert result is False


def test_is_rule_matched_no_matches(mocker, config):
    # GIVEN an empty list of conditions
    rule = {schema.CONDITIONS_KEY: []}
    rules_context = {}
    feature_flags = init_feature_flags(mocker, {}, config)

    # WHEN calling _evaluate_conditions
    result = feature_flags._evaluate_conditions(
        rule_name="dummy", feature_name="dummy", rule=rule, context=rules_context
    )

    # THEN return False
    assert result is False


def test_features_jmespath_envelope(mocker, config):
    expected_value = True
    mocked_app_config_schema = {"features": {"my_feature": {"default": expected_value}}}
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config, envelope="features")
    toggle = feature_flags.evaluate(name="my_feature", context={}, default=False)
    assert toggle == expected_value


# test_match_rule_with_equals_action
def test_match_condition_with_dict_value(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id is 6 and username is lessa": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.EQUALS.value,
                            "key": "tenant",
                            "value": {"tenant_id": "6", "username": "lessa"},
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    ctx = {"tenant": {"tenant_id": "6", "username": "lessa"}}
    toggle = feature_flags.evaluate(name="my_feature", context=ctx, default=False)
    assert toggle == expected_value


def test_get_feature_toggle_propagates_access_denied_error(mocker, config):
    # GIVEN a schema fetch that raises a StoreClientError
    # due to client invalid permissions to fetch from the store
    err = "An error occurred (AccessDeniedException) when calling the GetConfiguration operation"
    schema_fetcher = init_fetcher_side_effect(mocker, config, GetParameterError(err))
    feature_flags = FeatureFlags(schema_fetcher)

    # WHEN calling evaluate
    # THEN raise StoreClientError error
    with pytest.raises(StoreClientError, match="AccessDeniedException") as err:
        feature_flags.evaluate(name="Foo", default=False)


def test_get_configuration_with_envelope_and_raw(mocker, config):
    expected_value = True
    mocked_app_config_schema = {"log_level": "INFO", "features": {"my_feature": {"default": expected_value}}}
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config, envelope="features")

    features_config = feature_flags.get_configuration()
    config = feature_flags.store.get_raw_configuration

    assert "log_level" in config
    assert "log_level" not in features_config


##
## Inequality test cases
##


# Test not equals
def test_flags_not_equal_no_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "tenant id not equals 345345435": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.NOT_EQUALS.value,
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature", context={"tenant_id": "345345435", "username": "a"}, default=False
    )
    assert toggle == expected_value


def test_flags_not_equal_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "tenant id not equals 345345435": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.NOT_EQUALS.value,
                            "key": "tenant_id",
                            "value": "345345435",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "", "username": "a"}, default=False)
    assert toggle == expected_value


# Test less than
def test_flags_less_than_no_match_1(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date less than 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.12.25"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_less_than_no_match_2(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date less than 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.10.31"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_less_than_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date less than 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.04.01"},
        default=False,
    )
    assert toggle == expected_value


# Test less than or equal to
def test_flags_less_than_or_equal_no_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date less than or equal 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.12.25"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_less_than_or_equal_match_1(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date less than or equal 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.04.01"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_less_than_or_equal_match_2(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date less than or equal 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_LESS_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.10.31"},
        default=False,
    )
    assert toggle == expected_value


# Test greater than
def test_flags_greater_than_no_match_1(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date greater than 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.04.01"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_greater_than_no_match_2(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date greater than 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.10.31"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_greater_than_match(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date greater than 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.12.25"},
        default=False,
    )
    assert toggle == expected_value


# Test greater than or equal to
def test_flags_greater_than_or_equal_no_match(mocker, config):
    expected_value = False
    mocked_app_config_schema = {
        "my_feature": {
            "default": expected_value,
            "rules": {
                "Date greater than or equal 2021.10.31": {
                    "when_match": True,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.04.01"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_greater_than_or_equal_match_1(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date greater than or equal 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.12.25"},
        default=False,
    )
    assert toggle == expected_value


def test_flags_greater_than_or_equal_match_2(mocker, config):
    expected_value = True
    mocked_app_config_schema = {
        "my_feature": {
            "default": False,
            "rules": {
                "Date greater than or equal 2021.10.31": {
                    "when_match": expected_value,
                    "conditions": [
                        {
                            "action": RuleAction.KEY_GREATER_THAN_OR_EQUAL_VALUE.value,
                            "key": "current_date",
                            "value": "2021.10.31",
                        }
                    ],
                }
            },
        }
    }
    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    toggle = feature_flags.evaluate(
        name="my_feature",
        context={"tenant_id": "345345435", "username": "a", "current_date": "2021.10.31"},
        default=False,
    )
    assert toggle == expected_value


def test_non_boolean_feature_match(mocker, config):
    expected_value = ["value1"]
    # GIVEN
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: [],
            FEATURE_DEFAULT_VAL_TYPE_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: expected_value,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: "tenant_id",
                            CONDITION_VALUE: "345345435",
                        }
                    ],
                }
            },
        }
    }

    # WHEN
    features = init_feature_flags(mocker, mocked_app_config_schema, config)
    feature_value = features.evaluate(name="my_feature", context={"tenant_id": "345345435"}, default=[])
    # THEN
    assert feature_value == expected_value


def test_non_boolean_feature_with_no_rules(mocker, config):
    expected_value = ["value1"]
    # GIVEN
    mocked_app_config_schema = {
        "my_feature": {FEATURE_DEFAULT_VAL_KEY: expected_value, FEATURE_DEFAULT_VAL_TYPE_KEY: False}
    }
    # WHEN
    features = init_feature_flags(mocker, mocked_app_config_schema, config)
    feature_value = features.evaluate(name="my_feature", context={"tenant_id": "345345435"}, default=[])
    # THEN
    assert feature_value == expected_value


def test_non_boolean_feature_with_no_rule_match(mocker, config):
    expected_value = []
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: expected_value,
            FEATURE_DEFAULT_VAL_TYPE_KEY: False,
            RULES_KEY: {
                "tenant id equals 345345435": {
                    RULE_MATCH_VALUE: ["value1"],
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: "tenant_id",
                            CONDITION_VALUE: "345345435",
                        }
                    ],
                }
            },
        }
    }

    features = init_feature_flags(mocker, mocked_app_config_schema, config)
    feature_value = features.evaluate(name="my_feature", context={}, default=[])
    assert feature_value == expected_value


def test_get_all_enabled_features_boolean_and_non_boolean(mocker, config):
    expected_value = ["my_feature", "my_feature2", "my_non_boolean_feature"]
    mocked_app_config_schema = {
        "my_feature": {
            FEATURE_DEFAULT_VAL_KEY: False,
            RULES_KEY: {
                "tenant id is contained in [6, 2]": {
                    RULE_MATCH_VALUE: True,
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.IN.value,
                            CONDITION_KEY: "tenant_id",
                            CONDITION_VALUE: ["6", "2"],
                        }
                    ],
                }
            },
        },
        "my_feature2": {
            FEATURE_DEFAULT_VAL_KEY: True,
        },
        "my_feature3": {
            FEATURE_DEFAULT_VAL_KEY: False,
        },
        "my_non_boolean_feature": {
            FEATURE_DEFAULT_VAL_KEY: {},
            FEATURE_DEFAULT_VAL_TYPE_KEY: False,
            RULES_KEY: {
                "username equals 'a'": {
                    RULE_MATCH_VALUE: {"group": "admin"},
                    CONDITIONS_KEY: [
                        {
                            CONDITION_ACTION: RuleAction.EQUALS.value,
                            CONDITION_KEY: "username",
                            CONDITION_VALUE: "a",
                        }
                    ],
                },
            },
        },
    }

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    enabled_list: List[str] = feature_flags.get_enabled_features(context={"tenant_id": "6", "username": "a"})
    assert enabled_list == expected_value


def test_get_all_enabled_features_non_boolean_truthy_defaults(mocker, config):
    expected_value = ["my_truthy_feature"]
    mocked_app_config_schema = {
        "my_truthy_feature": {FEATURE_DEFAULT_VAL_KEY: {"a": "b"}, FEATURE_DEFAULT_VAL_TYPE_KEY: False},
        "my_falsy_feature": {FEATURE_DEFAULT_VAL_KEY: {}, FEATURE_DEFAULT_VAL_TYPE_KEY: False},
    }

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, config)
    enabled_list: List[str] = feature_flags.get_enabled_features(context={"tenant_id": "6", "username": "a"})
    assert enabled_list == expected_value

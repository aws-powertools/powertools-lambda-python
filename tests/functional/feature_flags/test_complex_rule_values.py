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
    FEATURE_DEFAULT_VAL_TYPE_KEY,
    RULE_MATCH_VALUE,
    RULES_KEY,
    RuleAction,
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


# default return value is an empty list, when rule matches return a non empty list
def test_feature_rule_match(mocker, config):
    expected_value = ["value1"]
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

    features = init_feature_flags(mocker, mocked_app_config_schema, config)
    feature_value = features.evaluate(name="my_feature", context={"tenant_id": "345345435"}, default=[])
    assert feature_value == expected_value


def test_feature_no_rule_match(mocker, config):
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
